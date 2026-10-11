"""Shared helpers: compile Typst to the ignored build folder and read PDF geometry."""
import re
import shutil
from pathlib import Path

import pymupdf
import typst

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT
BUILD = ROOT / "build" / "tests"
MM = 72 / 25.4
A4 = (210 * MM, 297 * MM)
# Height of Liberation Serif digits and capitals relative to the font size.
DIGIT_HEIGHT_EM = 0.676


def compile_to(source: Path, name: str) -> Path:
    BUILD.mkdir(parents=True, exist_ok=True)
    out = BUILD / f"{name}.pdf"
    typst.compile(str(source), output=str(out), root=str(ROOT))
    return out


def compile_snippet(name: str, code: str, imports=True) -> Path:
    """Compile a snippet that lives under the repo root so relative imports resolve."""
    folder = BUILD / "snippets"
    folder.mkdir(parents=True, exist_ok=True)
    src = folder / f"{name}.typ"
    header = '#import "/src/export.typ": *\n' if imports else ""
    src.write_text(header + code, encoding="utf-8")
    return compile_to(src, f"snippet-{name}")


def render_pages(pdf: Path, name: str, dpi=70, limit=4):
    folder = BUILD / "render"
    folder.mkdir(parents=True, exist_ok=True)
    with pymupdf.open(pdf) as doc:
        for i in range(min(limit, len(doc))):
            doc[i].get_pixmap(dpi=dpi).save(folder / f"{name}-{i + 1}.png")


def spans(page):
    """Yield (text, size, font, origin_x, origin_y, ink_bbox) for every text span.

    The bbox covers non-space glyphs only: PyMuPDF span boxes include trailing
    (justification-stretched) spaces, which are not visible ink.
    """
    for block in page.get_text("rawdict")["blocks"]:
        for line in block.get("lines", []):
            for s in line["spans"]:
                chars = [c for c in s["chars"] if c["c"].strip()]
                if chars:
                    boxes = [c["bbox"] for c in chars]
                    bbox = (min(b[0] for b in boxes), min(b[1] for b in boxes),
                            max(b[2] for b in boxes), max(b[3] for b in boxes))
                    yield ("".join(c["c"] for c in s["chars"]), s["size"], s["font"],
                           s["origin"][0], s["origin"][1], bbox)


def is_number_span(text, size, origin_y, page_number):
    return text.strip() == str(page_number) and origin_y < 20 * MM


def body_spans(page, page_number):
    return [s for s in spans(page) if not is_number_span(s[0], s[1], s[4], page_number)]


def full_text(pdf: Path) -> str:
    with pymupdf.open(pdf) as doc:
        text = "\n".join(p.get_text() for p in doc)
    return re.sub(r"\s+", " ", text.replace("\xad", "").replace("\xa0", " "))
