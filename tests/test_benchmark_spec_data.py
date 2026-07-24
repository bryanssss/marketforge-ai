from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pandas as pd

from app.benchmark.data import month_keys, parse_binance_zip, parse_checksum
from app.benchmark.spec import (
    load_spec,
    make_preregistration_lock,
    make_protocol_lock,
    sha256_json,
    write_json,
)


def test_frozen_spec_loads_and_hashes_stably() -> None:
    path = Path("benchmarks/frozen_v2/spec.json")
    first = load_spec(path)
    second = load_spec(path)
    assert first.benchmark_id == "marketforge-prospective-v2"
    assert first.hash == second.hash
    assert len(first.hash) == 64


def test_month_keys_use_exclusive_end() -> None:
    assert month_keys("2025-10-01T00:00:00Z", "2026-01-01T00:00:00Z") == ["2025-10", "2025-11", "2025-12"]


def test_checksum_parser_rejects_non_sha() -> None:
    assert parse_checksum("a" * 64 + "  file.zip") == "a" * 64
    try:
        parse_checksum("bad")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected invalid checksum to fail")


def test_binance_parser_supports_microseconds(tmp_path: Path) -> None:
    row = "1759276800000000,100,110,90,105,12,1759280399999999,1234,10,6,630,0\n"
    archive = tmp_path / "sample.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("sample.csv", row)
    frame = parse_binance_zip(archive)
    assert list(frame.columns) == ["timestamp", "open", "high", "low", "close", "volume", "amount"]
    assert str(frame["timestamp"].dt.tz) == "UTC"
    assert frame["amount"].iloc[0] == 1234


def test_protocol_lock_binds_all_three_locks(tmp_path: Path) -> None:
    raw = json.loads(Path("benchmarks/frozen_v2/spec.json").read_text())
    path = tmp_path / "spec.json"
    write_json(path, raw)
    spec = load_spec(path)
    model = {"models": {"x": {"revision": "abc"}}}
    data = {"status": "verified", "datasets": []}
    verification = {"all_verified": True}
    preregistration = make_preregistration_lock(
        spec, model, code_sha256="abc", git_commit="deadbeef", git_dirty=False
    )
    lock = make_protocol_lock(
        spec, model, data, "deadbeef", False, code_sha256="abc",
        model_verification=verification, environment_verification={"all_verified": True}, preregistration=preregistration
    )
    assert lock["status"] == "frozen"
    assert lock["model_lock_sha256"] == sha256_json(model)
    assert lock["protocol_sha256"]


def test_data_lock_detects_archive_tampering(tmp_path: Path) -> None:
    from app.benchmark.data import sha256_file, verify_data_lock

    raw = json.loads(Path("benchmarks/frozen_v2/spec.json").read_text())
    raw["data"]["symbols"] = ["TEST"]
    raw["data"]["context_start"] = "2026-07-01T00:00:00Z"
    raw["data"]["holdout_start"] = "2026-08-01T00:00:00Z"
    raw["data"]["holdout_end_exclusive"] = "2026-08-02T00:00:00Z"
    raw["data"]["data_available_not_before"] = "2026-08-03T00:00:00Z"
    spec_path = tmp_path / "spec.json"
    write_json(spec_path, raw)
    spec = load_spec(spec_path)
    archive = tmp_path / "archive.zip"
    checksum = tmp_path / "archive.zip.CHECKSUM"
    archive.write_bytes(b"provider bytes")
    digest = sha256_file(archive)
    checksum.write_text(digest + "  archive.zip\n", encoding="utf-8")
    data = tmp_path / "TEST-1h.csv"
    timestamps = pd.date_range("2026-07-01", "2026-08-02", inclusive="left", freq="h", tz="UTC")
    frame = pd.DataFrame({
        "timestamp": timestamps, "open": 1.0, "high": 1.0, "low": 1.0,
        "close": 1.0, "volume": 1.0, "amount": 1.0,
    })
    frame.to_csv(data, index=False)
    archive_aug = tmp_path / "archive-aug.zip"
    checksum_aug = tmp_path / "archive-aug.zip.CHECKSUM"
    archive_aug.write_bytes(b"provider bytes august")
    digest_aug = sha256_file(archive_aug)
    checksum_aug.write_text(digest_aug + "  archive-aug.zip\n", encoding="utf-8")
    lock = {
        "benchmark_id": spec.benchmark_id, "status": "verified",
        "provider_checksum_verified": True,
        "archives": [{
            "symbol": "TEST", "month": "2026-07", "archive_path": archive.name,
            "checksum_path": checksum.name, "provider_sha256": digest,
            "downloaded_sha256": digest, "checksum_file_sha256": sha256_file(checksum),
        }, {
            "symbol": "TEST", "month": "2026-08", "archive_path": archive_aug.name,
            "checksum_path": checksum_aug.name, "provider_sha256": digest_aug,
            "downloaded_sha256": digest_aug, "checksum_file_sha256": sha256_file(checksum_aug),
        }],
        "datasets": [{"symbol": "TEST", "path": data.name, "sha256": sha256_file(data)}],
    }
    assert verify_data_lock(tmp_path, lock, spec) == []
    archive.write_bytes(b"tampered")
    assert any("archive hash mismatch" in item for item in verify_data_lock(tmp_path, lock, spec))
