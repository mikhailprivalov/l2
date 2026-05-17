<template>
  <div
    ref="dropZoneRef"
    class="file-result-field"
    :class="{
      'file-result-field--active': isActive,
      'file-result-field--disabled': disabled,
      'file-result-field--invalid': persistentErrors.length > 0,
    }"
    tabindex="0"
    @click="focusField"
    @paste="handlePaste"
    @dragenter.prevent="handleDragEnter"
    @dragover.prevent="handleDragOver"
    @dragleave.prevent="handleDragLeave"
    @drop.prevent="handleDrop"
  >
    <input
      ref="fileInputRef"
      class="file-result-field__input"
      type="file"
      multiple
      :disabled="disabled"
      @change="handleInputChange"
    >

    <div class="file-result-field__header">
      <div>
        <div class="file-result-field__title">
          Файлы
        </div>
        <div class="file-result-field__hint">
          Перетащите файлы сюда, вставьте через Ctrl/⌘ + V или выберите вручную
        </div>
        <div
          v-if="settingsHint"
          class="file-result-field__settings-hint"
        >
          {{ settingsHint }}
        </div>
      </div>

      <button
        type="button"
        class="file-result-field__button"
        :disabled="disabled || isMaxReached"
        :title="isMaxReached ? `Достигнут лимит файлов (${settings.maxFiles})` : undefined"
        @click.stop="openFileDialog"
      >
        Выбрать файлы
      </button>
    </div>

    <div
      v-if="isActive"
      class="file-result-field__drop-hint"
    >
      Отпустите файлы для добавления
    </div>

    <div
      v-if="addErrors.length"
      class="file-result-field__errors"
    >
      <div
        v-for="(err, i) in addErrors"
        :key="i"
        class="file-result-field__error"
      >
        {{ err }}
      </div>
    </div>

    <div
      v-if="persistentErrors.length"
      class="file-result-field__errors"
    >
      <div
        v-for="(err, i) in persistentErrors"
        :key="i"
        class="file-result-field__error"
      >
        {{ err }}
      </div>
    </div>

    <div
      v-if="files.length"
      class="file-result-field__list"
    >
      <div
        v-for="file in files"
        :key="getFileKey(file)"
        class="file-result-field__item"
      >
        <div class="file-result-field__icon">
          {{ getExtensionLabel(file) }}
        </div>

        <div class="file-result-field__info">
          <a
            v-if="!file.isNew && file.url"
            class="file-result-field__name"
            :href="file.url"
            target="_blank"
            rel="noopener noreferrer"
            @click.stop
          >
            {{ file.originalName }}
          </a>

          <div
            v-else
            class="file-result-field__name"
          >
            {{ file.originalName }}
          </div>

          <div class="file-result-field__meta">
            <span>{{ formatFileSize(file.size) }}</span>
            <span v-if="file.mimeType">• {{ file.mimeType }}</span>
            <span v-if="file.isNew">• новый файл</span>
          </div>
        </div>

        <button
          type="button"
          class="file-result-field__remove"
          :disabled="disabled"
          title="Удалить файл"
          @click.stop="removeFile(file)"
        >
          ×
        </button>
      </div>
    </div>

    <div
      v-else
      class="file-result-field__empty"
    >
      Файлы пока не добавлены
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';

import type { FileFieldSettings } from '@/types/Descriptive/Fields/FileField';
import { FileFieldValue, FileFieldValueFile, NewFileFieldValueFile } from '@/forms/types/FileResultField';

const props = defineProps<{
  value: FileFieldValue | null
  settings: FileFieldSettings | null
  disabled?: boolean
}>();

const emit = defineEmits<{(e: 'input', value: FileFieldValue): void
}>();

const fileInputRef = ref<HTMLInputElement | null>(null);
const dropZoneRef = ref<HTMLElement | null>(null);
const dragDepth = ref(0);
const addErrors = ref<string[]>([]);

const files = computed<FileFieldValue>({
  get() {
    return props.value || [];
  },
  set(value) {
    emit('input', value);
  },
});

const isActive = computed(() => dragDepth.value > 0 && !props.disabled);

const isMaxReached = computed(() => {
  const max = props.settings?.maxFiles;
  return max != null && files.value.length >= max;
});

function formatFileSize(size: number): string {
  if (!size) {
    return '0 Б';
  }

  const units = ['Б', 'КБ', 'МБ', 'ГБ'];
  const index = Math.min(Math.floor(Math.log(size) / Math.log(1024)), units.length - 1);
  const value = size / (1024 ** index);

  return `${value.toFixed(value >= 10 || index === 0 ? 0 : 1)} ${units[index]}`;
}

