from __future__ import annotations

import threading
import time
import urllib.request

import uvicorn

from app.core.config import SETTINGS


def _serve() -> None:
    uvicorn.run("app.main:app", host="127.0.0.1", port=SETTINGS.port, log_level="warning")


def _wait_for_server(url: str, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1):  # noqa: S310 - local loopback URL
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("MarketForge desktop server did not start in time.")


def main() -> None:
    try:
        import webview
    except ImportError as exc:
        raise SystemExit("Install desktop dependencies with: pip install -r requirements-desktop.txt") from exc

    url = f"http://127.0.0.1:{SETTINGS.port}"
    thread = threading.Thread(target=_serve, daemon=True, name="marketforge-server")
    thread.start()
    _wait_for_server(f"{url}/api/health")
    webview.create_window("MarketForge AI", url, width=1440, height=920, min_size=(960, 640))
    webview.start(private_mode=True)


if __name__ == "__main__":
    main()
