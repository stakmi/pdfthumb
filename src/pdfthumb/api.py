from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Optional, Union

from .collect import collect_pdfs
from .render import Options, render_pdf

PathLike = Union[str, os.PathLike]


@dataclass
class ThumbnailResult:
    input: str
    status: str  # "ok" | "skipped" | "error"
    page: Optional[int] = None
    output: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.status != "error"

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


def _work(pdf: str, out_dir: str, opts: Options) -> list[dict]:
    try:
        return render_pdf(pdf, out_dir, opts)
    except Exception as e:  # noqa: BLE001
        return [{"input": pdf, "status": "error", "error": str(e)}]


def generate_thumbnails(
    inputs: Union[PathLike, Iterable[PathLike]],
    output_dir: PathLike = "thumbnails",
    *,
    width: int = 256,
    height: Optional[int] = None,
    quality: int = 80,
    pages: str = "1",
    crop_top: Optional[float] = None,
    recursive: bool = False,
    overwrite: bool = False,
    jobs: int = 1,
) -> list[ThumbnailResult]:
    """Generate WebP thumbnails for PDF files and/or directories.

    Per-file failures are reported as results with status "error" rather than raised.
    Raises ValueError for invalid options.
    """
    if isinstance(inputs, (str, os.PathLike)):
        inputs = [inputs]
    opts = Options(width=width, height=height, quality=quality, pages=pages,
                   overwrite=overwrite, crop_top=crop_top)
    opts.validate()

    out_root = Path(output_dir)
    tasks = [(str(pdf), str(out_root / rel), opts) for pdf, rel in collect_pdfs([str(i) for i in inputs], recursive)]
    raw: list[dict] = []
    if jobs > 1 and len(tasks) > 1:
        with ProcessPoolExecutor(max_workers=min(jobs, len(tasks))) as ex:
            for f in as_completed([ex.submit(_work, *t) for t in tasks]):
                raw.extend(f.result())
    else:
        for t in tasks:
            raw.extend(_work(*t))
    return [ThumbnailResult(**r) for r in raw]
