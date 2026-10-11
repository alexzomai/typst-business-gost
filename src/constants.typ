// Adapted from typst-gost/modern-g7-32 (GPL-3.0-only), upstream commit
// 6fe1cb2ef8f09b1947b241c58b47e7858598f3ce, file src/constants.typ.
// Modified: academic defaults removed, leading replaced by baseline-pitch
// model, added normative limits and settings for business documents.
// Licensed under GPL-3.0-only, see ../LICENSE.

#let default-font = "Liberation Serif"
#let default-text-size = (default: 14pt, small: 10pt)
#let default-indent = 1.25cm
#let default-margin = (left: 30mm, right: 15mm, top: 20mm, bottom: 20mm)
#let default-justify = true
#let default-line-spacing = 1.5
#let default-paragraph-spacing = 0pt
#let default-list-spacing = 0pt

// Minimal margins, mm. A long retention period raises the left minimum.
#let min-margin = (left: 20, right: 10, top: 20, bottom: 20)
#let min-margin-long-retention-left = 30

// Page number box top edge, distance from the top edge of the sheet.
#let page-number-offset = 10mm

// Allowed range of line spacing factor for narrative text.
#let min-line-spacing = 1.0
#let max-line-spacing = 1.5

// Maximum number of heading levels (item 5.18).
#let max-heading-levels = 4

// Longest line of a requisite by placement (item 3.5).
#let corner-zone-width = 8cm
#let longitudinal-zone-width = 12cm

// Recommended body sizes (pt) and a technical floor for reduced text.
#let recommended-text-sizes = (12, 13, 14)
#let min-small-text-size = 8

// Approximate font metrics (em) used only to place half-leading.
#let font-ascent = 0.89
#let font-descent = 0.22

#let config-state-key = "business-g7-97-config"
