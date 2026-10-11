"""Tests for the normative audit fixes (GOST R 7.0.97-2025 items 3.4, 3.5, 5.17, 5.18, 5.19, 5.22)."""
import unittest

import pymupdf
import typst

from helpers import MM, A4, body_spans, compile_snippet, spans

TOL = 1.5
LEFT = 30 * MM
RIGHT_EDGE = A4[0] - 15 * MM
CENTRE = (LEFT + RIGHT_EDGE) / 2


def doc(body, options=""):
    return f"#show: business-doc.with({options})\n{body}\n"


def lines_of(pdf, page=0):
    """Return list of (text, size, origin_x, origin_y, bbox) per span, top to bottom."""
    with pymupdf.open(pdf) as d:
        return sorted(((t, s, ox, oy, bb) for t, s, f, ox, oy, bb in body_spans(d[page], page + 1)),
                      key=lambda r: (round(r[3], 1), r[2]))


def find(rows, fragment):
    return [r for r in rows if fragment in r[0]]


class HeadingTest(unittest.TestCase):
    CODE = '#document-heading("ДОГОВОР", number: "[номер]", subject: "об оказании услуг по настоящему договору между сторонами, заключаемому на условиях, указанных ниже в тексте", place: "[Место]", date: "[Дата]")\nТекст.'

    def rows(self):
        return lines_of(compile_snippet("heading", doc(self.CODE)))

    def test_kind_is_centred(self):
        kind = find(self.rows(), "ДОГОВОР")[0]
        self.assertAlmostEqual((kind[4][0] + kind[4][2]) / 2, CENTRE, delta=TOL)

    def test_subject_is_left_from_left_margin_without_indent(self):
        rows = self.rows()
        subject = [r for r in rows if r[3] > find(rows, "ДОГОВОР")[0][3] + 1 and r[3] < find(rows, "[Место]")[0][3] - 1]
        self.assertGreaterEqual(len(subject), 2, "subject must wrap onto several lines for this check")
        for r in subject:
            self.assertAlmostEqual(r[4][0], LEFT, delta=TOL, msg=r[0])

    def test_heading_components_use_single_spacing(self):
        # inside a component the pitch is one 14 pt line; components are separated
        # by one extra interval (item 3.4), not by the 21 pt body pitch
        rows = self.rows()
        kind, place = find(rows, "ДОГОВОР")[0], find(rows, "[Место]")[0]
        subject = [r for r in rows if kind[3] + 1 < r[3] < place[3] - 1]
        ys = [round(r[3], 1) for r in subject]
        self.assertTrue(all(abs(b - a - 14) < 0.2 for a, b in zip(ys, ys[1:])), ys)
        self.assertLess(subject[0][3] - kind[3], 14 + 0.75 * 14 + 0.2)
        self.assertGreater(subject[0][3] - kind[3], 14 + 0.2)


    def test_plain_string_subject_must_start_with_o_or_ob(self):
        for ok in ("об оказании услуг", "О поставке товаров", "о поставке"):
            compile_snippet("subj-ok", doc(f'#document-heading("ДОГОВОР", subject: "{ok}")'))
        for bad in ("оказания услуг", "Оказание услуг", "Объём работ"):
            with self.assertRaises(typst.TypstError, msg=bad) as cm:
                compile_snippet("subj-bad", doc(f'#document-heading("ДОГОВОР", subject: "{bad}")'))
            self.assertIn("«О» или «Об»", str(cm.exception))

    def test_content_subject_is_the_callers_responsibility(self):
        compile_snippet("subj-content", doc('#document-heading("ДОГОВОР", subject: [оказания услуг])'))


