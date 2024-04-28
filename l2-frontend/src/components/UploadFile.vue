<template>
  <div>
    <RadioFieldById
      v-model="selectedType"
      :variants="fileTypes"
      @modified="changeType"
    />
    <Treeselect
      v-model="selectedForm"
      :options="fileForms"
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

const fileFilter = ref('');

const fileTypes = ref([
  { id: 1, label: 'XLSX' },
  { id: 2, label: 'PDF' },
  { id: 3, label: 'CSV' },
]);
const selectedType = ref(-1);

const selectedTypeLabel = computed(() => fileTypes.value.find((type) => type.id === selectedType.value).label);

const changeType = () => {
  fileFilter.value = `.${selectedTypeLabel.value}`;
};

const fileForms = ref([
  { id: 1, label: 'Загрузка цен по прайсу' },
]);
const selectedForm = ref(-1);

const file = ref(null);

const handleFileUpload = () => {
  const inputValue = file.value as HTMLInputElement;
  const currentFiles = inputValue.files;
  console.log(currentFiles);
  file.value = null;
};

</script>

<style scoped lang="scss">

</style>
