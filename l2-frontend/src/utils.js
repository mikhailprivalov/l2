export const CalculateVisibility = (fields, rule, patient = {}) => {
  return Boolean(CalculateFormula(fields, rule, patient, true))
};


export const CalculateFormula = (fields, formula, patient = {}, strict = false) => {
  let s = PrepareFormula(fields, formula, patient, strict);
  try {
    return (new Function(s)()) || 0
  } catch (e) {
    console.log(s);
    console.error(e);
    return ''
  }
};

const patientProps = ['age', 'sex'];

export const PrepareFormula = (fields, formula, patient = {}, strict = false) => {
  let s = formula;
  let necessary = s.match(/{(\d+)}/g);

  if (necessary) {
    for (const n of necessary) {
      let v = null;
      let vOrig = ((fields[n.replace(/[{}]/g, '')] || {}).value || '').trim();
      if ((/^\d+([,.]\d+)?$/).test(vOrig) && !strict) {
        if (fields[n.replace(/[{}]/g, '')]) {
          v = parseFloat(vOrig.trim().replace(',', '.'))
        }
        v = v || 0;
        v = isFinite(v) ? v : 0
      } else {
        v = vOrig
      }
      const r = new RegExp(n.replace(/{/g, '\\{').replace(/}/g, '\\}'), 'g');
      if (strict) {
        s = s.replace(r, `\`${v}\``)
      } else {
        s = s.replace(r, v || '')
      }
    }
  }

  for (const prop of patientProps) {
    const r = new RegExp(`\\[_${prop}_\\]`, 'g');
    s = s.replace(r, patient[prop] || '')
  }

  s = s.replace(/\n/g, '\\n');

  return `return (${s});`
};
