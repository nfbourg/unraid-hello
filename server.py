#!/usr/bin/env python3
"""Minimal no-dependency HTTP server for the Unraid deploy pipeline.

Serves a page showing the container hostname, image version (git sha), and
build timestamp so that deploys and updates are visually verifiable in a
browser over the tailnet. No LLM, no external deps -- this is Phase 1, the
fixture that proves the build -> registry -> Unraid deploy loop end to end.
"""
from __future__ import annotations

import html
import os
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

APP_VERSION = os.environ.get("APP_VERSION", "dev")
BUILD_TIME = os.environ.get("BUILD_TIME", "unknown")
PORT = int(os.environ.get("PORT", "8000"))

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>unraid-deploy hello</title>
<style>
  :root { color-scheme: light dark; }
  body { font: 16px/1.5 system-ui, sans-serif; margin: 0;
         display: grid; place-items: center; min-height: 100vh; }
  .card { padding: 2rem 2.5rem; border-radius: 12px;
          box-shadow: 0 1px 6px rgba(0,0,0,.25); max-width: 30rem; }
  h1 { margin: 0 0 1rem; font-size: 1.35rem; }
  dl { display: grid; grid-template-columns: auto 1fr; gap: .4rem 1rem; margin: 0; }
  dt { font-weight: 600; opacity: .65; }
  dd { margin: 0; font-family: ui-monospace, SFMono-Regular, monospace; }
</style>
</head>
<body>
  <div class="card">
    <h1>hello from the unraid-deploy pipeline</h1>
    <dl>
      <dt>hostname</dt><dd>__HOSTNAME__</dd>
      <dt>version</dt><dd>__VERSION__</dd>
      <dt>built</dt><dd>__BUILT__</dd>
    </dl>
  </div>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path.rstrip("/") == "/healthz":
            # Body carries the version marker so deploy.sh's post-`--update`
            # verify poll can confirm the NEW image is the one now serving
            # (a bare "ok" would pass health but not prove the version).
            self._respond(
                200, "text/plain; charset=utf-8", f"ok {APP_VERSION}\n".encode()
            )
            return
        body = (
            PAGE.replace("__HOSTNAME__", html.escape(socket.gethostname()))
            .replace("__VERSION__", html.escape(APP_VERSION))
            .replace("__BUILT__", html.escape(BUILD_TIME))
        ).encode()
        self._respond(200, "text/html; charset=utf-8", body)

    def _respond(self, code: int, ctype: str, body: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:  # one-line, unbuffered logs
        print(f"{self.address_string()} - {fmt % args}", flush=True)


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(
        f"hello serving on :{PORT} (version={APP_VERSION}, built={BUILD_TIME})",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
