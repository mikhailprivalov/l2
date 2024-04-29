<template>
  <div>
    <RadioFieldById
      v-model="selectedType"
      :variants="currentFileTypes"
      @modified="changeType"
    />
    <Treeselect
      v-if="selectedType"
      v-model="selectedForm"
      :options="currentFileForms"
    />
    <div v-if="selectedForm">
      <input
        ref="fileInput"
        style="margin-top: 15px"
        type="file"
        class="form-control-file"
        :readonly="loading"
        :accept="fileFilter"
        @change="handleFileUpload"
      >
      <div v-if="fileIsSelected">
        <button
          class="btn btn-blue-nb"
          :disabled="loading"
          @click="submitFileUpload()"
        >
          Загрузить файл
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { getCurrentInstance, onMounted, ref } from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import RadioFieldById from '@/fields/RadioFieldById.vue';
import api from '@/api';

import typesAndForms from './types-and-forms-file';

const { fileTypes, fileForms } = typesAndForms();

const root = getCurrentInstance().proxy.$root;
const props = defineProps({
  typesFile: {
    type: Array,
    required: false,
  },
  formsFile: {
    type: Array,
    required: false,
  },
  uploadResult: {
    type: Boolean,
    required: false,
  },
});

const fileFilter = ref('');
const loading = ref(false);

const currentFileTypes = ref([]);
const selectedType = ref(null);

const appendCurrentTypes = () => {
  currentFileTypes.value = [];
  if (props.typesFile) {
    for (const typeFile of props.typesFile) {
      currentFileTypes.value.push(fileTypes.value[typeFile]);
    }
  } else {
    currentFileTypes.value = Object.values(fileTypes.value);
  }
};

onMounted(() => {
  appendCurrentTypes();
});

const currentFileForms = ref([]);
const selectedForm = ref(null);
const appendCurrentForms = () => {
  currentFileForms.value = [];
  if (props.formsFile) {
    for (const form of props.formsFile) {
      currentFileForms.value.push(fileForms.value[selectedType.value][form]);
    }
  } else {
    currentFileForms.value = Object.values(fileForms.value[selectedType.value]);
  }
};

const changeType = () => {
  fileFilter.value = `.${selectedType.value}`;
  selectedForm.value = null;
  appendCurrentForms();
};

const fileInput = ref(null);
const file = ref(null);
const fileIsSelected = ref(false);

const handleFileUpload = () => {
  const input = fileInput.value as HTMLInputElement;
  const re = /(?:\.([^.]+))?$/;
  const fileExtension = re.exec(input.value)[1];
  if (fileExtension.toLowerCase() !== String(selectedType.value).toLowerCase()) {
    input.value = '';
    fileIsSelected.value = false;
    root.$emit('msg', 'error', `Файл не ${selectedType.value}`);
  } else {
    [file.value] = input.files;
    fileIsSelected.value = true;
  }
};

const submitFileUpload = async () => {
  loading.value = true;
  try {
    const formData = new FormData();
    formData.append('file', file.value);
    formData.append('selectedForm', selectedForm.value);
    const { data } = await api('parse-file/upload-file', null, null, null, formData);
    console.log(data);
  } catch (e) {
    // eslint-disable-next-line no-console
    console.error(e);
    root.$emit('msg', 'error', 'Ошибка загрузки');
  }
  loading.value = false;
};
</script>

<style scoped lang="scss">

</style>
