from pathlib import Path

import pymupdf as fitz
import pytest
from PIL import Image

from pdfthumb.cli import main
from pdfthumb.render import parse_pages


def make_pdf(path: Path, pages: int = 3) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    for i in range(pages):
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 72), f"Page {i + 1}", fontsize=36)
    doc.save(path)
    doc.close()
    return path


def test_parse_pages():
    assert parse_pages("1", 3) == [0]
    assert parse_pages("all", 3) == [0, 1, 2]
    assert parse_pages("1,3-5", 4) == [0, 2, 3]
    assert parse_pages("2-", 3) == [1, 2]
    with pytest.raises(ValueError):
        parse_pages("0", 3)


def test_single_file(tmp_path):
    pdf = make_pdf(tmp_path / "a.pdf")
    out = tmp_path / "out"
    assert main([str(pdf), "-o", str(out)]) == 0
    img = Image.open(out / "a.webp")
    assert img.format == "WEBP" and img.width == 256


def test_multiple_files_and_pages(tmp_path):
    a, b = make_pdf(tmp_path / "a.pdf"), make_pdf(tmp_path / "b.pdf", 2)
    out = tmp_path / "out"
    assert main([str(a), str(b), "-o", str(out), "-p", "all", "-w", "100", "-j", "2"]) == 0
    names = sorted(p.name for p in out.iterdir())
    assert names == ["a_p1.webp", "a_p2.webp", "a_p3.webp", "b_p1.webp", "b_p2.webp"]


def test_directory_recursive(tmp_path):
    src = tmp_path / "src"
    make_pdf(src / "top.pdf")
    make_pdf(src / "sub" / "top.pdf")
    (src / "note.txt").write_text("x")
    out = tmp_path / "out"
    assert main([str(src), "-o", str(out)]) == 0
    assert (out / "top.webp").exists() and not (out / "sub").exists()
    assert main([str(src), "-o", str(out), "-r"]) == 0
    assert (out / "sub" / "top.webp").exists()


def test_height_fit_and_corrupt(tmp_path):
    good = make_pdf(tmp_path / "g.pdf")
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"not a pdf")
    out = tmp_path / "out"
    assert main([str(good), str(bad), "-o", str(out), "--height", "100"]) == 1
    img = Image.open(out / "g.webp")
    assert img.height == 100 and img.width < 256


def test_crop_top(tmp_path):
    pdf = make_pdf(tmp_path / "a.pdf")
    out = tmp_path / "out"
    assert main([str(pdf), "-o", str(out), "--crop-top"]) == 0
    assert Image.open(out / "a.webp").size == (256, 256)
    assert main([str(pdf), "-o", str(out), "-c", "0.5", "--overwrite"]) == 0
    assert Image.open(out / "a.webp").size == (256, 128)
    # ratio larger than page aspect is capped at full page
    assert main([str(pdf), "-o", str(out), "-c", "5", "--overwrite"]) == 0
    assert Image.open(out / "a.webp").size == (256, 362)
    assert main([str(pdf), "-o", str(out), "-c", "--height", "10"]) == 2


def test_library_api(tmp_path):
    import io
    import pdfthumb

    pdf = make_pdf(tmp_path / "a.pdf")
    img = pdfthumb.render_thumbnail(pdf, page=2, width=120, crop_top=1)
    assert img.size == (120, 120)
    data = pdfthumb.thumbnail_bytes(pdf.read_bytes(), width=64)
    assert Image.open(io.BytesIO(data)).format == "WEBP"
    with pytest.raises(pdfthumb.PDFThumbError):
        pdfthumb.render_thumbnail(pdf, page=9)
    with pytest.raises(pdfthumb.PDFThumbError):
        pdfthumb.thumbnail_bytes(b"garbage")
    with pytest.raises(ValueError):
        pdfthumb.generate_thumbnails(pdf, tmp_path, quality=500)

    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"x")
    results = pdfthumb.generate_thumbnails([pdf, bad], tmp_path / "out", pages="all")
    assert [r.status for r in results if r.ok] == ["ok"] * 3
    assert [r for r in results if not r.ok][0].input == str(bad)
