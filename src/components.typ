// Original business-document components for this adaptation. They build on
// `compact`, `small-text` and `signature-field` adapted from
// typst-gost/modern-g7-32 (GPL-3.0-only). Licensed under GPL-3.0-only,
// see ../LICENSE.

#import "constants.typ": corner-zone-width, longitudinal-zone-width
#import "utils.typ": compact, small-text, signature-field, unbreak-name, get-config, spaced

// Body clause (item 3.4), optionally kept together on a page.
// Set paragraph styles INSIDE the block: embedding contexts may reset them.
// Detect paragraph structure recursively, including explicit par() and wrappers.
// Wrapping an existing block-level paragraph in par() can silently lose text.
#let has-paragraph-structure(body) = {
  if type(body) != content { return false }
  if body.func() in (par, parbreak) { return true }
  if body.has("children") and body.children.any(has-paragraph-structure) { return true }
  if body.has("body") { return has-paragraph-structure(body.body) }
  false
}

#let business-clause(body, breakable: true) = context {
  let cfg = get-config()
  block(width: 100%, breakable: breakable)[
    #set par(first-line-indent: (amount: cfg.indent, all: true), justify: true)
    #if has-paragraph-structure(body) {
      body
    } else {
      par(body)
    }
  ]
}

// Document heading (item 5.17): optional status line, kind and number
// centred; the subject ("heading to the text", wording "О"/"Об") starts at the
// left margin; place on the left and date on the right. Components are set at
// single spacing, separated by an extra interval (item 3.4).
#let document-heading(
  kind,
  number: none,
  subject: none,
  status: none,
  place: none,
  date: none,
) = {
  if type(subject) == str {
    assert(
      lower(subject.split(" ").at(0)) in ("о", "об"),
      message: "subject: заголовок к тексту формулируется с предлогом «О» или «Об» (п. 5.17), получено «" + subject + "»",
    )
  }
  set par(first-line-indent: 0pt, justify: false)
  compact[
    #align(center, {
      if status != none { strong(status); linebreak() }
      strong[#kind#if number != none [ № #number]]
    })
    #if subject != none [
      #v(0.75em, weak: true)
      #align(left, subject)
    ]
  ]
  if place != none or date != none {
    compact[#place #h(1fr) #date]
  }
}

// Compact requisites: label in bold, lines at single spacing.
#let requisites(label, ..lines) = compact[
  *#label*\ #lines.pos().join(linebreak())
]

// Requisite of a form (item 3.5): the longest line is at most 8 cm for the
// "corner" placement and 12 cm for the "longitudinal" one. The zone is a width
// limit only; `align` puts the zone at the left or right edge of the text area.
// Generic business blocks (`requisites`, parties' bank details) are not
// subject to this limit and keep using `requisites`.
// Reject overwide text runs instead of silently painting outside the zone.
// Conservative: URLs and references must fit as tokens even if Typst could
// break them at punctuation. The original text is never clipped or rewritten.
#let checked-zone(width, body) = {
  show regex("[^ \\t\\r\\n]+"): it => context {
    assert(
      measure(it).width <= width,
      message: "Текст реквизита превышает ширину зоны; сократите токен или добавьте явный перенос (п. 3.5)",
    )
    it
  }
  block(width: width, above: 0pt, below: 0pt, body)
}

#let form-requisite(placement, label, ..lines, align: left) = {
  assert(
    placement in ("corner", "longitudinal"),
    message: "placement: допустимо «corner» или «longitudinal» (п. 3.5)",
  )
  let width = if placement == "corner" { corner-zone-width } else { longitudinal-zone-width }
  std.align(align, checked-zone(width, requisites(label, ..lines)))
}

// Two requisite blocks side by side, e.g. parties.
#let requisites-pair(left, right) = compact(grid(
  columns: (1fr, 1fr),
  column-gutter: 10mm,
  left, right,
))

// Signature fields (item 5.22). "horizontal": two persons of equal rank on one
// level. "vertical": persons of different rank one under the other, in the
// order given (the caller lists the more senior person first). Writing the
// name as "И.О. Фамилия" is the caller's responsibility; signature-field
// removes ordinary/NBSP spaces between the two initials only.
#let signatures(
  left: (position: [Исполнитель], name: none),
  right: (position: [Заказчик], name: none),
  layout: "horizontal",
) = {
  assert(
    layout in ("horizontal", "vertical"),
    message: "layout: допустимо «horizontal» или «vertical»",
  )
  let first = signature-field(left.name, left.position)
  let second = signature-field(right.name, right.position)
  if layout == "horizontal" {
    context {
      let cfg = get-config()
      set par(justify: false, first-line-indent: 0pt)
      // Shared rows: the tallest position sets the start of BOTH signatures.
      spaced(cfg.size, 1.0, block(breakable: false, grid(
        columns: (1fr, 1fr), column-gutter: 10mm,
        left.position, right.position,
        signature-field(left.name, none), signature-field(right.name, none),
      )))
    }
  } else {
    block(breakable: false, grid(columns: 1fr, row-gutter: 1em, first, second))
  }
}

// Stacked blanks for parties signing an appendix. Not a replacement for the
// full position/signature/name requisite provided by `signatures`.
// A shared grid prevents the body first-line indent from shifting one row.
#let signature-lines(
  labels: ([Исполнитель:], [Заказчик:]),
  line-length: 60mm,
  column-gutter: 3mm,
  row-gutter: 5mm,
  above: 10mm,
) = {
  set par(first-line-indent: 0pt, justify: false)
  v(above)
  layout(size => {
    let label-width = labels.map(label => measure(label).width).fold(0pt, calc.max)
    assert(
      label-width + column-gutter + line-length <= size.width,
      message: "signature-lines: подписи и линии не помещаются в доступную ширину; сократите подписи или длину линии",
    )
    block(breakable: false, grid(
      columns: (auto, line-length),
      column-gutter: column-gutter,
      row-gutter: row-gutter,
      align: left + bottom,
      ..labels.map(label => (label, line(length: line-length))).flatten(),
    ))
  })
}

// Header of a contract appendix (item 5.19): the word "Приложение", its number
// and the reference to the underlying document (kind, date, number) form a
// corner requisite at the upper right, lines aligned left, longest line at most
// 8 cm (item 3.5). The appendix title is a separate centred line. The reference
// is `to` as given, or built from `base-kind`, `base-date`, `base-number`, or a
// placeholder; actual values are the caller's responsibility.
#let contract-appendix-header(
  number,
  title,
  to: none,
  base-kind: none,
  base-date: none,
  base-number: none,
  new-page: true,
) = {
  if new-page { pagebreak(weak: true) }
  let reference = if to != none {
    to
  } else if base-kind != none or base-date != none or base-number != none {
    [к #(if base-kind != none { base-kind } else { [\[вид основного документа\]] }) от #(if base-date != none { base-date } else { [\[дата\]] }) № #(if base-number != none { base-number } else { [\[номер\]] })]
  } else {
    [к \[вид, дата и номер основного документа\]]
  }
  set par(first-line-indent: 0pt, justify: false)
  align(right, checked-zone(corner-zone-width, compact(align(left)[
    Приложение № #number\
    #reference
  ])))
  if title != none {
    v(0.75em)
    compact(align(center, strong(title)))
  }
}

// Table at reduced size with a repeating, bold header row.
#let data-table(columns, header, rows, align: auto) = table(
  columns: columns,
  align: align,
  table.header(..header.map(h => strong(h))),
  ..rows.flatten(),
)
