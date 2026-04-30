<template>
  <div class="request-fields-container">
    <div class="custom-form-container">
      <formulate-form
        v-model="formValues"
        :debounce="100"
        @input="onInput"
      >
        <div class="request-fields">
          <div class="half-width">
            <label class="formulate-input-label date-time-label">Дата и время исследования</label>
            <div class="date-time-fields">
              <FormulateInput
                type="date"
                name="date"
                placeholder="ДД.ММ.ГГГГ"
              />
              <FormulateInput
                type="time"
                name="time"
                placeholder="ЧЧ:ММ"
              />
            </div>
          </div>
          <div class="half-width">
            <FormulateInput
              type="number"
              name="dose"
              label="Доза"
              placeholder="мЗв"
            />
          </div>
          <div
            class="half-width"
            style="padding-top: 25px; display: flex; gap: 20px;"
          >
            <FormulateInput
              type="checkbox"
              name="cito"
              label="Cito"
            />
            <FormulateInput
              type="checkbox"
              name="isDynamic"
              label="Динамика"
            />
          </div>
        </div>
        <div class="request-fields">
          <div class="half-width">
            <label class="formulate-input-label date-time-label">Контраст</label>
            <treeselect
              v-model="formValues.currentContrast"
              :multiple="false"
              :options="contrastOptions"
              placeholder="Выберите контраст"
              @input="onInput"
            />
          </div>
          <FormulateInput
            class="half-width"
            type="number"
            name="contrastAmount"
            placeholder="Объём, мг"
            label="Объём"
          />
        </div>

        <div class="request-fields">
          <FormulateInput
            class="full-width"
            type="textarea"
            name="anamnesis"
            label="Краткий анамнез"
            placeholder="Анамнез"
          />
        </div>
        <div class="request-fields">
          <FormulateInput
            class="half-width"
            type="textarea"
            name="comment"
            label="Комментарий"
            placeholder="Комментарий"
          />
          <div class="half-width">
            <label class="formulate-input-label">Файл</label>
            <div class="file-upload-container">
              <input
                ref="fileInput"
                type="file"
                style="display: none"
                @change="handleFileChange"
              >
              <div
                v-if="!selectedFile"
                class="file-drop-zone"
                @click="openFileDialog"
                @dragover.prevent
                @drop.prevent="handleFileDrop"
              >
                <div class="file-drop-content">
                  <i class="fa fa-cloud-upload" />
                  <span>Добавить файл (до 10 МБ)</span>
                </div>
              </div>
              <div
                v-else
                class="selected-file"
              >
                <div class="file-info">
                  <div class="file-icon">
                    <i class="fa fa-file" />
                  </div>
                  <div class="file-details">
                    <div class="file-name">
                      {{ selectedFile.name }}
                    </div>
                    <div class="file-size">
                      {{ formatFileSize(selectedFile.size) }}
                    </div>
                  </div>
                </div>
                <div class="file-actions">
                  <button
                    type="button"
                    class="btn-change"
                    title="Заменить файл"
                    @click="openFileDialog"
                  >
                    <i class="fa fa-refresh" />
                  </button>
                  <button
                    type="button"
                    class="btn-remove"
                    title="Удалить файл"
                    @click="removeFile"
                  >
                    <i class="fa fa-times" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </formulate-form>
    </div>
    <div class="bottom-buttons">
      <button
        class="btn btn-blue-nb top-inner-select"
        @click.prevent="createRequest"
      >
        Создать заявку
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import isEqual from 'lodash/isEqual';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import useNotify from '@/hooks/useNotify';
import researchesPoint from '@/api/researches-point';

const props = defineProps<{ value: Record<string, any> }>();

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'input', id: Record<string, any>): void
  (e: 'create:request'): void
}>();

const formValues = ref({ ...props.value, currentContrast: props.value.currentContrast || null });
const selectedFile = ref<File | null>(null);
const fileInput = ref<HTMLInputElement>();
const notify = useNotify();

const contrastOptions = ref([]);

async function getContrastsCollect() {
  const response = await researchesPoint.getContrastCollect();
  contrastOptions.value = response.data;
}

