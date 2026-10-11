// Adapted from typst-gost/modern-g7-32 (GPL-3.0-only), upstream commit
// 6fe1cb2ef8f09b1947b241c58b47e7858598f3ce, file src/lib.typ.
// Modified: the upstream academic entry point is replaced by a business
// document entry point with validated configuration.
// Licensed under GPL-3.0-only, see ../LICENSE.

#import "constants.typ": *
#import "utils.typ": fetch-field
#import "validate.typ": *
#import "style.typ": business-style

#let business-doc(
  paper: "a4",
  font: default-font,
  text-size: default-text-size,
  indent: default-indent,
  margin: default-margin,
  line-spacing: default-line-spacing,
  paragraph-spacing: default-paragraph-spacing,
  justify: default-justify,
  duplex: false,
  long-retention: false,
  strict-font-size: true,
  heading-numbering: "1.",
  heading-align: "indent",
  title: none,
  author: none,
  body,
) = {
  let sizes = validate-text-size(text-size, strict-font-size)
  assert(
    heading-align in ("indent", "center"),
    message: "heading-align: допустимо «indent» или «center»",
  )
  let cfg = (
    paper: validate-paper(paper),
    font: font,
    size: sizes.default,
    small-size: sizes.small,
    indent: validate-indent(indent),
    margin: validate-margin(margin, long-retention),
    line-spacing: validate-line-spacing(line-spacing),
    paragraph-spacing: paragraph-spacing,
    justify: justify,
    duplex: duplex,
    heading-numbering: heading-numbering,
    heading-align: heading-align,
  )
  set document(title: title, author: author) if title != none and author != none
  set document(title: title) if title != none and author == none
  set document(author: author) if title == none and author != none
  state(config-state-key).update(cfg)
  show: business-style.with(cfg)
  body
}
