// Original code for this adaptation; argument normalisation is delegated to
// `fetch-field` reused from typst-gost/modern-g7-32 (GPL-3.0-only).
// Licensed under GPL-3.0-only, see ../LICENSE.

#import "constants.typ": *
#import "utils.typ": fetch-field

#let to-mm(value, name) = {
  assert(type(value) == length, message: name + ": ожидается длина, например 20mm")
  assert(value.em == 0, message: name + ": допустимы только абсолютные единицы (mm, cm, pt)")
  value.abs.mm()
}

#let validate-margin(margin, long-retention) = {
  if type(margin) == length {
    margin = (left: margin, right: margin, top: margin, bottom: margin)
  }
  let m = fetch-field(margin, ("left*", "right*", "top*", "bottom*"), hint: "margin")
  let left-min = if long-retention {
    min-margin-long-retention-left
  } else {
    min-margin.left
  }
  let checks = (
    (key: "left", min: left-min),
    (key: "right", min: min-margin.right),
    (key: "top", min: min-margin.top),
    (key: "bottom", min: min-margin.bottom),
  )
  for c in checks {
    let mm = to-mm(m.at(c.key), "margin." + c.key)
    assert(
      mm >= c.min - 0.001,
      message: "Поле «" + c.key + "» " + str(calc.round(mm, digits: 2)) + " мм меньше минимума " + str(c.min) + " мм"
        + if c.key == "left" and long-retention { " (срок хранения более 10 лет)" } else { "" },
    )
  }
  m
}

#let validate-text-size(text-size, strict) = {
  let sizes = fetch-field(text-size, ("default*", "small"), default: (small: default-text-size.small))
  let body = to-mm(sizes.default, "text-size.default") / 25.4 * 72
  let small = to-mm(sizes.small, "text-size.small") / 25.4 * 72
  if strict {
    assert(
      recommended-text-sizes.any(s => calc.abs(body - s) < 0.01),
      message: "Размер основного шрифта " + str(calc.round(body, digits: 2)) + " пт вне рекомендованных 12, 13, 14 пт. Для иного размера укажите strict-font-size: false",
    )
  } else {
    assert(body >= 8, message: "Размер основного шрифта меньше 8 пт")
  }
  assert(
    small < body,
    message: "Уменьшенный шрифт (" + str(calc.round(small, digits: 2)) + " пт) должен быть меньше основного (" + str(calc.round(body, digits: 2)) + " пт)",
  )
  assert(
    small >= min-small-text-size - 0.01,
    message: "Уменьшенный шрифт меньше " + str(min-small-text-size) + " пт (ограничение шаблона, не требование стандарта)",
  )
  (default: sizes.default, small: sizes.small)
}

#let validate-line-spacing(factor) = {
  assert(
    type(factor) in (int, float),
    message: "line-spacing: ожидается число от 1 до 1,5",
  )
  assert(
    factor >= min-line-spacing and factor <= max-line-spacing,
    message: "Межстрочный интервал " + str(factor) + " вне диапазона " + str(min-line-spacing) + " до " + str(max-line-spacing),
  )
  factor
}

#let validate-indent(indent) = {
  let mm = to-mm(indent, "indent")
  assert(
    calc.abs(mm - 12.5) < 0.01,
    message: "Абзацный отступ должен быть 1,25 см, получено " + str(calc.round(mm / 10, digits: 2)) + " см",
  )
  indent
}

#let validate-paper(paper) = {
  assert(paper == "a4", message: "Шаблон рассчитан на формат A4, получено «" + repr(paper) + "»")
  paper
}
