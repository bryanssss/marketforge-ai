from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import PROJECT_ROOT
from app.core.schemas import ExperimentPayload, ModelRecordPayload, ProjectPayload

_DB_PATH = PROJECT_ROOT / "storage" / "marketforge.db"
_LOCK = threading.RLock()


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _connect() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(_DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    return connection




@contextmanager
def _connection():
    connection = _connect()
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialise_storage() -> None:
    with _LOCK, _connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                settings_json TEXT NOT NULL,
                dataset_fingerprints_json TEXT NOT NULL,
                language TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NULL REFERENCES projects(id) ON DELETE SET NULL,
                name TEXT NOT NULL,
                kind TEXT NOT NULL,
                dataset_fingerprint TEXT NOT NULL,
                settings_json TEXT NOT NULL,
                metrics_json TEXT NOT NULL,
                result_json TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                result_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS model_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                family TEXT NOT NULL,
                version TEXT NOT NULL,
                source TEXT NOT NULL,
                revision TEXT NOT NULL,
                checksum TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                active INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(name, version, revision)
            );
            """
        )
        count = connection.execute("SELECT COUNT(*) AS n FROM model_registry").fetchone()["n"]
        if count == 0:
            builtins = [
                ("Naive persistence", "baseline", "1", "built-in", "v0.5", ""),
                ("Robust drift", "baseline", "1", "built-in", "v0.5", ""),
                ("Moving-block bootstrap", "baseline", "1", "built-in", "v0.5", ""),
                ("Exponential smoothing", "baseline", "1", "built-in", "v0.5", ""),
                ("Momentum", "baseline", "1", "built-in", "v0.5", ""),
                ("Mean reversion", "baseline", "1", "built-in", "v0.5", ""),
                ("Regime ensemble", "baseline", "1", "built-in", "v0.5", ""),
            ]
            now = _now()
            connection.executemany(
                "INSERT INTO model_registry(name,family,version,source,revision,checksum,metadata_json,active,created_at) VALUES(?,?,?,?,?,?,?,1,?)",
                [(name, family, version, source, revision, checksum, "{}", now) for name, family, version, source, revision, checksum in builtins],
            )


def _decode_row(row: sqlite3.Row, fields: tuple[str, ...]) -> dict[str, Any]:
    output = dict(row)
    for field in fields:
        key = f"{field}_json"
        if key in output:
            output[field] = json.loads(output.pop(key))
    if "active" in output:
        output["active"] = bool(output["active"])
    return output


def list_projects() -> list[dict[str, Any]]:
    initialise_storage()
    with _connection() as connection:
        rows = connection.execute("SELECT * FROM projects ORDER BY updated_at DESC, id DESC").fetchall()
    return [_decode_row(row, ("settings", "dataset_fingerprints")) for row in rows]


def create_project(payload: ProjectPayload) -> dict[str, Any]:
    initialise_storage()
    now = _now()
    with _LOCK, _connection() as connection:
        cursor = connection.execute(
            "INSERT INTO projects(name,description,settings_json,dataset_fingerprints_json,language,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
            (payload.name, payload.description, _json(payload.settings), _json(payload.dataset_fingerprints), payload.language, now, now),
        )
        project_id = int(cursor.lastrowid)
        row = connection.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    return _decode_row(row, ("settings", "dataset_fingerprints"))


def delete_project(project_id: int) -> bool:
    initialise_storage()
    with _LOCK, _connection() as connection:
        cursor = connection.execute("DELETE FROM projects WHERE id=?", (project_id,))
    return cursor.rowcount > 0


def list_experiments(project_id: int | None = None, limit: int = 100) -> list[dict[str, Any]]:
    initialise_storage()
    with _connection() as connection:
        if project_id is None:
            rows = connection.execute("SELECT * FROM experiments ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM experiments WHERE project_id=? ORDER BY id DESC LIMIT ?", (project_id, limit)
            ).fetchall()
    return [_decode_row(row, ("settings", "metrics", "result", "tags")) for row in rows]


def create_experiment(payload: ExperimentPayload) -> dict[str, Any]:
    initialise_storage()
    result_json = _json(payload.result)
    result_hash = hashlib.sha256(result_json.encode("utf-8")).hexdigest()
    now = _now()
    with _LOCK, _connection() as connection:
        cursor = connection.execute(
            """INSERT INTO experiments(project_id,name,kind,dataset_fingerprint,settings_json,metrics_json,result_json,tags_json,result_hash,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (
                payload.project_id,
                payload.name,
                payload.kind,
                payload.dataset_fingerprint,
                _json(payload.settings),
                _json(payload.metrics),
                result_json,
                _json(payload.tags),
                result_hash,
                now,
            ),
        )
        row = connection.execute("SELECT * FROM experiments WHERE id=?", (int(cursor.lastrowid),)).fetchone()
    return _decode_row(row, ("settings", "metrics", "result", "tags"))


def list_models() -> list[dict[str, Any]]:
    initialise_storage()
    with _connection() as connection:
        rows = connection.execute("SELECT * FROM model_registry ORDER BY active DESC, family, name, version").fetchall()
    return [_decode_row(row, ("metadata",)) for row in rows]


def register_model(payload: ModelRecordPayload) -> dict[str, Any]:
    initialise_storage()
    with _LOCK, _connection() as connection:
        cursor = connection.execute(
            """INSERT INTO model_registry(name,family,version,source,revision,checksum,metadata_json,active,created_at)
            VALUES(?,?,?,?,?,?,?,?,?)""",
            (
                payload.name,
                payload.family,
                payload.version,
                payload.source,
                payload.revision,
                payload.checksum,
                _json(payload.metadata),
                int(payload.active),
                _now(),
            ),
        )
        row = connection.execute("SELECT * FROM model_registry WHERE id=?", (int(cursor.lastrowid),)).fetchone()
    return _decode_row(row, ("metadata",))