class AppendixHeaderTest(unittest.TestCase):
    CORNER = 80 * MM  # item 3.5: the longest line of a corner requisite is at most 8 cm
    LONG = "к договору оказания консультационных и информационных услуг от [дата] № [номер]"

    def rows(self, name, call):
        return lines_of(compile_snippet(name, doc(f"Основной текст.\n{call}\nТекст приложения.")), page=1)

    def attribution(self, rows):
        top = find(rows, "Приложение")[0]
        text = [r for r in rows if r[3] < find(rows, "Текст приложения")[0][3] - 1]
        return top, text

    def test_attribution_is_in_the_upper_right_corner_within_8_cm(self):
        rows = self.rows("app-corner", f'#contract-appendix-header(1, [Перечень услуг], to: [{self.LONG}])')
        top, block = self.attribution(rows)
        attribution = [r for r in block if "Перечень" not in r[0]]
        self.assertGreaterEqual(len(attribution), 3, "long reference must wrap")
        for r in attribution:
            self.assertGreaterEqual(r[4][0], RIGHT_EDGE - self.CORNER - 0.6, r[0])
            self.assertLessEqual(r[4][2], RIGHT_EDGE + 0.6, r[0])
        self.assertAlmostEqual(min(r[4][0] for r in attribution), RIGHT_EDGE - self.CORNER, delta=TOL)
        self.assertLess(top[3], 20 * MM + 20, "attribution starts at the top of the page")

    def test_attribution_lines_are_left_aligned_at_single_spacing(self):
        rows = self.rows("app-left", f'#contract-appendix-header(1, [Перечень услуг], to: [{self.LONG}])')
        _, block = self.attribution(rows)
        attribution = [r for r in block if "Перечень" not in r[0]]
        xs = {round(r[4][0]) for r in attribution}
        self.assertEqual(len(xs), 1, xs)
        ys = [r[3] for r in attribution]
        self.assertTrue(all(abs(b - a - 14) < 0.2 for a, b in zip(ys, ys[1:])), ys)

    def test_title_is_separate_and_centred(self):
        rows = self.rows("app-title", '#contract-appendix-header(1, [Перечень услуг])')
        title = find(rows, "Перечень")[0]
        self.assertAlmostEqual((title[4][0] + title[4][2]) / 2, CENTRE, delta=TOL)
        self.assertGreater(title[3], find(rows, "Приложение")[0][3] + 13)

    def test_default_reference_is_a_placeholder_for_kind_date_and_number(self):
        rows = self.rows("app-default", '#contract-appendix-header(2, [Перечень услуг])')
        text = " ".join(" ".join(r[0] for r in rows).split())
        self.assertIn("[вид, дата и номер основного документа]", text)

    def test_structured_reference_has_kind_date_and_number(self):
        rows = self.rows("app-struct", '#contract-appendix-header(3, [Перечень услуг], base-kind: "договору", base-date: "[дата]", base-number: "[номер]")')
        text = " ".join(" ".join(r[0] for r in rows).split())
        self.assertIn("Приложение № 3", text)
        self.assertIn("к договору от [дата] № [номер]", text)

    def test_partial_structured_reference_preserves_each_missing_field(self):
        fields = ("base-kind", "base-date", "base-number")
        values = ("договору", "01.01.2026", "123")
        placeholders = ("[вид основного документа]", "[дата]", "[номер]")
        for mask in range(1, 7):
            args = ", ".join(f'{field}: "{value}"' for i, (field, value) in enumerate(zip(fields, values)) if mask & (1 << i))
            with self.subTest(args=args):
                rows = self.rows("app-partial", f'#contract-appendix-header(1, none, {args})')
                text = " ".join(" ".join(r[0] for r in rows).split())
                for i in range(3):
                    self.assertIn(values[i] if mask & (1 << i) else placeholders[i], text)
                self.assertIn(" от ", text)
                self.assertIn(" № ", text)

    def test_existing_to_argument_still_works(self):
        compile_snippet("app-to", doc('#contract-appendix-header(1, [Перечень], to: [к договору № [номер]])'))


