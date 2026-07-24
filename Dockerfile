FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    MARKETFORGE_HOST=0.0.0.0 \
    MARKETFORGE_PORT=7070 \
    MARKETFORGE_ENV=container \
    MARKETFORGE_DOCS=false

WORKDIR /app

RUN groupadd --system marketforge \
    && useradd --system --gid marketforge --home-dir /app --shell /usr/sbin/nologin marketforge

COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY --chown=marketforge:marketforge . .
USER marketforge

EXPOSE 7070

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import json,urllib.request; r=urllib.request.urlopen('http://127.0.0.1:7070/api/health', timeout=3); assert json.load(r)['status']=='ready'" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7070", "--no-server-header", "--proxy-headers", "--forwarded-allow-ips", "127.0.0.1"]
