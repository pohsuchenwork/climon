"""Run the climon online server: ``python -m climon.server``."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os

from climon.server.app import serve_forever


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    # PORT is injected by hosts like Render; CLIMON_PORT is our own; then a default.
    host = os.environ.get("CLIMON_HOST", "localhost")
    port = int(os.environ.get("PORT") or os.environ.get("CLIMON_PORT") or "8765")
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(serve_forever(host, port))


if __name__ == "__main__":
    main()
