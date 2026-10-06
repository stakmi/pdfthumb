from __future__ import annotations

import sys
from pathlib import Path


def collect_pdfs(inputs: list[str], recursive: bool = False) -> list[tuple[Path, Path]]:
    """Return (pdf_path, relative_dir) pairs. relative_dir mirrors structure under directory inputs."""
    results: list[tuple[Path, Path]] = []
    seen: set[Path] = set()

    def add(p: Path, rel: Path) -> None:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            results.append((p, rel))

    for raw in inputs:
        p = Path(raw).expanduser()
        if p.is_dir():
            pattern = "**/*" if recursive else "*"
            for f in sorted(p.glob(pattern)):
                if f.is_file() and f.suffix.lower() == ".pdf":
                    add(f, f.parent.relative_to(p))
        elif p.is_file():
            if p.suffix.lower() == ".pdf":
                add(p, Path("."))
            else:
                print(f"warning: skipping non-PDF file: {p}", file=sys.stderr)
        else:
            print(f"warning: not found: {p}", file=sys.stderr)
    return results
