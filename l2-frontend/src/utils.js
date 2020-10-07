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

export const LINK_FIELD = 'LINK_FIELD';
export const LINK_PATIENT = 'LINK_PATIENT';

export class Link {
  constructor(type, id) {
    this.type = type
    this.id = id
  }
}

export const PrepareFormula = (fields, formula, patient = {}, strict = false, returnLinks = false) => {
  let s = formula;
  let necessary = s.match(/{(\d+)}/g);
  const links = [];

  if (necessary) {
    for (const n of necessary) {
      let v = null;
      const vid = n.replace(/[{}]/g, '');
      let vOrig = ((fields[vid] || {}).value || '').trim();
      if (returnLinks) {
        if (!links.find(l => l.id === vid)) {
          links.push(new Link(LINK_FIELD, vid))
        }
        continue
      }
      if ((/^\d+([,.]\d+)?$/).test(vOrig) && !strict) {
        if (fields[vid]) {
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
    if (returnLinks) {
      const propOrig = `[_${prop}_]`;
      if (s.includes(propOrig)) {
        links.push(new Link(LINK_PATIENT, prop));
      }
      continue;
    }
    const r = new RegExp(`\\[_${prop}_\\]`, 'g');
    s = s.replace(r, patient[prop] || '')
  }

  if (returnLinks) {
    return links;
  }

  s = s.replace(/\n/g, '\\n');

  return `return (${s});`
};
