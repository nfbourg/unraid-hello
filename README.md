# unraid-hello

Phase-1 fixture for the `unraid_deploy` pipeline: a minimal, no-dependency
Python HTTP server used to prove the **build → deploy → update** loop on an
Unraid box end-to-end, before any real (LLM) app is shipped.

This repo is **public on purpose** — it exists only so the Unraid Docker
daemon can clone it over HTTPS and build the image with no credentials
(e.g. via Compose Manager Plus `build:` from a git context). It contains no
secrets and nothing tailnet-specific.

## What it does

Serves one page (and a `/healthz` endpoint) showing:

- **hostname** — the container's hostname
- **version** — `APP_VERSION` build-arg (the git short-sha of the deploy)
- **built** — `BUILD_TIME` build-arg

so a deploy or an update is **visually verifiable in a browser**: change the
version marker, rebuild, and confirm the new value is what's now serving.

`/healthz` returns `ok <APP_VERSION>` (200) — the version is in the body so a
post-update poll can confirm the *new* image is the one now running, not just
that *something* is healthy.

## Build

```sh
docker build \
  --provenance=false \
  --build-arg APP_VERSION="$(git rev-parse --short HEAD)" \
  --build-arg BUILD_TIME="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  -t unraid-hello .
docker run --rm --read-only --cap-drop=ALL -p 8210:8000 unraid-hello
# then: curl -s localhost:8210/healthz   ->   ok <sha>
```

Hardening-friendly: runs as non-root uid 1000, works under `--read-only`
and `--cap-drop=ALL`, no writable paths required.

## Compose (Unraid / Compose Manager Plus)

Use this repo as the build context. Bind the published port to the tailnet
IP only — never `0.0.0.0` — so the app is reachable on the tailnet and
nowhere else:

```yaml
services:
  hello:
    build:
      context: "https://github.com/nfbourg/unraid-hello.git"
      args:
        APP_VERSION: "v1"
        BUILD_TIME: "manual"
    container_name: hello
    ports:
      - "100.70.51.30:8210:8000"   # tailnet IP only
    read_only: true
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    restart: unless-stopped
```
