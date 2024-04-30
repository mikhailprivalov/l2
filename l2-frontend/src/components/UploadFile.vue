<template>
  <div>
    <div class="margin-first-item">
      <RadioFieldById
        v-if="currentFileTypes.length > 0"
        v-model="selectedType"
        :variants="currentFileTypes"
        @modified="changeType"
      />
      <h5
        v-else
        class="text-center"
      >
        Такие расширения файлов не поддерживаются
      </h5>
    </div>
    <div
      v-if="selectedType"
      class="margin-item"
    >
      <Treeselect
        v-if="currentFileForms.length > 0"
        v-model="selectedForm"
        :options="currentFileForms"
        placeholder="Выберите структуру файла"
      />
      <h5
        v-else
        class="text-center"
      >
        Такие структуры файла не поддерживаются
      </h5>
    </div>
    <div
      v-if="selectedForm"
      class="margin-item"
    >
      <input
        ref="fileInput"
        style="margin-top: 15px"
        type="file"
        class="form-control-file"
        :accept="fileFilter"
        @change="handleFileUpload"
      >
    </div>
    <div
      v-if="fileIsSelected"
      class="margin-item"
    >
      <button
        class="btn btn-blue-nb"
        @click="submitFileUpload()"
      >
        Загрузить файл
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
// todo - simpleMode - режим без модалки (без выбора)
import {
  getCurrentInstance, onMounted, PropType, ref,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import RadioFieldById from '@/fields/RadioFieldById.vue';
import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';

import typesAndForms, { formsFile, typesFile } from './types-and-forms-file';

const { getTypes, getForms } = typesAndForms();

const store = useStore();
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
  try {
    const formData = new FormData();
    formData.append('file', file.value);
    formData.append('selectedForm', selectedForm.value);
    formData.append('entityId', props.entityId ? props.entityId : null);
    formData.append('otherNeedData', props.otherNeedData ? props.otherNeedData : null);
    await store.dispatch(actions.INC_LOADING);
    const { data } = await api('parse-file/upload-file', null, null, null, formData);
    await store.dispatch(actions.DEC_LOADING);
    console.log(data);
  } catch (e) {
    // eslint-disable-next-line no-console
    console.error(e);
    root.$emit('msg', 'error', 'Ошибка загрузки');
  }
};
</script>

<style scoped lang="scss">
.margin-first-item {
  margin-bottom: 10px
}
.margin-item {
  margin: 10px 0;
}
</style>