class SignaturesTest(unittest.TestCase):
    LONG_L = "Заместитель директора по финансовым вопросам и экономическому развитию"
    LONG_R = "Заместитель директора по административным вопросам и хозяйственной части"

    def rows(self, name, call):
        return lines_of(compile_snippet(name, doc(call)))

    def side(self, name="sig-side"):
        return self.rows(name, f'#signatures(left: (position: [{self.LONG_L}], name: "[И.О. Фамилия]"), right: (position: [{self.LONG_R}], name: "[И.О. Фамилия]"))')

    def test_everything_in_the_block_is_body_size(self):
        # item 3.3 allows smaller type only for tables and requisites 08 and 25;
        # the signature (item 5.22) is body text, so position, caption and name are 14 pt
        for r in self.side():
            self.assertAlmostEqual(r[1], 14, delta=0.01, msg=r[0])

    def test_multiline_position_is_single_spaced(self):
        rows = self.side()
        left = sorted({round(r[3], 1) for r in rows if r[4][2] < CENTRE and "подпись" not in r[0] and "Фамилия" not in r[0]})
        self.assertGreaterEqual(len(left), 3, left)
        self.assertTrue(all(abs(b - a - 14) < 0.2 for a, b in zip(left, left[1:])), left)

    def test_order_position_then_signature_then_name_and_equal_ranks_side_by_side(self):
        rows = self.side()
        column = lambda right: [r for r in rows if (r[4][0] >= CENTRE - 5) == right]
        pos_l = min((r for r in column(False) if "Заместитель" in r[0]), key=lambda r: r[3])
        pos_r = min((r for r in column(True) if "Заместитель" in r[0]), key=lambda r: r[3])
        self.assertAlmostEqual(pos_l[3], pos_r[3], delta=0.1)
        self.assertLess(pos_l[4][0], pos_r[4][0])
        for right in (False, True):
            col = column(right)
            caption = find(col, "подпись")[0]
            name = find(col, "Фамилия")[0]
            last_position = max(r[3] for r in col if r is not caption and r is not name)
            self.assertGreater(caption[3], last_position)
            self.assertAlmostEqual(name[3], caption[3], delta=3)
        self.assertLess(find(column(False), "подпись")[0][4][0], find(column(True), "подпись")[0][4][0])

    def test_unequal_wrapped_positions_share_signature_and_name_baselines(self):
        rows = self.rows("sig-unequal", f'#signatures(left: (position: [{self.LONG_L}], name: "И.О. Первый"), right: (position: [Директор], name: "И.О. Второй"))')
        captions = find(rows, "подпись")
        self.assertEqual(len(captions), 2)
        self.assertAlmostEqual(captions[0][3], captions[1][3], delta=0.1)
        self.assertAlmostEqual(find(rows, "Первый")[0][3], find(rows, "Второй")[0][3], delta=0.1)
        position_rows = [r for r in rows if r[4][2] < CENTRE and "подпись" not in r[0] and "Первый" not in r[0]]
        self.assertGreaterEqual(len(position_rows), 3)
        self.assertGreater(captions[0][3], max(r[3] for r in position_rows))

    def test_vertical_layout_stacks_different_ranks_in_the_given_order(self):
        rows = self.rows("sig-vert", '#signatures(layout: "vertical", left: (position: [Директор], name: "[И.О. Фамилия]"), right: (position: [Главный бухгалтер], name: "[И.О. Фамилия]"))')
        director, accountant = find(rows, "Директор")[0], find(rows, "Главный бухгалтер")[0]
        self.assertGreater(accountant[3], director[3] + 2 * 14)
        self.assertAlmostEqual(director[4][0], LEFT, delta=TOL)
        self.assertAlmostEqual(accountant[4][0], LEFT, delta=TOL)
        first_name, second_name = sorted(find(rows, "Фамилия"), key=lambda r: r[3])
        self.assertLess(first_name[3], accountant[3])
        self.assertGreater(second_name[3], accountant[3])

    def test_unknown_layout_fails(self):
        with self.assertRaises(typst.TypstError) as cm:
            compile_snippet("sig-bad", doc('#signatures(layout: "diagonal")'))
        self.assertIn("«horizontal» или «vertical»", str(cm.exception))


