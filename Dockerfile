# Phase-1 pipeline fixture: no dependencies, stdlib HTTP server only.
# Proves the build -> self-hosted-registry -> Unraid deploy loop.
FROM python:3.14-slim

# Build metadata, surfaced by the app so deploys/updates are visible in a browser.
ARG APP_VERSION=dev
ARG BUILD_TIME=unknown
ENV APP_VERSION=${APP_VERSION} \
    BUILD_TIME=${BUILD_TIME} \
    PORT=8000 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Non-root uid 1000 per the house baseline (matches host user; keeps any
# bind-mounted paths writable, and lets --read-only run cleanly).
RUN useradd -m -u 1000 app
COPY server.py /app/server.py
USER app
EXPOSE 8000

# Service -> CMD (a CLI tool would use ENTRYPOINT). No restart policy is set
# here; that lives on the Unraid side via the container template.
CMD ["python", "/app/server.py"]
