// Original business-document components for this adaptation. They build on
// `compact`, `small-text` and `signature-field` adapted from
// typst-gost/modern-g7-32 (GPL-3.0-only). Licensed under GPL-3.0-only,
// see ../LICENSE.

#import "utils.typ": compact, small-text, signature-field, unbreak-name

// Document heading: optional status line, kind and number, subject line,
// then place on the left and date on the right.
#let document-heading(
  kind,
  number: none,
  subject: none,
  status: none,
  place: none,
  date: none,
) = {
  set par(first-line-indent: 0pt, justify: false)
  align(center)[
    #if status != none [*#status*\ ]
    *#kind#if number != none [ № #number]*
    #if subject != none [\ #subject]
  ]
  if place != none or date != none {
    block(width: 100%, above: 0.75em, below: 0pt)[#place #h(1fr) #date]
  }
}

// Compact requisites: label in bold, lines at single spacing.
#let requisites(label, ..lines) = compact[
  *#label*\ #lines.pos().join(linebreak())
]

// Two requisite blocks side by side, e.g. parties.
#let requisites-pair(left, right) = compact(grid(
  columns: (1fr, 1fr),
  column-gutter: 10mm,
  left, right,
))

// Two signature fields side by side.
#let signatures(
  left: (position: [Исполнитель], name: none),
  right: (position: [Заказчик], name: none),
) = block(breakable: false, grid(
  columns: (1fr, 1fr),
  column-gutter: 10mm,
  signature-field(left.name, left.position),
  signature-field(right.name, right.position),
))

// Optional header of a contract appendix: starts a new page, centred.
#let contract-appendix-header(number, title, to: none, new-page: true) = {
  if new-page { pagebreak(weak: true) }
  set par(first-line-indent: 0pt, justify: false)
  align(center)[
    *Приложение № #number*
    #if to != none [\ #to]
    #if title != none [\ *#title*]
  ]
}

// Table at reduced size with a repeating, bold header row.
#let data-table(columns, header, rows, align: auto) = table(
  columns: columns,
  align: align,
  table.header(..header.map(h => strong(h))),
  ..rows.flatten(),
)
