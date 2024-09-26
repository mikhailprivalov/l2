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
  });
  const fileFilters = {
    XLSX: '.xlx, .xls, .xlsx, ws-excel',
  };
  const getFileFilters = (types) => fileFilters[types.toUpperCase()];
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

  const isResultForm = ref([]);

  /* (101.01) - 101 номер файла, 01 - номер функции в файле для обработки загруженного файла (см. parseFile) */
  const fileForms = ref({
    XLSX: {
      100.01: { id: '100.01', label: 'Загрузка цен по прайсу' },
      100.02: { id: '100.02', label: 'Загрузка посещений' },
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
  const unsupportedFileForms = (type: string, forms: string[]) => {
    const result = forms.filter(form => form === fileForms.value[type][form]);
    return result.length === 0;
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
  return {
    getTypes, getForms, getFileFilters, unsupportedFileForms,
  };
}
