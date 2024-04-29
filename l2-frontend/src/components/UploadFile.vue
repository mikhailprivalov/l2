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
        ref="file"
        style="margin-top: 15px"
        type="file"
        class="form-control-file"
        :accept="fileFilter"
        @change="handleFileUpload"
      >
      <div v-if="fileIsSelected">
        <button class="btn btn-blue-nb">
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

const file = ref(null);
const fileIsSelected = ref(false);

const handleFileUpload = () => {
  const input = file.value as HTMLInputElement;
  const re = /(?:\.([^.]+))?$/;
  const fileExtension = re.exec(input.value)[1];
  console.log(fileExtension);
  if (fileExtension.toLowerCase() !== String(selectedType.value).toLowerCase()) {
    input.value = '';
    fileIsSelected.value = false;
    root.$emit('msg', 'error', `Файл не ${selectedType.value}`);
  } else {
    fileIsSelected.value = true;
  }
};

</script>

<style scoped lang="scss">

</style>
