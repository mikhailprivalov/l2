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
import { computed, ref } from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import RadioFieldById from '@/fields/RadioFieldById.vue';

import typesAndForms from './types-and-forms-file';

const { fileTypes, fileForms } = typesAndForms();

const fileFilter = ref('');

const currentFileTypes = ref([]);
const selectedType = ref(null);

const changeType = () => {
  fileFilter.value = `.${selectedType.value}`;
};

const currentFileForms = ref([]);
const selectedForm = ref(null);

const file = ref(null);

const handleFileUpload = () => {
  const inputValue = file.value as HTMLInputElement;
  const currentFiles = inputValue.files;
  console.log(currentFiles);
};

</script>

<style scoped lang="scss">

</style>
