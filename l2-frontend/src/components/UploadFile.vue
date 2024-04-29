<template>
  <div>
    <RadioFieldById
      v-model="selectedType"
      :variants="currentFileTypes"
      @modified="changeType"
    />
    <Treeselect
      v-model="selectedForm"
      :options="currentFileForms"
    />
    <div>
      <input
        ref="file"
        style="margin-top: 15px"
        type="file"
        class="form-control-file"
        :accept="fileFilter"
        @change="handleFileUpload"
      >
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import RadioFieldById from '@/fields/RadioFieldById.vue';

import typesAndForms from './types-and-forms-file';

const { fileTypes, fileForms } = typesAndForms();

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
    for (const type of props.typesFile) {
      currentFileTypes.value.push(fileTypes.value[type]);
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

const handleFileUpload = () => {
  const inputValue = file.value as HTMLInputElement;
  const currentFiles = inputValue.files;
  console.log(currentFiles);
};

</script>

<style scoped lang="scss">

</style>
