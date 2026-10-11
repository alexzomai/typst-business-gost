# modern-g7-97: шаблон деловых документов (Typst)

Шаблон для договоров, актов и счетов на оплату. Оформление построено по ГОСТ Р 7.0.97-2025 (разделы 3 и 6.1, см. `docs/standard-matrix.md`). Основа: часть кода из typst-gost/modern-g7-32 под GPL-3.0, см. `NOTICE.md`.

Шаблон не гарантирует соответствие стандарту и не заменяет юридическую проверку документа.

## Умолчания
A4, поля 30/15/20/20 мм (левое, правое, верхнее, нижнее), Liberation Serif 14 пт, интервал 1,5, абзацный отступ 1,25 см, выравнивание по ширине. Нумерация со второй страницы по центру верхнего поля, первая страница без номера.

## Быстрый старт
```typ
#import "../src/export.typ": *
#show: business-doc.with(title: "Договор")

#document-heading("ДОГОВОР", number: "[номер]", subject: "оказания услуг",
  place: "[Место]", date: "[Дата]")

= Предмет договора
1.1. Текст пункта.

#signatures(
  left: (position: [Исполнитель], name: "[Инициалы Фамилия]"),
  right: (position: [Заказчик], name: "[Инициалы Фамилия]"),
)
```
Примеры: `examples/contract.typ`, `act.typ`, `invoice.typ`, `long-duplex.typ`.

## Параметры `business-doc`
| Параметр | По умолчанию | Проверка |
|---|---|---|
| `text-size` | `(default: 14pt, small: 10pt)` | основной 12, 13 или 14 пт; уменьшенный меньше основного и не менее 8 пт |
| `line-spacing` | `1.5` | от 1 до 1,5 |
| `margin` | `(left: 30mm, right: 15mm, top: 20mm, bottom: 20mm)` | не менее 20/10/20/20 мм |
| `long-retention` | `false` | при `true` левое поле не менее 30 мм |
| `duplex` | `false` | зеркальные поля для двусторонней печати, номер по центру листа |
| `indent` | `1.25cm` | ровно 1,25 см |
| `strict-font-size` | `true` | `false` снимает ограничение 12 до 14 пт |
| `heading-align` | `"indent"` | `"indent"` или `"center"` |
| `paper` | `"a4"` | только A4 |

Недопустимые значения останавливают компиляцию с понятным сообщением. Интервал считается как расстояние между базовыми линиями: размер шрифта умножить на `line-spacing` (14 пт и 1,5 дают 21 пт). Это не то же самое, что «множитель» в Word.

## Компоненты
`document-heading`, `requisites`, `requisites-pair`, `signatures`, `contract-appendix-header`, `data-table`, `small-text`, `compact`.

## Использование в другом документе
Импортируйте `src/export.typ` по относительному пути. Компилируйте с корнем, включающим шаблон:
```
typst compile --root . examples/contract.typ build/contract.pdf
```

## Установка и проверка
```
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
```
Результаты и изображения страниц лежат в `build/tests/` (в Git не попадают).

## Лицензия
Шаблон распространяется на условиях GPL-3.0 (`LICENSE`). Подробности и оговорки о частных документах: `docs/license.md`.
