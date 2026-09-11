from __future__ import annotations

import argparse


def cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    uvicorn.run(
        "astroimage.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0