const settingsHint = computed(() => {
  const s = props.settings;
  if (!s) return '';

  const parts: string[] = [];

  if (s.minFiles != null && s.maxFiles != null && s.minFiles === s.maxFiles) {
    parts.push(`ровно ${s.minFiles} файл(ов)`);
  } else {
    if (s.minFiles != null) parts.push(`не менее ${s.minFiles} файл(ов)`);
    if (s.maxFiles != null) parts.push(`не более ${s.maxFiles} файл(ов)`);
  }

  if (s.allowedExtensions?.length) {
    parts.push(`допустимые форматы: ${s.allowedExtensions.join(', ').toUpperCase()}`);
  }

  if (s.maxFileSizeMb != null) {
    parts.push(`макс. размер файла: ${s.maxFileSizeMb} МБ`);
  }

  if (s.maxTotalSizeMb != null) {
    parts.push(`макс. суммарный размер: ${s.maxTotalSizeMb} МБ`);
  }

  if (s.filenamePatternDescription) {
    parts.push(`имя файла: ${s.filenamePatternDescription}`);
  }

  return parts.join(' • ');
});

const persistentErrors = computed(() => {
  const s = props.settings;
  if (!s) return [];

  const errs: string[] = [];
  const current = files.value;

  if (s.maxTotalSizeMb != null) {
    const totalBytes = current.reduce((sum, f) => sum + (f.size || 0), 0);
    const limitBytes = s.maxTotalSizeMb * 1024 * 1024;
    if (totalBytes > limitBytes) {
      errs.push(`Суммарный размер файлов (${formatFileSize(totalBytes)}) превышает допустимый (${s.maxTotalSizeMb} МБ)`);
    }
  }

  return errs;
});

function getFileExtension(filename: string): string {
  const parts = filename.split('.');

  if (parts.length < 2) {
    return '';
  }

  return parts[parts.length - 1].toLowerCase();
}

