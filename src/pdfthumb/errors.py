class PDFThumbError(Exception):
    """Raised when a PDF cannot be thumbnailed (corrupt, encrypted, bad page, ...)."""
