import uvicorn

from app.core.config import SETTINGS

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=SETTINGS.host,
        port=SETTINGS.port,
        reload=False,
        server_header=False,
    )