function createTempId(): string {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function getFileKey(file: FileFieldValueFile): string {
  if ('pk' in file) {
    return `existing-${file.pk}`;
  }

  return `new-${file.tempId}`;
}

function getExtensionLabel(file: FileFieldValueFile): string {
  const extension = file.extension || getFileExtension(file.originalName);

  return extension ? extension.slice(0, 5).toUpperCase() : 'FILE';
}

function validateFile(file: File): string | null {
  const s = props.settings;
  if (!s) return null;

  const ext = getFileExtension(file.name);

  if (s.allowedExtensions?.length) {
    const allowed = s.allowedExtensions.map(e => e.toLowerCase());
    if (!allowed.includes(ext)) {
      const formatted = s.allowedExtensions.join(', ').toUpperCase();
      return `«${file.name}» — недопустимый формат. Разрешены: ${formatted}`;
    }
  }

  if (s.maxFileSizeMb != null) {
    const limitBytes = s.maxFileSizeMb * 1024 * 1024;
    if (file.size > limitBytes) {
      return `«${file.name}» — файл слишком большой (${formatFileSize(file.size)}, лимит ${s.maxFileSizeMb} МБ)`;
    }
  }

  if (s.filenamePattern) {
    try {
      const re = new RegExp(s.filenamePattern);
      if (!re.test(file.name)) {
        const desc = s.filenamePatternDescription || s.filenamePattern;
        return `«${file.name}» — имя файла не соответствует требованиям: ${desc}`;
      }
    } catch {
      // Невалидный regex в настройках — пропускаем проверку
    }
  }

  return null;
}

function addFiles(rawFiles: File[]) {
  if (!rawFiles.length) {
    return;
  }

  addErrors.value = [];

  const s = props.settings;
  const errors: string[] = [];
  const accepted: NewFileFieldValueFile[] = [];
  const currentCount = files.value.length;
  const maxFiles = s?.maxFiles ?? null;

  for (const file of rawFiles) {
    if (maxFiles != null && currentCount + accepted.length >= maxFiles) {
      errors.push(`Достигнут лимит файлов (${maxFiles}). «${file.name}» не добавлен`);
      continue;
    }

    const err = validateFile(file);
    if (err) {
      errors.push(err);
      continue;
    }

    accepted.push({
      tempId: createTempId(),
      originalName: file.name,
      extension: getFileExtension(file.name),
      mimeType: file.type || '',
      size: file.size,
      file,
      isNew: true,
    });
  }

  if (accepted.length) {
    files.value = [...files.value, ...accepted];
  }

  addErrors.value = errors;
}

function focusField() {
  dropZoneRef.value?.focus();
}

function openFileDialog() {
  if (props.disabled) {
    return;
  }

  fileInputRef.value?.click();
}

function handleInputChange(event: Event) {
  const input = event.target as HTMLInputElement;

  if (!input.files) {
    return;
  }

  addFiles(Array.from(input.files));
  input.value = '';
}

function handleDragEnter() {
  if (props.disabled) {
    return;
  }

  dragDepth.value += 1;
}

function handleDragOver() {
  if (props.disabled) {
    return;
  }

  dragDepth.value = Math.max(dragDepth.value, 1);
}

function handleDragLeave() {
  if (props.disabled) {
    return;
  }

  dragDepth.value = Math.max(dragDepth.value - 1, 0);
}

function handleDrop(event: DragEvent) {
  if (props.disabled) {
    return;
  }

  dragDepth.value = 0;

  const droppedFiles = Array.from(event.dataTransfer?.files || []);
  addFiles(droppedFiles);
}

function handlePaste(event: ClipboardEvent) {
  if (props.disabled) {
    return;
  }

  const pastedFiles = Array.from(event.clipboardData?.files || []);

  if (!pastedFiles.length) {
    return;
  }

  event.preventDefault();
  addFiles(pastedFiles);
}

function removeFile(fileToRemove: FileFieldValueFile) {
  addErrors.value = [];
  files.value = files.value.filter(file => getFileKey(file) !== getFileKey(fileToRemove));
}
</script>

<style scoped lang="scss">
.file-result-field {
  width: 100%;
  min-height: 120px;
  padding: 12px;
  border: 1px dashed #b8c2cc;
  border-radius: 8px;
  background: #fafafa;
  outline: none;
  transition: border-color 0.15s ease, background-color 0.15s ease, box-shadow 0.15s ease;

  &:focus {
    border-color: #6b9bd2;
    box-shadow: 0 0 0 2px rgba(107, 155, 210, 0.2);
  }
}

.file-result-field--active {
  border-color: #4f8fd8;
  background: #f1f7ff;
}

.file-result-field--disabled {
  opacity: 0.75;
  background: #f3f3f3;
  cursor: not-allowed;
}

.file-result-field--invalid {
  border-color: #d9534f;
}

.file-result-field__input {
  display: none;
}

.file-result-field__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.file-result-field__title {
  font-weight: 600;
  font-size: 14px;
  color: #222;
}

.file-result-field__hint {
  margin-top: 3px;
  font-size: 12px;
  color: #777;
}

.file-result-field__settings-hint {
  margin-top: 4px;
  font-size: 11px;
  color: #5a7fa8;
}

.file-result-field__button {
  flex: 0 0 auto;
  padding: 6px 10px;
  border: 1px solid #9fb3c8;
  border-radius: 6px;
  background: #fff;
  color: #234;
  font-size: 13px;
  cursor: pointer;

  &:hover:not(:disabled) {
    background: #f3f8ff;
  }

  &:disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }
}

.file-result-field__errors {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-result-field__error {
  padding: 6px 10px;
  border-radius: 5px;
  background: #fff2f2;
  border: 1px solid #f5c6cb;
  color: #842029;
  font-size: 12px;
  line-height: 1.4;
}

.file-result-field__drop-hint {
  margin-top: 10px;
  padding: 10px;
  border-radius: 6px;
  background: #e8f2ff;
  color: #24527f;
  text-align: center;
  font-size: 13px;
}

.file-result-field__list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.file-result-field__item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border: 1px solid #e2e6ea;
  border-radius: 6px;
  background: #fff;
}

.file-result-field__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 46px;
  height: 34px;
  border-radius: 5px;
  background: #eef2f6;
  color: #34495e;
  font-size: 10px;
  font-weight: 700;
}

.file-result-field__info {
  min-width: 0;
  flex: 1 1 auto;
}

.file-result-field__name {
  display: block;
  overflow: hidden;
  color: #222;
  font-size: 13px;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-decoration: none;
}

a.file-result-field__name:hover {
  text-decoration: underline;
}

.file-result-field__meta {
  margin-top: 2px;
  color: #777;
  font-size: 12px;
}

.file-result-field__remove {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border: 1px solid #e2b5b5;
  border-radius: 50%;
  background: #fff;
  color: #a33;
  font-size: 20px;
  line-height: 1;
  cursor: pointer;

  &:hover:not(:disabled) {
    background: #fff2f2;
  }

  &:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }
}

.file-result-field__empty {
  margin-top: 12px;
  padding: 12px;
  border-radius: 6px;
  background: #fff;
  color: #888;
  font-size: 13px;
  text-align: center;
}
</style>