class ExampleDocumentsTest(unittest.TestCase):
    @staticmethod
    def example(name):
        from helpers import compile_to, TEMPLATE
        return compile_to(TEMPLATE / "examples" / f"{name}.typ", f"conf-example-{name}")

    def test_invoice_signs_director_above_accountant(self):
        pdf = self.example("invoice")
        with pymupdf.open(pdf) as d:
            rows = []
            for i, page in enumerate(d, start=1):
                rows += [(t, s, ox, oy + i * 1000, bb) for t, s, f, ox, oy, bb in body_spans(page, i)]
        director, accountant = find(rows, "Директор")[0], find(rows, "Бухгалтер")[0]
        self.assertGreater(accountant[3], director[3])
        self.assertAlmostEqual(director[4][0], accountant[4][0], delta=TOL)

    def test_contract_appendix_example_has_kind_date_and_number_in_the_corner(self):
        pdf = self.example("contract")
        with pymupdf.open(pdf) as d:
            rows = lines_of(pdf, page=len(d) - 1)
        text = " ".join(" ".join(r[0] for r in rows).split())
        self.assertIn("к договору от [дата] № [номер]", text)
        self.assertGreaterEqual(find(rows, "Приложение")[0][4][0], RIGHT_EDGE - 80 * MM - 0.6)


class RequisiteZoneTest(unittest.TestCase):
    LONG = "Очень длинная строка реквизита бланка организации с подробным описанием для проверки переноса по ширине зоны"

    def width(self, name, call, **kw):
        rows = lines_of(compile_snippet(name, doc(call)))
        rows = [r for r in rows if r[3] > 0]
        return rows

    def test_corner_requisite_lines_are_at_most_8_cm(self):
        rows = self.width("zone-corner", f'#form-requisite("corner", [Заголовок:], [{self.LONG}])')
        self.assertGreaterEqual(len({round(r[3]) for r in rows}), 3, "long line must wrap")
        for r in rows:
            self.assertLessEqual(r[4][2] - LEFT, 80 * MM + 0.6, r[0])
            self.assertAlmostEqual(r[4][0], LEFT, delta=TOL)

    def test_longitudinal_requisite_lines_are_at_most_12_cm_and_wider_than_corner(self):
        rows = self.width("zone-long", f'#form-requisite("longitudinal", [Заголовок:], [{self.LONG}])')
        widest = max(r[4][2] - LEFT for r in rows)
        self.assertLessEqual(widest, 120 * MM + 0.6)
        self.assertGreater(widest, 80 * MM + 5, "12 cm zone must not be narrowed to 8 cm")

    def test_generic_requisites_stay_unconstrained(self):
        rows = self.width("zone-generic", f'#requisites([Банк:], [{self.LONG}])')
        self.assertGreater(max(r[4][2] - LEFT for r in rows), 120 * MM, "business blocks keep the full width")

    def test_requisite_can_be_placed_at_the_right_edge(self):
        rows = self.width("zone-right", f'#form-requisite("corner", [Гриф:], [{self.LONG}], align: right)')
        for r in rows:
            self.assertLessEqual(r[4][2], RIGHT_EDGE + 0.6)
            self.assertGreaterEqual(r[4][0], RIGHT_EDGE - 80 * MM - 0.6)

    def test_unknown_placement_fails(self):
        with self.assertRaises(typst.TypstError) as cm:
            compile_snippet("zone-bad", doc('#form-requisite("diagonal", [A], [B])'))
        self.assertIn("«corner» или «longitudinal»", str(cm.exception))


