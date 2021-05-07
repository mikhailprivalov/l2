const FUNCTION_CACHE = {};

const patientProps = ['age', 'sex'];

export const LINK_FIELD = 'LINK_FIELD';
export const LINK_PATIENT = 'LINK_PATIENT';

export class Link {
  type: string;

  id: string;

  constructor(type: string, id: string) {
    this.type = type;
    this.id = id;
  }
}

export const swapLayouts = (origStr: string): string => {
  let str = origStr;
  const replacer = {
    q: 'й',
    w: 'ц',
    e: 'у',
    r: 'к',
    t: 'е',
    y: 'н',
    u: 'г',
    i: 'ш',
    o: 'щ',
    p: 'з',
    '[': 'х',
    ']': 'ъ',
    a: 'ф',
    s: 'ы',
    d: 'в',
    f: 'а',
    g: 'п',
    h: 'р',
    j: 'о',
    k: 'л',
    l: 'д',
    ';': 'ж',
    '\'': 'э',
    z: 'я',
    x: 'ч',
    c: 'с',
    v: 'м',
    b: 'и',
    n: 'т',
    m: 'ь',
    ',': 'б',
    '.': 'ю',
    '/': '.',
  };

  for (let i = 0; i < str.length; i++) {
    if (replacer[str[i].toLowerCase()]) {
      let replace;
      if (str[i] === str[i].toLowerCase()) {
        replace = replacer[str[i].toLowerCase()];
      } else if (str[i] === str[i].toUpperCase()) {
        replace = replacer[str[i].toLowerCase()].toUpperCase();
      }

      str = str.replace(str[i], replace);
    }
  }

  return str;
};

interface Field {
  value: string | void;
}

export const PrepareFormula = (
  fields: Field[], formula: string, patient = {}, strict = false, returnLinks = false,
): string | Link[] => {
  let s = formula;
  const necessary = s.match(/{(\d+)}/g);
  const links = [];

  if (necessary) {
    for (const n of necessary) {
      let v = null;
      const vid = n.replace(/[{}]/g, '');
      const vOrig = ((fields[vid] || {}).value || '').trim();
      if (returnLinks) {
        if (!links.find((l) => l.id === vid)) {
          links.push(new Link(LINK_FIELD, vid));
        }
      } else {
        if ((/^\d+([,.]\d+)?$/).test(vOrig) && !strict) {
          if (fields[vid]) {
            v = parseFloat(vOrig.trim().replace(',', '.'));
          }
          v = v || 0;
          v = Number.isFinite(v) ? v : 0;
        } else {
          v = vOrig;
        }
        const r = new RegExp(n.replace(/{/g, '\\{').replace(/}/g, '\\}'), 'g');
        if (strict) {
          s = s.replace(r, `\`${v}\``);
        } else {
          s = s.replace(r, v || '');
        }
      }
    }
  }

  for (const prop of patientProps) {
    if (returnLinks) {
      const propOrig = `[_${prop}_]`;
      if (s.includes(propOrig)) {
        links.push(new Link(LINK_PATIENT, prop));
      }
    } else {
      const r = new RegExp(`\\[_${prop}_\\]`, 'g');
      s = s.replace(r, patient[prop] || '');
    }
  }

  if (returnLinks) {
    return links;
  }

  s = s.replace(/\n/g, '\\n');

  return `return (${s});`;
};

export const CalculateFormula = (
  fields: Field[], formula: string, patient = {}, strict = false,
): string | number => {
  const s = PrepareFormula(fields, formula, patient, strict);

  if (Array.isArray(s)) {
    return '';
  }

  try {
    if (!FUNCTION_CACHE[s]) {
      // eslint-disable-next-line no-new-func
      const result = (new Function(s)());
      FUNCTION_CACHE[s] = (typeof result === 'boolean' || result) ? result : 0;
    }
    console.log(FUNCTION_CACHE);
    return FUNCTION_CACHE[s];
  } catch (e) {
    FUNCTION_CACHE[s] = null;
    console.log(s);
    console.error(e);
    return '';
  }
};

export const CalculateVisibility = (
  fields: Field[], rule: string, patient = {},
): boolean => Boolean(CalculateFormula(fields, rule, patient, true));

interface Error {code?: number, message?: string}

export const validateSnils = (
  snilsOrig: string | number, returnErrors: boolean,
) : boolean | {result: boolean, errors: Error} => {
  let result = false;
  let snils = snilsOrig;
  const errors: Error = {};

  if (typeof snils === 'number') {
    snils = snils.toString();
  } else if (typeof snils !== 'string') {
    snils = '';
  }
  snils = snils.replace(/-/g, '').replace(/ /g, '');
  if (!snils.length) {
    errors.code = 1;
    errors.message = 'СНИЛС пуст';
  } else if (/[^0-9]/.test(snils)) {
    errors.code = 2;
    errors.message = 'СНИЛС может состоять только из цифр';
  } else if (snils.length !== 11) {
    errors.code = 3;
    errors.message = 'СНИЛС может состоять только из 11 цифр';
  } else {
    let sum = 0;
    for (let i = 0; i < 9; i++) {
      sum += parseInt(snils[i], 10) * (9 - i);
    }
    let checkDigit = 0;
    if (sum < 100) {
      checkDigit = sum;
    } else if (sum > 101) {
      checkDigit = parseInt(String(sum % 101), 10);
      if (checkDigit === 100) {
        checkDigit = 0;
      }
    }
    if (checkDigit === parseInt(snils.slice(-2), 10)) {
      result = true;
    } else {
      errors.code = 4;
      errors.message = 'Неправильное контрольное число';
    }
  }
  if (returnErrors) {
    return {
      result,
      errors,
    };
  }
  return result;
};

export const normalizeNamePart = (stringOrig: string): string => {
  const string = swapLayouts(stringOrig).replace(/  +/g, ' ');
  const r = [];
  for (const s of string.split(' ')) {
    const v = [];

    for (const si of s.split('-')) {
      v.push(si.charAt(0).toUpperCase() + si.slice(1).toLowerCase());
    }

    r.push(v.join('-'));
  }
  return r.join(' ').trim();
};
