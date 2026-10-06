from __future__ import annotations

import io
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Union

import pymupdf as fitz
from PIL import Image

from .errors import PDFThumbError

PDFSource = Union[str, os.PathLike, bytes]


def parse_pages(spec: str, page_count: int) -> list[int]:
    """Parse '1,3-5' or 'all' into 0-based page indices (out-of-range pages dropped)."""
    spec = spec.strip().lower()
    if spec == "all":
        return list(range(page_count))
    pages: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            if "-" in part:
                a, b = part.split("-", 1)
                start = int(a) if a else 1
                end = int(b) if b else page_count
                pages.extend(range(start, end + 1))
            else:
                pages.append(int(part))
        except ValueError:
            raise ValueError(f"invalid page spec: {spec!r}") from None
    out: list[int] = []
    for n in pages:
        if n < 1:
            raise ValueError(f"invalid page number: {n}")
        if n <= page_count and (n - 1) not in out:
            out.append(n - 1)
    return out


@dataclass
class Options:
    width: int = 256
    height: int | None = None
    quality: int = 80
    pages: str = "1"
    overwrite: bool = False
    crop_top: float | None = None  # keep top region with height = width * crop_top

    def validate(self) -> None:
        if self.width < 1 or (self.height is not None and self.height < 1):
            raise ValueError("width/height must be positive")
        if not 0 <= self.quality <= 100:
            raise ValueError("quality must be 0-100")
        if self.crop_top is not None:
            if self.crop_top <= 0:
                raise ValueError("crop_top ratio must be positive")
            if self.height is not None:
                raise ValueError("crop_top cannot be combined with height")


def _open(pdf: PDFSource) -> fitz.Document:
    try:
        doc = fitz.open(stream=pdf, filetype="pdf") if isinstance(pdf, (bytes, bytearray)) else fitz.open(pdf)
    except Exception as e:  # noqa: BLE001
        raise PDFThumbError(f"cannot open PDF: {e}") from e
    if doc.needs_pass:
        doc.close()
        raise PDFThumbError("PDF is password-protected")
    return doc


def _render_page(page: fitz.Page, opts: Options) -> Image.Image:
    rect = page.rect
    if opts.crop_top:
        clip_h = min(rect.height, rect.width * opts.crop_top)
        rect = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y0 + clip_h)
        tw = opts.width
        th = max(1, round(clip_h * tw / rect.width))
    else:
        scale = opts.width / rect.width
        if opts.height:
            scale = min(scale, opts.height / rect.height)
        tw, th = max(1, round(rect.width * scale)), max(1, round(rect.height * scale))
    # Render at 2x target then downsample for crisp output.
    zoom = 2 * tw / rect.width
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=rect, alpha=False)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    return img.resize((tw, th), Image.LANCZOS)


def render_thumbnail(
    pdf: PDFSource,
    page: int = 1,
    *,
    width: int = 256,
    height: int | None = None,
    crop_top: float | None = None,
) -> Image.Image:
    """Render one page (1-based) of a PDF path or PDF bytes to a PIL image."""
    opts = Options(width=width, height=height, crop_top=crop_top)
    opts.validate()
    with _open(pdf) as doc:
        if not 1 <= page <= doc.page_count:
            raise PDFThumbError(f"page {page} out of range (document has {doc.page_count})")
        return _render_page(doc[page - 1], opts)


def thumbnail_bytes(
    pdf: PDFSource,
    page: int = 1,
    *,
    width: int = 256,
    height: int | None = None,
    crop_top: float | None = None,
    quality: int = 80,
) -> bytes:
    """Render one page (1-based) of a PDF to WebP-encoded bytes."""
    if not 0 <= quality <= 100:
        raise ValueError("quality must be 0-100")
    img = render_thumbnail(pdf, page, width=width, height=height, crop_top=crop_top)
    buf = io.BytesIO()
    img.save(buf, "WEBP", quality=quality, method=6)
    return buf.getvalue()


def render_pdf(pdf: str | os.PathLike, out_dir: str | os.PathLike, opts: Options) -> list[dict]:
    """Render selected pages of a PDF file to WebP files in out_dir. Returns result dicts."""
    pdf, out_dir = Path(pdf), Path(out_dir)
    results: list[dict] = []
    with _open(pdf) as doc:
        indices = parse_pages(opts.pages, doc.page_count)
        if not indices:
            raise PDFThumbError(f"no pages match '{opts.pages}' (document has {doc.page_count})")
        out_dir.mkdir(parents=True, exist_ok=True)
        single = len(indices) == 1 and opts.pages.strip() == "1"
        for i in indices:
            name = f"{pdf.stem}.webp" if single else f"{pdf.stem}_p{i + 1}.webp"
            dest = out_dir / name
            if dest.exists() and not opts.overwrite:
                results.append({"input": str(pdf), "page": i + 1, "output": str(dest), "status": "skipped"})
                continue
            img = _render_page(doc[i], opts)
            img.save(dest, "WEBP", quality=opts.quality, method=6)
            results.append({"input": str(pdf), "page": i + 1, "output": str(dest), "status": "ok",
                            "width": img.width, "height": img.height})
    return results
