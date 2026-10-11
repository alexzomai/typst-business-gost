"""Geometry regressions for reusable stacked signature blanks."""
import unittest
import pymupdf
from helpers import compile_snippet, MM, spans


class SignatureLinesTest(unittest.TestCase):
    def test_rejects_overlap_and_overwide_labels(self):
        for name, code in (
            ('narrow', '#block(width: 70mm)[#signature-lines()]'),
            ('long', '#signature-lines(labels: ([ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZ],))'),
        ):
            with self.subTest(name=name), self.assertRaisesRegex(Exception, 'signature-lines:'):
                compile_snippet('signature-reject-' + name, '#show: business-doc\n' + code)

    def test_alignment_under_body_indentation(self):
        for size in (12, 13, 14):
            with self.subTest(size=size):
                pdf = compile_snippet(f"signature-lines-{size}", f'''#show: business-doc.with(text-size: {size}pt)
Текст перед подписями.

#signature-lines()
''')
                with pymupdf.open(pdf) as doc:
                    page = doc[0]
                    labels = [s for s in spans(page) if s[0].strip() in ("Исполнитель:", "Заказчик:")]
                    self.assertEqual(len(labels), 2)
                    self.assertAlmostEqual(labels[0][3], labels[1][3], delta=0.1)
                    lines = [item for d in page.get_drawings() for item in d['items'] if item[0] == 'l']
                    self.assertEqual(len(lines), 2)
                    self.assertAlmostEqual(lines[0][1].x, lines[1][1].x, delta=0.1)
                    self.assertAlmostEqual(lines[0][2].x, lines[1][2].x, delta=0.1)
                    self.assertAlmostEqual(lines[0][2].x-lines[0][1].x, 60*MM, delta=0.1)
                    self.assertGreater(lines[0][1].x, max(s[5][2] for s in labels))
                    self.assertGreater(lines[1][1].y, lines[0][1].y)
