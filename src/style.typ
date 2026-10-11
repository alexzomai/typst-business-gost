// Adapted from typst-gost/modern-g7-32 (GPL-3.0-only), upstream commit
// 6fe1cb2ef8f09b1947b241c58b47e7858598f3ce, file src/style.typ.
// Modified: page numbering moved to a fixed top position; footer, outline,
// citation and figure rules removed; baseline-pitch line spacing.
// Licensed under GPL-3.0-only, see ../LICENSE.

#import "constants.typ": *
#import "utils.typ": line-edges, spaced

#let page-number-layer(margin, duplex) = context {
  let n = here().page()
  if n > 1 {
    place(
      top + left,
      dx: 0pt,
      dy: page-number-offset,
      box(
        width: page.width,
        align(center, text(top-edge: "cap-height", bottom-edge: "baseline", counter(page).display("1"))),
      ),
    )
  }
}

#let business-style(cfg, body) = {
  let m = cfg.margin
  set page(
    paper: cfg.paper,
    margin: if cfg.duplex {
      (inside: m.left, outside: m.right, top: m.top, bottom: m.bottom)
    } else {
      m
    },
    header: none,
    footer: none,
    background: page-number-layer(m, cfg.duplex),
  )

  set text(font: cfg.font, lang: "ru", hyphenate: false, overhang: false)
  show: it => spaced(cfg.size, cfg.line-spacing, it)

  set par(
    justify: cfg.justify,
    first-line-indent: (amount: cfg.indent, all: true),
    spacing: cfg.paragraph-spacing,
  )

  set list(marker: [–], indent: cfg.indent, spacing: default-list-spacing)
  set enum(indent: cfg.indent, spacing: default-list-spacing)

  set table(stroke: 0.5pt, inset: 4pt)
  show table: set par(first-line-indent: 0pt, justify: false)
  show table: it => spaced(cfg.small-size, 1.0, it)
  show table.cell: set align(left)
  show figure.caption: set align(left)

  set heading(numbering: cfg.heading-numbering)
  show heading: set text(size: cfg.size, weight: "bold")
  show heading: set par(first-line-indent: 0pt, justify: false)
  show heading: set block(above: cfg.size * cfg.line-spacing, below: cfg.size * cfg.line-spacing * 0.5, sticky: true)
  show heading: it => if cfg.heading-align == "center" {
    align(center, it)
  } else {
    pad(it, left: cfg.indent)
  }

  body
}
