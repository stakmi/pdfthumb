from __future__ import annotations

import argparse
import json
import os
import sys

from . import __version__
from .api import generate_thumbnails


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pdfthumb", description="Generate WebP thumbnails from PDF files.")
    p.add_argument("inputs", nargs="+", metavar="INPUT", help="PDF files and/or directories")
    p.add_argument("-o", "--output", default="thumbnails", help="output directory (default: ./thumbnails)")
    p.add_argument("-w", "--width", type=int, default=256, help="thumbnail width in px (default: 256)")
    p.add_argument("--height", type=int, default=None, help="max height in px (fit within width x height)")
    p.add_argument("-c", "--crop-top", type=float, nargs="?", const=1.0, default=None, metavar="RATIO",
                   help="keep only the top of the page, crop height = width x RATIO (default RATIO: 1.0, square)")
    p.add_argument("-q", "--quality", type=int, default=80, help="WebP quality 0-100 (default: 80)")
    p.add_argument("-p", "--pages", default="1", help='pages, e.g. "1", "1,3-5", "all" (default: 1)')
    p.add_argument("-r", "--recursive", action="store_true", help="recurse into directories")
    p.add_argument("--overwrite", action="store_true", help="overwrite existing thumbnails")
    p.add_argument("-j", "--jobs", type=int, default=os.cpu_count() or 1, help="parallel workers")
    p.add_argument("--json", action="store_true", help="print results as JSON")
    p.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        results = generate_thumbnails(
            args.inputs, args.output, width=args.width, height=args.height, quality=args.quality,
            pages=args.pages, crop_top=args.crop_top, recursive=args.recursive,
            overwrite=args.overwrite, jobs=args.jobs,
        )
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if not results:
        print("error: no PDF files found", file=sys.stderr)
        return 1

    failed = False
    for r in results:
        if not r.ok:
            failed = True
            print(f"error: {r.input}: {r.error}", file=sys.stderr)
        elif not args.json:
            print(f"{r.output}{' (skipped, exists)' if r.status == 'skipped' else ''}")
    if args.json:
        print(json.dumps([r.to_dict() for r in results], indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
