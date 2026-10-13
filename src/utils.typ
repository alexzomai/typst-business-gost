// Adapted from typst-gost/modern-g7-32 (GPL-3.0-only), upstream commit
// 6fe1cb2ef8f09b1947b241c58b47e7858598f3ce, file src/utils.typ.
// `fetch-field` and `unbreak-name` are reused unchanged. `small-text` and
// the signature field are modified (see NOTICE.md). Licensed under
// GPL-3.0-only, see ../LICENSE.

#import "constants.typ": *

// ---- reused unchanged from upstream ----
#let fetch-field(field, expected-keys, default: (:), hint: "") = {
  let expected-keys-arg-error = "Ожидаемые ключи должны быть списком строк, например '(arg1*, arg2), здесь arg1 - обязательный агрумент, а arg2 - необязательный'"

  assert(type(expected-keys) == array, message: expected-keys-arg-error)
  assert(
    expected-keys.map(elem => type(elem)).all(elem => elem == str),
    message: expected-keys-arg-error,
  )

  assert(
    type(default) == dictionary,
    message: "Стандартные значения должны быть определены в словаре, например: 'default: (arg1: false)'",
  )
  assert(
    default.len() <= expected-keys.len(),
    message: "Количество стандартных значений должно быть не больше числа ожидаемых аргументов",
  )

  let get-default(key) = (key, default.at(key, default: none))

  let clean-expected-keys = expected-keys.map(key => key.replace("*", ""))
  let required-keys = expected-keys
    .filter(key => key.at(-1) == "*")
    .map(key => key.slice(0, -1))
  let not-required-keys = expected-keys.filter(key => key.at(-1) != "*")

  if type(field) == type(none) {
    return clean-expected-keys.map(get-default).to-dict()
  }

  if type(field) == dictionary {
    for key in required-keys {
      assert(
        key in field.keys(),
        message: "В словаре "
          + hint
          + " отсутствует обязательный ключ '"
          + key
          + "'",
      )
    }
    for key in field.keys() {
      assert(
        key in clean-expected-keys,
        message: "В словаре "
          + hint
          + " обнаружен неожиданный ключ '"
          + key
          + "', допустимые ключи: "
          + repr(expected-keys),
      )
    }
    let result = clean-expected-keys.map(get-default).to-dict()
    for (key, value) in field {
      result.insert(key, value)
    }
    return result
  } else if type(field) == array {
    assert(
      field.len() >= required-keys.len(),
      message: "В списке "
        + hint
        + " указаны не все обязательные элементы: "
        + repr(required-keys),
    )
    assert(
      field.len() <= expected-keys.len(),
      message: "В списке "
        + hint
        + " указано слишком много аргументов, требуемые: "
        + repr(expected-keys),
    )
    let result = (:)
    for (i, key) in clean-expected-keys.enumerate() {
      result.insert(key, field.at(i, default: default.at(key, default: none)))
    }
    return result
  } else if type(field) in (str, int, length) {
    let result = clean-expected-keys.map(get-default).to-dict()
    result.insert(clean-expected-keys.at(0), field)
    return result
  } else {
    panic(
      "Некорректный тип поля "
        + repr(type(field))
        + "("
        + repr(field)
        + ") используйте словарь, список или строку для значения "
        + hint,
    )
  }
}

#let unbreak-name(name) = {
  if name == none { return }
  return name.replace(" ", "\u{00A0}")
}

// ---- modified from upstream ----

// Line box model. Typst places baselines at (top-edge + bottom-edge + leading)
// intervals. We fix leading to 0 and choose both edges so that the interval
// equals `size * factor`, independent of any Word-style line spacing model.
#let line-edges(size, factor) = {
  let pitch = size * factor
  let extra = pitch - size * (font-ascent + font-descent)
  let top = size * font-ascent + extra / 2
  (top-edge: top, bottom-edge: -(pitch - top))
}

#let spaced(size, factor, body) = {
  let e = line-edges(size, factor)
  set text(size: size, top-edge: e.top-edge, bottom-edge: e.bottom-edge)
  set par(leading: 0pt)
  body
}

#let get-config() = state(config-state-key, none).get()

// Reduced-size text (tables, requisites captions), single line spacing.
#let small-text = body => context {
  let cfg = get-config()
  spaced(cfg.small-size, 1.0, body)
}

// Block with single line spacing at body size (compact requisites).
#let compact = body => context {
  let cfg = get-config()
  set par(first-line-indent: 0pt, justify: false)
  block(width: 100%, above: 0pt, below: cfg.size * 0.75, spaced(cfg.size, 1.0, body))
}

// Signature field (item 5.22): position, then a rule with the caption and the
// name. The whole field is body text at single spacing and body size: item 3.3
// allows smaller type only for tables and requisites 08 and 25, so the caption
// is not reduced. Built on a grid, not a table, so that table styling does
// not apply to it.
#let signature-field(name, position, details: "подпись") = context {
  let cfg = get-config()
  // Item 5.22: no space between initials, but keep the surname separator.
  // Restrict this to two capital-letter initials; do not rewrite other names.
  let normalized-name = if name == none { none } else {
    name.replace(regex("(\\p{Lu}\\.)[ \u{00A0}]+(\\p{Lu}\\.)"), m => m.captures.at(0) + m.captures.at(1))
  }
  set par(justify: false, first-line-indent: 0pt)
  spaced(cfg.size, 1.0, block(breakable: false)[
    #position
    #v(0.8em)
    #grid(
      columns: (1fr, auto),
      column-gutter: 6pt,
      align: (center, left + bottom),
      grid(
        rows: (auto, auto),
        row-gutter: 2pt,
        box(width: 100%, height: 0.2em, stroke: (bottom: 0.5pt)),
        details,
      ),
      unbreak-name(normalized-name),
    )
  ])
}
