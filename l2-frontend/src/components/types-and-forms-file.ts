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

  const isResult = ref([
    'api.laboratory.forms100.form_01',
  ]);

  /* (101.01) - 101 номер файла, 01 - номер функции в файле для обработки загруженного файла (см. parseFile) */
  const fileForms = ref({
    XLSX: {
      'api.contracts.forms100.form_01': { id: 'api.contracts.forms100.form_01', label: 'Загрузка цен по прайсу' },
    },
    PDF: {
      'api.laboratory.forms100.form_01': { id: 'api.laboratory.forms100.form_01', label: 'Загрузка PDF результата' },
    },
  });
  // todo - режим UploadResult - получать по расширению файла - только функции связанные с сохранением результата (анализаторы)
  // todo - UploadResult + forms - получать только выбранные isResult функции
  const getForms = (type: string, forms: string[] = [], onlyResult = false): formsFile[] => {
    let result: formsFile[] = [];
    if (forms && forms.length > 0) {
      for (const form of forms) {
        if (!onlyResult && fileForms.value[type][form]) {
          result.push(fileForms.value[type][form]);
        } else if (onlyResult && isResult.value.includes(form)) {
          result.push(fileForms.value[type][form]);
        }
      }
    } else {
      result = Object.values(fileForms.value[type]);
    }
    return result;
  };
  return { getTypes, getForms };
}