class UnbreakableZoneTest(unittest.TestCase):
    TOKENS = ("W" * 80, "Ш" * 80, "https://example.org/" + "x" * 160, "REF-" + "9" * 160)

    def test_form_requisites_reject_overwide_tokens_with_clear_error(self):
        for placement in ("corner", "longitudinal"):
            for token in self.TOKENS:
                for content in (f'"{token}"', f'strong("{token}")', f'link("{token}")' if token.startswith("https") else f'[{token}]'):
                    with self.subTest(placement=placement, content=content):
                        with self.assertRaises(typst.TypstError) as cm:
                            compile_snippet("zone-token", doc(f'#form-requisite("{placement}", [Реквизит], {content})'))
                        self.assertIn("превышает ширину зоны", str(cm.exception))

    def test_appendix_attribution_rejects_overwide_tokens_with_clear_error(self):
        for token in self.TOKENS:
            for args in (f'to: [{token}]', f'base-kind: "{token}"', f'base-date: "{token}"', f'base-number: "{token}"'):
                with self.subTest(args=args):
                    with self.assertRaises(typst.TypstError) as cm:
                        compile_snippet("app-token", doc(f'#contract-appendix-header(1, none, {args})'))
                    self.assertIn("превышает ширину зоны", str(cm.exception))


class HeadingLevelsTest(unittest.TestCase):
    def test_four_levels_compile(self):
        compile_snippet("levels-4", doc("= Раздел\n== Подраздел\n=== Пункт\n==== Подпункт\nТекст."))

    def test_fifth_level_fails(self):
        with self.assertRaises(typst.TypstError) as cm:
            compile_snippet("levels-5", doc("= А\n== Б\n=== В\n==== Г\n===== Д\nТекст."))
        self.assertIn("не должно быть более четырёх", str(cm.exception))


class DocumentationTest(unittest.TestCase):
    def read(self, name):
        from helpers import ROOT
        return (ROOT / name).read_text(encoding="utf-8")

    def test_matrix_covers_audited_clauses(self):
        text = self.read("docs/standard-matrix.md")
        for clause in ("| 3.5 |", "| 5.17 |", "| 5.18 |", "| 5.19 |", "| 5.22 |"):
            self.assertIn(clause, text)

    def test_matrix_states_spacing_correspondence_is_unproven(self):
        text = self.read("docs/standard-matrix.md")
        self.assertIn("не доказано", text)
        self.assertIn("кегль", text)
        self.assertIn("таблицы, реквизиты 08 и 25", text)
        self.assertIn("И.О. Фамилия", text)
        self.assertIn("ответственность", text)

    def test_matrix_separates_geometry_from_semantic_rules(self):
        text = self.read("docs/standard-matrix.md")
        self.assertIn("Проверяется геометрия", text)
        self.assertIn("Остаётся ответственностью автора документа", text)

    def test_audit_report_exists_with_findings_and_sources(self):
        text = self.read("docs/conformity-audit.md")
        for heading in ("## Исправлено", "## Не решено", "## Источники", "## Измеренные факты"):
            self.assertIn(heading, text)

    def test_audit_identifies_signature_22_outside_font_exceptions(self):
        text = self.read("docs/conformity-audit.md")
        self.assertIn("Подпись — реквизит 22", text)
        self.assertNotIn("Является ли подпись", text)
        self.assertIn("реквизиты 08 и 25", text)

    def test_zone_documentation_does_not_guarantee_arbitrary_content_width(self):
        for name in ("README.md", "docs/standard-matrix.md", "docs/conformity-audit.md"):
            text = self.read(name)
            self.assertIn("не гарантируется", text, name)
            self.assertIn("токен", text, name)

    def test_no_claim_of_full_compliance(self):
        import re
        for name in ("README.md", "docs/standard-matrix.md", "docs/conformity-audit.md"):
            text = self.read(name).lower()
            for hit in re.finditer(r"(полн\w+ соответстви\w+|full (gost )?compliance)", text):
                before = text[max(0, hit.start() - 40):hit.start()]
                self.assertRegex(before, r"(не |без |нет |отсутств)", f"{name}: {hit.group(0)}")

    def test_readme_lists_new_api_and_limited_support(self):
        text = self.read("README.md")
        for word in ("form-requisite", "layout", "base-kind", "ограничен"):
            self.assertIn(word, text)


if __name__ == "__main__":
    unittest.main()
