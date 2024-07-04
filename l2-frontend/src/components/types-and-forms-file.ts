import { ref } from 'vue';

export interface typesFile {
  id: string,
  label: string,
}
export interface formsFile {
  id: string,
  label: string,
}
export default function typesAndForms() {
  const fileTypes = ref({
    XLSX: { id: 'XLSX', label: 'XLSX' },
    PDF: { id: 'PDF', label: 'PDF' },
  });
  // todo - сделать соотношение - расширение файла - и все виды accept фильтров {xlsx: '.xlx, .xlsx, ws-excel'}
  const getTypes = (types: string[]): typesFile[] => {
    let result: typesFile[] = [];
    if (types && types.length > 0) {
      for (const type of types) {
        if (fileTypes.value[type.toUpperCase()]) {
          result.push(fileTypes.value[type]);
        }
      }
    } else {
      result = Object.values(fileTypes.value);
    }
    return result;
  };

  const isResultForm = ref([
    'api.laboratory.forms100.form_01',
  ]);

  /* (101.01) - 101 номер файла, 01 - номер функции в файле для обработки загруженного файла (см. parseFile) */
  const fileForms = ref({
    XLSX: {
      'api.contracts.forms100.form_01': { id: 'api.contracts.forms100.form_01', label: 'Загрузка цен по прайсу' },
    },
    PDF: {
      'api.laboratory.forms100.form_01': {
        id: 'api.laboratory.forms100.form_01',
        label: 'Прикрепление результата к исследованию',
      },
    },
  });
  const addForms = (type: string, forms = null, allowedForms: string[] = null) => {
    const result: formsFile[] = [];
    for (const form of forms) {
      if (allowedForms.includes(form) && fileForms.value[type][form]) {
        result.push(fileForms.value[type][form]);
      }
    }
    return result;
  };

  const getForms = (type: string, forms: string[] = null, onlyResult = false, allowedForms: string[] = null): formsFile[] => {
    let result: formsFile[] = [];
    if (!allowedForms) {
      return [];
    }
    if (forms) {
      result = addForms(type, forms, allowedForms);
    } else if (onlyResult) {
      result = addForms(type, isResultForm.value, allowedForms);
    } else {
      const tmp: formsFile[] = Object.values(fileForms.value[type]);
      const tmpResult = tmp.map(obj => obj.id);
      result = addForms(type, tmpResult, allowedForms);
    }
    return result;
  };
  return { getTypes, getForms };
}
