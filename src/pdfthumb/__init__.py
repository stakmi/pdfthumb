"""Generate WebP thumbnails from PDF files."""

__version__ = "0.1.0"

from .api import ThumbnailResult, generate_thumbnails
from .collect import collect_pdfs
from .errors import PDFThumbError
from .render import parse_pages, render_thumbnail, thumbnail_bytes

__all__ = [
    "__version__",
    "PDFThumbError",
    "ThumbnailResult",
    "collect_pdfs",
    "generate_thumbnails",
    "parse_pages",
    "render_thumbnail",
    "thumbnail_bytes",
]
