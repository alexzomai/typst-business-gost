"""Template tests: geometry, pagination, spacing, fonts, validation, content."""
import re
import statistics
import unittest

import pymupdf
import typst

from helpers import (
    A4, BUILD, DIGIT_HEIGHT_EM, MM, TEMPLATE, ROOT, body_spans,
    compile_snippet, compile_to, full_text, render_pages, spans,
)

EXAMPLES = ["contract", "act", "invoice", "long-duplex"]
TOL = 1.5  # points, about 0.5 mm: PDF text coordinates are rounded by the font metrics


def compile_example(name):
    return compile_to(TEMPLATE / "examples" / f"{name}.typ", f"example-{name}")


class ExamplesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pdfs = {n: compile_example(n) for n in EXAMPLES}
        for n, p in cls.pdfs.items():
            render_pages(p, n)

    def test_all_examples_compile_with_pages(self):
        for n, p in self.pdfs.items():
            with pymupdf.open(p) as doc:
                self.assertGreaterEqual(len(doc), 1, n)
        with pymupdf.open(self.pdfs["long-duplex"]) as doc:
            self.assertGreaterEqual(len(doc), 6)
        with pymupdf.open(self.pdfs["contract"]) as doc:
            self.assertGreaterEqual(len(doc), 2)

    def test_a4_geometry(self):
        for n, p in self.pdfs.items():
            with pymupdf.open(p) as doc:
                for page in doc:
                    self.assertAlmostEqual(page.rect.width, A4[0], delta=0.6, msg=n)
                    self.assertAlmostEqual(page.rect.height, A4[1], delta=0.6, msg=n)

    def test_first_page_has_no_number_and_others_have(self):
        for n, p in self.pdfs.items():
            with pymupdf.open(p) as doc:
                for i, page in enumerate(doc, start=1):
                    top = [s for s in spans(page) if s[4] < 20 * MM]
                    if i == 1:
                        self.assertEqual(top, [], f"{n}: visible text in top field of page 1")
                    else:
                        self.assertEqual([s[0] for s in top], [str(i)], f"{n} page {i}")

    def test_page_number_position(self):
        # centred on the sheet, top of the digits 10 mm from the sheet edge
        for n, p in self.pdfs.items():
            duplex = n == "long-duplex"
            with pymupdf.open(p) as doc:
                for i, page in enumerate(doc, start=1):
                    if i == 1:
                        continue
                    text, size, _, ox, oy, bbox = next(s for s in spans(page) if s[4] < 20 * MM)
                    width = bbox[2] - bbox[0]
                    left, right = (30, 15)
                    if duplex and i % 2 == 0:
                        left, right = right, left
                    centre = A4[0] / 2
                    self.assertAlmostEqual((bbox[0] + bbox[2]) / 2, centre, delta=TOL, msg=f"{n} p{i} x")
                    glyph_top = oy - DIGIT_HEIGHT_EM * size
                    self.assertAlmostEqual(glyph_top, 10 * MM, delta=TOL, msg=f"{n} p{i} y")

    def test_body_within_margins(self):
        for n, p in self.pdfs.items():
            duplex = n == "long-duplex"
            with pymupdf.open(p) as doc:
                for i, page in enumerate(doc, start=1):
                    left, right = (30, 15)
                    if duplex and i % 2 == 0:
                        left, right = right, left
                    for text, size, _, ox, oy, bbox in body_spans(page, i):
                        self.assertGreaterEqual(bbox[0], left * MM - 0.6, f"{n} p{i} {text[:20]}")
                        self.assertLessEqual(bbox[2], A4[0] - right * MM + 0.6, f"{n} p{i} {text[:20]}")
                        self.assertGreaterEqual(oy - DIGIT_HEIGHT_EM * size, 20 * MM - TOL, f"{n} p{i} top")
                        self.assertLessEqual(oy, A4[1] - 20 * MM + 0.6, f"{n} p{i} bottom")

    def test_duplex_mirrors_left_and_right_margins(self):
        with pymupdf.open(self.pdfs["long-duplex"]) as doc:
            def min_x(page, i):
                return min(s[5][0] for s in body_spans(page, i))
            self.assertAlmostEqual(min_x(doc[1], 2), 15 * MM, delta=0.6)
            self.assertAlmostEqual(min_x(doc[2], 3), 30 * MM, delta=0.6)

    def test_font_family_and_size(self):
        for n, p in self.pdfs.items():
            with pymupdf.open(p) as doc:
                sizes = {}
                for i, page in enumerate(doc, start=1):
                    for text, size, font, *_ in spans(page):
                        self.assertIn("LiberationSerif", font, n)
                        sizes[round(size, 2)] = sizes.get(round(size, 2), 0) + len(text)
                self.assertEqual(max(sizes, key=sizes.get), 14.0, n)
                self.assertTrue(set(sizes) <= {14.0, 10.0}, f"{n}: unexpected sizes {sizes}")

    def lines(self, page, i):
        """Line starts (baseline y, x), one per baseline, without the page number."""
        first = {}
        for text, size, _, ox, oy, bbox in body_spans(page, i):
            y = round(oy, 1)
            first[y] = min(first.get(y, ox), ox)
        return sorted((y, x) for y, x in first.items())

    def test_baseline_pitch_is_size_times_factor(self):
        with pymupdf.open(self.pdfs["long-duplex"]) as doc:
            lines = self.lines(doc[1], 2)  # page of continuous body text
            diffs = [round(b[0] - a[0], 2) for a, b in zip(lines, lines[1:])]
            self.assertGreater(len(diffs), 20)
            self.assertAlmostEqual(statistics.mode(diffs), 14 * 1.5, delta=0.1, msg=str(diffs))
            self.assertGreaterEqual(min(diffs), 14 * 1.5 - 0.1)

    def test_first_line_indent(self):
        with pymupdf.open(self.pdfs["long-duplex"]) as doc:
            xs = [round(x, 1) for k in (2, 4, 6) for _, x in self.lines(doc[k], k + 1)]  # odd pages
            base = min(xs)
            self.assertAlmostEqual(base, 30 * MM, delta=0.6)
            indented = [x for x in xs if abs(x - base - 12.5 * MM) < 0.8]
            self.assertGreaterEqual(len(indented), 3)
            self.assertTrue(all(x - base < 0.6 or x - base > 12.5 * MM - 0.8 for x in xs))


