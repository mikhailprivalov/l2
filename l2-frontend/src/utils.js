export const CalculateVisibility = (fields, rule) => {
  return Boolean(CalculateFormula(fields, rule, true))
}


export const CalculateFormula = (fields, formula, strict = false) => {
  let s = PrepareFormula(fields, formula, strict)

  try {
    return (new Function(s)()) || 0
  } catch (e) {
    return ''
  }
}

export const PrepareFormula = (fields, formula, strict = false) => {
  let s = formula
  let necessary = s.match(/{(\d+)}/g)

  if (necessary) {
    for (const n of necessary) {
      let v = null
      let vOrig = ((fields[n.replace(/[{}]/g, '')] || {}).value || '').trim()
      if ((/^\d+([,.]\d+)?$/).test(vOrig) && !strict) {
        if (fields[n.replace(/[{}]/g, '')]) {
          v = parseFloat(vOrig.trim().replace(',', '.'))
        }
        v = v || 0
        v = isFinite(v) ? v : 0
      } else {
        v = vOrig
      }
      const r = new RegExp(n.replace(/{/g, '\\{').replace(/}/g, '\\}'), 'g')
      if (strict) {
        s = s.replace(r, `\`${v}\``)
      } else {
        s = s.replace(r, v || '')
      }
    }
  }
  return `return (${s});`
}
