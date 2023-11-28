import { StringDict } from '@/types/common';

const DEBUG = false;

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
    z: 'я',
    c: 'с',
    b: 'и',
    n: 'т',
    m: 'ь',
    '/': '.',
  };

  let hasReplaced = false;

  for (let i = 0; i < str.length; i++) {
    if (replacer[str[i].toLowerCase()]) {
      let replace;
      if (str[i] === str[i].toLowerCase()) {
        replace = replacer[str[i].toLowerCase()];
      } else if (str[i] === str[i].toUpperCase()) {
        replace = replacer[str[i].toLowerCase()].toUpperCase();
      }

      str = str.replace(str[i], replace);
      hasReplaced = true;
    }
  }

  if (hasReplaced) {
    const moreReplacers = {
      "'": 'э',
      '"': 'Э',
      ',': 'б',
      '<': 'Б',
      '.': 'ю',
      '>': 'Ю',
      i: 'ш',
      I: 'Ш',
      v: 'м',
      V: 'М',
      x: 'ч',
      X: 'Ч',
    };

    for (let i = 0; i < str.length; i++) {
      if (moreReplacers[str[i]]) {
        str = str.replace(str[i], moreReplacers[str[i]]);
      }
    }
  }

  return str;
};

interface Field {
  value: string | void;
}

const reDigitBrackets = /{(\d+)}/g;
const reBrackets = /[{}]/g;
const reFloat = /^\d+([,.]\d+)?$/;
const reOpen = /{/g;
const reClose = /}/g;
const reN = /\n/g;

const RE_CACHE = {};

const getRe = (re: string, m: any) => {
  const k = `${re}%%${m || null}`;
  if (!RE_CACHE[k]) {
    RE_CACHE[k] = new RegExp(re, m);
  }

  return RE_CACHE[k];
};

const BRACKETS_REPLACE_CACHE = {};

const replaceBrackets = (str: string) => {
  if (!BRACKETS_REPLACE_CACHE[str]) {
    BRACKETS_REPLACE_CACHE[str] = str.replace(reOpen, '\\{').replace(reClose, '\\}');
  }
  return BRACKETS_REPLACE_CACHE[str];
};

const BRACKETS_CLEAN_CACHE = {};

const cleanBrackets = (str: string) => {
  if (!BRACKETS_CLEAN_CACHE[str]) {
    BRACKETS_CLEAN_CACHE[str] = str.replace(reBrackets, '');
  }
  return BRACKETS_CLEAN_CACHE[str];
};

const cleanObject = (obj: any) => {
  for (const key of Object.keys(obj)) {
    // eslint-disable-next-line no-param-reassign
    delete obj[key];
  }
};

export const cleanCaches = () => {
  cleanObject(FUNCTION_CACHE);
  cleanObject(RE_CACHE);
  cleanObject(BRACKETS_REPLACE_CACHE);
  cleanObject(BRACKETS_CLEAN_CACHE);
};

