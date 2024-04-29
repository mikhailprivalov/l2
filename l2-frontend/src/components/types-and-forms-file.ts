import { ref } from 'vue';

export default function typesAndForms() {
  const typesFile = ref(['333']);
  const formsFile = ref(['222']);
  return { typesFile, formsFile };
}