LOREM = " ".join(["Стороны согласовали порядок исполнения обязательств по настоящему разделу договора."] * 30)


def doc_code(options, body=None):
    return f'#show: business-doc.with({options})\n{body or LOREM}\n'


class MetadataTest(unittest.TestCase):
    def test_document_metadata_combinations(self):
        cases = (
            ("none", "", "", ""),
            ("author-only", 'author: "Test Author"', "", "Test Author"),
            ("title-only", 'title: "Test Title"', "Test Title", ""),
            ("both", 'title: "Test Title", author: "Test Author"', "Test Title", "Test Author"),
        )
        for name, options, title, author in cases:
            with self.subTest(name=name):
                pdf = compile_snippet(f"metadata-{name}", doc_code(options, "Metadata test."))
                with pymupdf.open(pdf) as doc:
                    self.assertEqual(doc.metadata["title"], title)
                    self.assertEqual(doc.metadata["author"], author)


class LineSpacingTest(unittest.TestCase):
    def pitch(self, name, options):
        pdf = compile_snippet(name, doc_code(options))
        with pymupdf.open(pdf) as doc:
            ys = sorted({round(s[4], 1) for s in spans(doc[0])})
        diffs = [round(b - a, 2) for a, b in zip(ys, ys[1:])]
        return statistics.mode(diffs)

    def test_factors(self):
        for factor in (1.0, 1.25, 1.5):
            self.assertAlmostEqual(self.pitch(f"ls{factor}", f"line-spacing: {factor}"), 14 * factor, delta=0.1)

    def test_sizes(self):
        for size in (12, 13):
            self.assertAlmostEqual(self.pitch(f"sz{size}", f"text-size: {size}pt"), size * 1.5, delta=0.1)


