import { ref } from 'vue';

export default function typesAndForms() {
  const fileTypes = ref({
    XLSX: { id: 'XLSX', label: 'XLSX' },
    PDF: { id: 'PDF', label: 'PDF' },
    CSV: { id: 'CSV', label: 'CSV' },
  });
  /* (101.01) - 101 номер файла, 01 - номер функции в файле для обработки загруженного файла (см. parseFile) */
  const fileForms = ref({
    XLSX: {
      101.01: { id: 101.01, label: '101.01' },
      101.02: { id: 101.02, label: '101.02' },
      101.03: { id: 101.03, label: '101.03' },
    },
    PDF: {
      101.04: { id: 101.04, label: '101.04' },
    },
    CSV: {
      101.05: { id: 101.05, label: '101.05' },
    },
  });
  return { fileTypes, fileForms };
}
