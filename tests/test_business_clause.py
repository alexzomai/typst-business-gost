"""PDF regressions for body blocks (3.4) and signature initials (5.22)."""
import unittest

import pymupdf
import typst

from helpers import A4, MM, body_spans, compile_snippet


class BusinessClauseTest(unittest.TestCase):
    TEXT = " ".join(["Текст условия договора для проверки абзацного отступа и выравнивания"] * 8)

    def compile_clause(self, name, body, options="", arguments=""):
        try:
            return compile_snippet(name, f'''#show: business-doc.with({options})
#block[
  // Embedding blocks can reset paragraph styles (e.g. compact requisites).
  #set par(first-line-indent: 0pt, justify: false)
  #business-clause({arguments})[
{body}
  ]
]
''')
        except typst.TypstError as exc:
            self.fail(f"business-clause must be exported and compile: {exc}")

    def test_nested_block_indents_each_paragraph_and_justifies(self):
        pdf = self.compile_clause("clause-indent", f"Первый {self.TEXT}\n\nВторой {self.TEXT}",
                                  options="justify: false")
        with pymupdf.open(pdf) as doc:
            rows = list(body_spans(doc[0], 1))
        lines = {}
        for row in rows:
            lines.setdefault(round(row[4], 2), []).append(row)
        paragraphs = [[], []]
        current = 0
        for spans in lines.values():
            text = "".join(s[0] for s in spans)
            if "Второй" in text:
                current = 1
            paragraphs[current].append((text, min(s[3] for s in spans), max(s[5][2] for s in spans)))
        for paragraph in paragraphs:
            self.assertGreaterEqual(len(paragraph), 3, paragraph)
            self.assertAlmostEqual(paragraph[0][1] / MM, 42.5, delta=0.2)
            for text, x, right in paragraph[1:]:
                self.assertAlmostEqual(x / MM, 30, delta=0.2, msg=text)
            # Every non-final line fills the available width, even if the outer
            # document opts out of justification. Ink boxes exclude spaces.
            for text, x, right in paragraph[:-1]:
                self.assertAlmostEqual(right, A4[0] - 15 * MM, delta=0.6, msg=text)

    def test_inline_numbered_clause_after_heading(self):
        pdf = compile_snippet('clause-inline-numbered', f'''#show: business-doc.with()
#let clause(body) = business-clause(body)
= Условия
#clause[1\\.1. Первый {self.TEXT}]
''')
        with pymupdf.open(pdf) as doc:
            lines = [line for block in doc[0].get_text('dict')['blocks']
                     for line in block.get('lines', [])
                     if ''.join(s['text'] for s in line['spans']).startswith('1.1.')]
            self.assertEqual(len(lines), 1)
            self.assertAlmostEqual(lines[0]['bbox'][0] / MM, 42.5, delta=0.2)

    def test_explicit_paragraphs_are_preserved(self):
        for name, content in (
            ('explicit-one', '#par[Первый текст.]'),
            ('explicit-two', '#par[Первый текст.]#par[Второй текст.]'),
            ('wrapped-two', '#align(left)[Первый текст.\n\nВторой текст.]'),
        ):
            with self.subTest(name=name):
                pdf = compile_snippet(name, '#show: business-doc.with()\n#business-clause[' + content + ']')
                with pymupdf.open(pdf) as doc:
                    self.assertIn('Первый текст.', doc[0].get_text())
                    if name != 'explicit-one':
                        self.assertIn('Второй текст.', doc[0].get_text())
                        starts = [(span['text'], span['origin'][1])
                                  for b in doc[0].get_text('dict')['blocks']
                                  for line in b.get('lines', []) for span in line['spans']
                                  if 'Первый' in span['text'] or 'Второй' in span['text']]
                        self.assertEqual(len(starts), 2)
                        self.assertGreater(starts[1][1], starts[0][1])

    def test_breakable_default_can_span_pages(self):
        pdf = self.compile_clause("clause-breakable", "\n\n".join([self.TEXT] * 14))
        with pymupdf.open(pdf) as doc:
            self.assertGreater(len(doc), 1)
            self.assertTrue(all(body_spans(p, i + 1) for i, p in enumerate(doc)))

    def test_unbreakable_clause_moves_together(self):
        code = f'''#show: business-doc.with()
#v(210mm)
#business-clause(breakable: false)[
Начало {self.TEXT}

Конец условия.
]
'''
        try:
            pdf = compile_snippet("clause-unbreakable", code)
        except typst.TypstError as exc:
            self.fail(f"business-clause must support breakable: false: {exc}")
        with pymupdf.open(pdf) as doc:
            self.assertEqual(len(doc), 2)
            self.assertNotIn("Начало", doc[0].get_text())
            self.assertIn("Начало", doc[1].get_text())
            self.assertIn("Конец", doc[1].get_text())


class SignatureInitialsTest(unittest.TestCase):
    def test_spaces_between_initials_removed_but_surname_gap_kept(self):
        for index, gap in enumerate((" ", "\u00a0", "  \u00a0 ", "")):
            for surname_gap in (" ", "\u00a0"):
                with self.subTest(gap=repr(gap), surname_gap=repr(surname_gap)):
                    pdf = compile_snippet(f"initials-{index}-{ord(surname_gap)}", f'''#show: business-doc.with()
#import "/src/utils.typ": signature-field
#signature-field("И.{gap}И.{surname_gap}Иванов", [Директор])
''')
                    with pymupdf.open(pdf) as doc:
                        name = [s for s in body_spans(doc[0], 1) if "Иванов" in s[0]]
                        self.assertEqual(len(name), 1, name)
                        self.assertEqual(name[0][0].replace("\u00a0", " ").strip(), "И.И. Иванов")
                        # Measure the compiled glyphs too: initials have no gap,
                        # while the surname keeps one space advance.
                        chars = [c for b in doc[0].get_text("rawdict")["blocks"]
                                 for line in b.get("lines", []) for s in line["spans"]
                                 if "Иванов" in "".join(c["c"] for c in s["chars"])
                                 for c in s["chars"]]
                        self.assertEqual("".join(c["c"] for c in chars).replace("\u00a0", " ").strip(), "И.И. Иванов")
                        self.assertAlmostEqual(chars[2]["origin"][0], chars[1]["bbox"][2], delta=0.1)
                        self.assertGreater(chars[5]["origin"][0] - chars[3]["bbox"][2], 2)


class PublicExampleTest(unittest.TestCase):
    def test_readme_explains_clause_and_full_appendix_signature(self):
        from helpers import ROOT
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for term in ("business-clause(body, breakable: true)", "signature-lines", "пустые линии", "не полноценный реквизит"):
            self.assertIn(term, text)

    def test_contract_appendix_uses_exported_clause_and_full_signatures(self):
        from helpers import ROOT, compile_to
        source = ROOT / "examples/contract.typ"
        self.assertIn("#business-clause", source.read_text(encoding="utf-8"))
        pdf = compile_to(source, "contract-clause-appendix")
        with pymupdf.open(pdf) as doc:
            text = doc[-1].get_text().replace("\u00a0", " ")
            self.assertIn("Исполнитель", text)
            self.assertIn("Заказчик", text)
            self.assertEqual(text.count("подпись"), 2)
            self.assertEqual(text.count("[И.О. Фамилия]"), 2)


if __name__ == "__main__":
    unittest.main()
