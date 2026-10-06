# pdfthumb

Generate WebP thumbnails from PDFs. The input can be one file, several files, or directories.
You can use it as a **command-line tool** or as a **Python library**.

## Install

```bash
./install.sh          # creates .venv, installs deps, links ~/.local/bin/pdfthumb
./install.sh --dev    # also installs pytest
./uninstall.sh
```

You need Python 3.9 or later. Dependencies are PyMuPDF and Pillow, so no system packages are required.

## Usage

```bash
pdfthumb doc.pdf                       # -> thumbnails/doc.webp
pdfthumb a.pdf b.pdf -o out/           # multiple files
pdfthumb ./pdfs -r                     # directory, recursive (structure mirrored in output)
pdfthumb doc.pdf -p all -w 512         # every page -> doc_p1.webp, doc_p2.webp ...
pdfthumb doc.pdf -p 1,3-5 --height 300 # fit within 256x300
pdfthumb doc.pdf --crop-top           # top square only -> 256x256
pdfthumb doc.pdf -c 0.5                # top band, 256x128
pdfthumb ./pdfs --json                 # JSON results on stdout
```

| Option | Default | Description |
|---|---|---|
| `-o, --output DIR` | `./thumbnails` | Output directory |
| `-w, --width PX` | `256` | Thumbnail width (the aspect ratio is kept) |
| `--height PX` | – | Maximum height; the thumbnail is fitted within width × height |
| `-c, --crop-top [RATIO]` | off | Keep only the top of the page. Crop height = width × RATIO (`1.0` = square when the flag is given without a value). Can't be combined with `--height` |
| `-q, --quality N` | `80` | WebP quality (0–100) |
| `-p, --pages SPEC` | `1` | Pages to render, e.g. `1`, `1,3-5`, `all` |
| `-r, --recursive` | off | Recurse into directories |
| `--overwrite` | off | Overwrite existing thumbnails. Without it, existing files are skipped |
| `-j, --jobs N` | CPU count | Number of parallel workers |
| `--json` | off | Print results as JSON |

Output naming: `<name>.webp` with the default `-p 1`, otherwise `<name>_p<N>.webp`.
The exit code is `1` if any PDF failed, for example a corrupt or password-protected file.

## Library usage

Install it into your own environment:

```bash
pip install pdfthumb                        # from PyPI
pip install -e /path/to/pdf-thumbnail       # from a local checkout
```

### Batch: files or directories to WebP files

```python
from pdfthumb import generate_thumbnails

results = generate_thumbnails(
    ["a.pdf", "docs/"],      # a path, or a list of files and/or directories
    "thumbnails",            # output directory
    width=256,
    pages="1",               # "1", "1,3-5", "all"
    crop_top=1.0,            # optional: keep only the top square
    recursive=True,
    overwrite=False,
    jobs=4,                  # parallel processes (default 1)
)
for r in results:
    if r.ok:
        print(r.status, r.output, r.width, r.height)   # status: "ok" or "skipped"
    else:
        print("failed:", r.input, r.error)
```

`generate_thumbnails` raises `ValueError` for invalid options. A PDF that fails (for example a corrupt or encrypted file) does not raise. It comes back as a result with `status="error"`.
To get JSON-ready output, call `r.to_dict()`.

### Single page in memory (e.g. in a web service)

```python
from pdfthumb import render_thumbnail, thumbnail_bytes, PDFThumbError

# A PIL.Image, from a file path or raw PDF bytes
img = render_thumbnail("doc.pdf", page=1, width=300, crop_top=0.75)

# WebP-encoded bytes, ready to upload or return in an HTTP response
with open("doc.pdf", "rb") as f:
    try:
        webp = thumbnail_bytes(f.read(), page=1, width=256, quality=80)
    except PDFThumbError as e:
        print("cannot thumbnail:", e)
```

### API reference

| Function | Returns | Notes |
|---|---|---|
| `generate_thumbnails(inputs, output_dir="thumbnails", *, width, height, quality, pages, crop_top, recursive, overwrite, jobs)` | `list[ThumbnailResult]` | Writes the WebP files. Same behaviour as the CLI |
| `render_thumbnail(pdf, page=1, *, width=256, height=None, crop_top=None)` | `PIL.Image.Image` | `pdf` is a path or `bytes` |
| `thumbnail_bytes(pdf, page=1, *, width, height, crop_top, quality=80)` | `bytes` (WebP) | |
| `collect_pdfs(inputs, recursive=False)` | `list[(Path, Path)]` | Lists the PDFs found in the inputs, with each one's directory relative to its input folder |
| `parse_pages(spec, page_count)` | `list[int]` | Page indices, starting at 0 |
| `PDFThumbError` | exception | Raised for a corrupt or encrypted PDF, or a page that doesn't exist |

You can also run the CLI as a module: `python -m pdfthumb ...`

## Tests

```bash
./install.sh --dev && .venv/bin/pytest
```

## CI / Releasing to PyPI

- `.github/workflows/ci.yml` runs the tests on every push to `main` and on every PR. It covers Python 3.9–3.13 on Linux, plus macOS and Windows.
- `.github/workflows/publish.yml` runs when a `v*` tag is pushed. It tests and builds the package, checks it, publishes it to **PyPI**, and creates a GitHub release.
  Running the workflow manually ("Run workflow") publishes to **TestPyPI** instead, as a dry run.

One-time setup, using Trusted Publishing so no API token is stored:
1. On https://pypi.org/manage/account/publishing/, add a *pending publisher*:
   project `pdfthumb`, owner/repo = your GitHub repo, workflow `publish.yml`, environment `pypi`.
2. Optionally, do the same on https://test.pypi.org with environment `testpypi`.
3. In GitHub, go to **Settings → Environments** and create the `pypi` and `testpypi` environments. You can add required reviewers to them.

Release:
```bash
# bump __version__ in src/pdfthumb/__init__.py, then:
git commit -am "Release 0.1.1"
git tag v0.1.1 && git push origin main v0.1.1
```
The workflow fails if the tag doesn't match `__version__`.