class ValidationTest(unittest.TestCase):
    def fails(self, name, options, fragment):
        with self.assertRaises(typst.TypstError) as cm:
            compile_snippet(name, doc_code(options))
        self.assertIn(fragment, str(cm.exception), name)

    def test_margins_below_minimum_fail(self):
        base = "left: 30mm, right: 15mm, top: 20mm, bottom: 20mm"
        for key, value in (("left", "19mm"), ("right", "9mm"), ("top", "19mm"), ("bottom", "19mm")):
            margin = base.replace(f"{key}: " + {"left": "30mm", "right": "15mm", "top": "20mm", "bottom": "20mm"}[key], f"{key}: {value}")
            self.fails(f"m-{key}", f"margin: ({margin})", f"«{key}»")

    def test_long_retention_requires_30mm_left(self):
        self.fails("m-long", "margin: (left: 25mm, right: 15mm, top: 20mm, bottom: 20mm), long-retention: true", "более 10 лет")

    def test_margin_minimums_are_accepted(self):
        compile_snippet("m-min", doc_code("margin: (left: 20mm, right: 10mm, top: 20mm, bottom: 20mm)"))

    def test_font_size_out_of_range_fails(self):
        self.fails("fs-11", "text-size: 11pt", "12, 13, 14")
        self.fails("fs-15", "text-size: 15pt", "12, 13, 14")
        self.fails("fs-small-big", "text-size: (default: 12pt, small: 12pt)", "меньше основного")
        self.fails("fs-small-tiny", "text-size: (default: 12pt, small: 6pt)", "меньше 8 пт")

    def test_font_size_can_be_relaxed_explicitly(self):
        compile_snippet("fs-relaxed", doc_code("text-size: 11pt, strict-font-size: false"))

    def test_line_spacing_out_of_range_fails(self):
        self.fails("ls-low", "line-spacing: 0.9", "вне диапазона")
        self.fails("ls-high", "line-spacing: 1.6", "вне диапазона")

    def test_indent_and_paper_fail(self):
        self.fails("indent", "indent: 1cm", "1,25 см")
        self.fails("paper", 'paper: "a5"', "A4")

    def test_incomplete_margin_fails(self):
        self.fails("m-missing", "margin: (left: 30mm)", "right")


class ContentTest(unittest.TestCase):
    FORBIDDEN = re.compile(
        r"университет|кафедр|студент|руководител|реферат|дипломн|курсов|bibliograph|библиограф|"
        r"performer|supervisor|abstract|school|7\.32|add-pagebreaks|title-template|"
        r"ГОСТ Р 7\.0\.32|список использованных",
        re.I,
    )

    def active_files(self):
        return [p for d in ("src", "examples") for p in (TEMPLATE / d).rglob("*") if p.is_file()]

    def test_no_academic_content_in_active_files(self):
        files = self.active_files()
        self.assertGreaterEqual(len(files), 10)
        for p in files:
            hits = self.FORBIDDEN.findall(p.read_text(encoding="utf-8"))
            self.assertEqual(hits, [], f"{p.relative_to(ROOT)}: {hits}")

    def test_only_typst_files_are_active(self):
        for p in self.active_files():
            self.assertEqual(p.suffix, ".typ", p)

    def test_upstream_assets_and_academic_parts_absent(self):
        for name in ("assets", "template", "component", "title-templates", "preview", "features"):
            self.assertEqual(list(TEMPLATE.rglob(name)), [], name)

    def test_no_em_dash_in_client_copy(self):
        for p in self.active_files():
            self.assertNotIn("—", p.read_text(encoding="utf-8"), p.name)

    def test_license_is_full_gpl3(self):
        text = (TEMPLATE / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("GNU GENERAL PUBLIC LICENSE", text)
        self.assertIn("Version 3, 29 June 2007", text)
        self.assertIn("END OF TERMS AND CONDITIONS", text)
        self.assertGreaterEqual(len(text.splitlines()), 670)

    def test_examples_have_no_personal_identifiers(self):
        for n in EXAMPLES:
            text = full_text(compile_example(n))
            self.assertIsNone(re.search(r"\b\d{10,15}\b", text), n)


if __name__ == "__main__":
    unittest.main()
