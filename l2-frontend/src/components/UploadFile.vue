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
import {
  getCurrentInstance, onMounted, PropType, ref,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import RadioFieldById from '@/fields/RadioFieldById.vue';
import api from '@/api';

import typesAndForms, { formsFile, typesFile } from './types-and-forms-file';

const { getTypes, getForms } = typesAndForms();

const root = getCurrentInstance().proxy.$root;
const props = defineProps({
  typesFile: {
    type: Array as PropType<string[]>,
    required: false,
  },
  formsFile: {
    type: Array as PropType<string[]>,
    required: false,
  },
  uploadResult: {
    type: Boolean,
    required: false,
  },
  entityId: {
    type: Number,
    required: false,
  },
  otherNeedData: {
    type: Object || Array || String || Number,
    required: false,
  },
});

const fileFilter = ref('');
const loading = ref(false);

const currentFileTypes = ref<typesFile[]>([]);
const selectedType = ref(null);

onMounted(() => {
  currentFileTypes.value = getTypes(props.typesFile);
});

const currentFileForms = ref<formsFile[]>([]);
const selectedForm = ref(null);

const changeType = () => {
  fileFilter.value = `.${selectedType.value}`;
  currentFileForms.value = getForms(String(selectedType.value), props.formsFile);
  if (currentFileForms.value.length > 0) {
    selectedForm.value = currentFileForms.value[0].id;
  }
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
