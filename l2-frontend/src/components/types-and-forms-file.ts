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
      'api.laboratory.forms100.form_01': { id: 'api.laboratory.forms100.form_01', label: 'Загрузка PDF результата из QMS' },
    },
  });
  // todo - UploadResult + forms - получать только выбранные isResult функции (протестировать)
  const getForms = (type: string, forms: string[] = null, onlyResult = false, allowedForms: string[] = null): formsFile[] => {
    /* onlyResult - Выдаст только формы находящиеся в isResultForm, allowedForms - выдаст только те функции которые разрешены */
    const result: formsFile[] = [];
    console.log(allowedForms);
    if (!allowedForms) {
      return result;
    }
    if (forms && forms.length > 0) {
      for (const form of forms) {
        if (!onlyResult && fileForms.value[type][form] && allowedForms.includes(form)) {
          result.push(fileForms.value[type][form]);
        } else if (onlyResult && isResultForm.value.includes(form) && allowedForms.includes(form)) {
          result.push(fileForms.value[type][form]);
        }
      }
    } else if (!forms && onlyResult) {
      for (const form of isResultForm.value) {
        if (fileForms.value[type][form] && allowedForms.includes(form)) {
          result.push(fileForms.value[type][form]);
        }
      }
    } else {
      const tmpResult = Object.values(fileForms.value[type]);
      for (const form of tmpResult) {
        if (allowedForms.includes(String(form))) {
          result.push(fileForms.value[type][form]);
        }
      }
    }
    return result;
  };
  return { getTypes, getForms };
}
