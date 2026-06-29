#!/usr/bin/env python3
"""Static file server for web/ WITH HTTP Range support.

PMTiles fetches byte ranges out of web/tiles/mpas.pmtiles, which needs 206 Partial
Content responses. Python's stock http.server does not honour Range, so local
preview of the MPA tiles needs this. (GitHub Pages supports Range natively.)

Run:  python3 scripts/serve.py 8000
"""

from __future__ import annotations

import os
import re
import sys
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"


class RangeHandler(SimpleHTTPRequestHandler):
    def end_headers(self):  # noqa: N802 (stdlib casing)
        # Dev server: never let the browser cache, so regenerated data shows immediately.
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def send_head(self):  # noqa: N802 (stdlib casing)
        rng = self.headers.get("Range")
        if not rng:
            return super().send_head()
        path = self.translate_path(self.path)
        if not os.path.isfile(path):
            return super().send_head()
        size = os.path.getsize(path)
        m = re.match(r"bytes=(\d*)-(\d*)", rng)
        if not m:
            return super().send_head()
        start = int(m.group(1)) if m.group(1) else 0
        end = int(m.group(2)) if m.group(2) else size - 1
        end = min(end, size - 1)
        if start > end:
            self.send_error(416, "Requested Range Not Satisfiable")
            return None
        length = end - start + 1
        f = open(path, "rb")  # noqa: SIM115 (caller closes)
        f.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        self._range = (f, length)
        return f

    def copyfile(self, source, outputfile):
        rng = getattr(self, "_range", None)
        if rng is None:
            return super().copyfile(source, outputfile)
        f, length = rng
        remaining = length
        while remaining > 0:
            chunk = f.read(min(64 * 1024, remaining))
            if not chunk:
                break
            outputfile.write(chunk)
            remaining -= len(chunk)


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    handler = partial(RangeHandler, directory=str(WEB))
    print(f"serving {WEB} with Range support on http://localhost:{port}")
    HTTPServer(("0.0.0.0", port), handler).serve_forever()


if __name__ == "__main__":
    main()