export const PrepareFormula = (
  fields: Field[],
  formula: string,
  patient = {},
  strict = false,
  returnLinks = false,
): string | Link[] => {
  let s = formula;
  const necessary = s.match(reDigitBrackets);
  const links = [];

  if (necessary) {
    for (const n of necessary) {
      let v = null;
      const vid = cleanBrackets(n);
      const vFromField = fields[vid]?.value;
      if (DEBUG) {
        // eslint-disable-next-line no-console
        console.log('vFromField', vid, vFromField);
      }
      const vOrig = String(parseInt(vFromField || '', 10) === 0 ? 0 : vFromField || '').trim();
      if (DEBUG) {
        // eslint-disable-next-line no-console
        console.log('vOrig', vid, vOrig);
      }
      if (returnLinks) {
        if (!links.find((l) => l.id === vid)) {
          links.push(new Link(LINK_FIELD, vid));
        }
      } else {
        if (reFloat.test(vOrig) && !strict) {
          if (fields[vid]) {
            v = parseFloat(vOrig.trim().replace(',', '.'));
          }
          v = v || 0;
          v = Number.isFinite(v) ? v : 0;
        } else {
          v = vOrig;
        }
        const r = getRe(replaceBrackets(n), 'g');
        if (strict) {
          s = s.replace(r, `\`${v}\``);
        } else {
          s = s.replace(r, String(v === 0 ? 0 : v || ''));
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
      const r = getRe(`\\[_${prop}_\\]`, 'g');
      s = s.replace(r, patient[prop] || '');
    }
  }

  if (returnLinks) {
    return links;
  }

  s = s.replace(reN, '\\n');

  return `return /*strict=${strict}*/ (${s});`;
};

const isEmpty = (v) => !v;
const isFilled = (v) => !isEmpty(v);

export const CalculateFormula = (fields: Field[], formula: string, patient = {}, strict = false): string | number => {
  const s = PrepareFormula(fields, formula, patient, strict);
  if (DEBUG) {
    // eslint-disable-next-line no-console
    console.log(s);
  }

  if (Array.isArray(s)) {
    return '';
  }

  try {
    if (!FUNCTION_CACHE[s]) {
      // eslint-disable-next-line no-new-func
      const result = new Function('isEmpty', 'isFilled', s)(isEmpty, isFilled);
      FUNCTION_CACHE[s] = typeof result === 'boolean' || result ? result : 0;
    }
    return FUNCTION_CACHE[s];
  } catch (e) {
    FUNCTION_CACHE[s] = null;
    // eslint-disable-next-line no-console
    console.log(s);
    // eslint-disable-next-line no-console
    console.error(e);
    return '';
  }
};

export const CalculateVisibility = (f: Field[], rule: string, p = {}): boolean => Boolean(CalculateFormula(f, rule, p, true));

interface Error {
  code?: number;
  message?: string;
}

export const validateSnils = (
  snilsOrig: string | number,
  returnErrors?: boolean,
): boolean | { result: boolean; errors: Error } => {
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

export const replaceAll = (s: string, a: string, b: string) => s.replace(new RegExp(a, 'gm'), b);

const reName = /[^-а-яёА-ЯЁA-Z.’',() ]/g;
export const reSpaceDuplication = / +/g;

const NAME_REPLACERS = {
  "'": '’',
};

export const normalizeNamePart = (stringOrig: string): string => {
  let string = swapLayouts(stringOrig).replace(reSpaceDuplication, ' ');
  string = string.replace(reName, '');

  for (const nameReplacer of Object.keys(NAME_REPLACERS)) {
    string = replaceAll(string, nameReplacer, NAME_REPLACERS[nameReplacer]);
  }

  if (string.length > 0) {
    string = string[0].toUpperCase() + string.slice(1);
  }

  return string;
};

const keys = (values: StringDict) => Object.keys(values);
const v2s = (origStr: string, values: StringDict) => keys(values).reduce((s, k) => replaceAll(s, `{${k}}`, values[k]), origStr);

export const valuesToString = v2s;

export const getFormattedDate = (date: Date | void): string => {
  if (!date) {
    return '';
  }
  const year = date.getFullYear();
  let month = (1 + date.getMonth()).toString();
  month = month.length > 1 ? month : `0${month}`;
  let day = date.getDate().toString();
  day = day.length > 1 ? day : `0${day}`;
  return `${day}.${month}.${year}`;
};

export const convertSubjectNameToCertObject = (subjectName: string): any => {
  const result = {};
  const parts = subjectName.split(/([а-яa-z]+=|[а-яa-z]+\s[а-яa-z]+=)/iug);
  const p = parts.slice(1);
  for (let i = 0; i < p.length; i += 2) {
    const key = p[i].replace('=', '');
    const value = p[i + 1];
    result[key] = value.length > 2 ? value.slice(0, -2) : value;
  }

  return result;
};

export const convertSubjectNameToTitle = (object: any, subjectName: string | null) => {
  const obj = object || convertSubjectNameToCertObject(subjectName);

  // eslint-disable-next-line no-console
  console.log(obj);
  // eslint-disable-next-line no-console
  console.log(subjectName);
  return [obj.SN, obj.G, obj.SNILS, obj.T].filter(Boolean).join(' ');
};

export const subjectNameHasOGRN = (object: any, subjectName: string | null) => {
  const obj = object || convertSubjectNameToCertObject(subjectName);

  let ogrn = obj['ОГРН'] || null;

  if (!ogrn) {
    ogrn = Object.entries(obj).find(([, v]) => v === 'ОГРН')?.[0] || null;
  }

  return String(ogrn || '').length === 13;
};

export const validateEmail = (email: string) => Boolean(
  String(email || '')
    .toLowerCase()
    .match(
      // eslint-disable-next-line max-len
      /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/,
    ),
);

export const selectFile = (contentType: string | null): Promise<File> => new Promise((resolve) => {
  const input = document.createElement('input');
  input.type = 'file';
  input.multiple = false;
  if (contentType) {
    input.accept = contentType;
  }

  input.onchange = () => {
    const files = Array.from(input.files);
    resolve(files[0]);
  };

  input.click();
});

export const setLocalStorageDataJson = (name, value) => {
  window.localStorage.setItem(name, JSON.stringify(value));
};