onMounted(() => {
  getContrastsCollect();
  if (!props.value.currentContrast) {
    formValues.value.currentContrast = -1;
  }
});

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Б';
  const k = 1024;
  const sizes = ['Б', 'КБ', 'МБ', 'ГБ'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${Math.round((bytes / (k ** i)) * 100) / 100} ${sizes[i]}`;
}

function convertFileToBase64(file: File): Promise<{ url: string; name: string; type: string }> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      resolve({
        url: e.target?.result as string,
        name: file.name,
        type: file.type,
      });
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

async function updateFormFiles() {
  if (selectedFile.value) {
    const fileData = await convertFileToBase64(selectedFile.value);
    formValues.value.files = [fileData];
  } else {
    formValues.value.files = [];
  }
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];

  if (!file) {
    selectedFile.value = null;
    updateFormFiles();
    return;
  }

  const maxSize = 10 * 1024 * 1024;

  if (file.size > maxSize) {
    notify.error('Размер файла больше 10 МБ');
    selectedFile.value = null;
    updateFormFiles();
    return;
  }

  selectedFile.value = file;
  updateFormFiles();
  input.value = '';
}

function handleFileDrop(event: DragEvent) {
  const file = event.dataTransfer?.files?.[0];

  if (!file) {
    return;
  }

  const maxSize = 10 * 1024 * 1024;

  if (file.size > maxSize) {
    notify.error(`Размер файла "${file.name}" превышает установленный лимит в 10 МБ.`);
    selectedFile.value = null;
    updateFormFiles();
    return;
  }

  selectedFile.value = file;
  updateFormFiles();
}

function removeFile() {
  selectedFile.value = null;
  updateFormFiles();
}

function openFileDialog() {
  fileInput.value?.click();
}

function createRequest() {
  emit('create:request');
}

function onInput() {
  emit('input', formValues.value);
}

watch(() => props.value, (val) => {
  if (!isEqual(val, formValues.value)) {
    formValues.value = { ...val };
  }

  if (!val.files || val.files.length === 0) {
    selectedFile.value = null;
  }
}, { deep: true });
</script>

<style lang="scss" scoped>
.custom-form-container {
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 8px;
  width: 100%;
  margin-top: 8px;
  position: absolute;
  top: 0;
  left: 0;
  bottom: 34px;
  right: 0;
  overflow-y: auto;
}
.request-fields-container {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  right: 0;
}
.request-fields {
  display: flex;
  gap: 12px;
  margin-bottom: 6px;
  flex-wrap: nowrap;
}

.half-width {
  flex: 1 1 0;
  min-width: 0;
}
.third-width {
  flex: 1 1 0;
  min-width: 0;
  max-width: 33%;
}
.full-width {
  flex: 0 0 100%;
  max-width: 100%;
}

.cito-checkbox {
  display: flex;
  max-width: 76px;
}

.file-upload-container {
  margin-top: 5px;
}

.file-drop-zone {
  border: 2px dashed #ccc;
  border-radius: 6px;
  padding: 12px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.3s ease;
  background-color: #f8f9fa;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 50px;
  color: #666;
  font-size: 14px;
  margin-top: 5px;
}

.file-drop-zone:hover {
  border-color: #6c757d;
  background-color: #e9ecef;
}

.file-drop-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-drop-content i {
  font-size: 18px;
  color: #6c757d;
}

.selected-file {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  margin-top: 5px;
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-icon {
  font-size: 24px;
  color: #049372;
}

.file-details {
  display: flex;
  flex-direction: column;
}

.file-name {
  font-weight: 600;
  color: #333;
}

.file-size {
  font-size: 14px;
  color: #666;
}

.file-actions {
  display: flex;
  gap: 5px;
}

.btn-change {
  background: none;
  border: none;
  color: #049372;
  font-size: 18px;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-change:hover {
  color: #037a5a;
}

.btn-remove {
  background: none;
  border: none;
  color: #dc3545;
  font-size: 18px;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-remove:hover {
  color: #c82333;
}

.formulate-input-label {
  display: block;
  margin-bottom: 5px;
  font-weight: 600;
  font-size: 14px;
  color: #374151;
}

::v-deep .formulate-input .formulate-input-element {
  max-width: 1000px;
  margin-bottom: 0;
}

.full-width ::v-deep .formulate-input .formulate-input-element {
  max-width: 100%;
}

::v-deep .formulate-input-wrapper {
  padding-bottom: 0;
}

::v-deep .formulate-input-element {
    input {
        &[type="date"], &[type="number"], &[type="text"], &[type="time"], &[type="datetime-local"] {
            min-height: 0;
            height: 34px;
        }
    }

    select {
        height: 34px;
    }
}

::v-deep [data-type="radio"] .formulate-input-wrapper {
    &, .formulate-input-group {
        display: flex;
        gap: 12px;
    }
}

.bottom-buttons {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  align-content: center;
  align-items: stretch;
  height: 34px;
  background-color: #aab2bd;
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2;
}

.date-time-fields {
  display: flex;
  gap: 6px;
}

.width-treeselect {
  display: flex;
  width: 100px;
}

.date-time-label {
  line-height: 1.5;
  font-size: 0.9em;
  font-weight: 600;
  margin-bottom: 0.1em;
}
</style>
