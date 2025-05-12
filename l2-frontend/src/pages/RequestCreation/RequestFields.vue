<template>
  <div class="request-fields-container">
    <div class="custom-form-container">
      <formulate-form
        v-model="formValues"
        :debounce="100"
        @input="onInput"
      >
        <div class="request-fields">
          <FormulateInput
            class="third-width"
            type="date"
            name="date"
            label="Дата исследования"
            placeholder="ДД.ММ.ГГГГ"
          />
          <FormulateInput
            class="third-width"
            type="number"
            name="dose"
            label="Эффективная доза"
            placeholder="мЗв"
          />
          <FormulateInput
            class="third-width"
            type="l2-radio"
            name="priority"
            label="‎ "
            :variants="[{ id: 'planned', label: 'Планово' }, { id: 'cito', label: 'Cito' }]"
          />
        </div>
        <div class="request-fields">
          <FormulateInput
            class="half-width"
            type="l2-radio"
            name="contrast"
            label="‎ "
            :variants="[{ id: 'without-contrast', label: 'Без контраста' }, { id: 'with-contrast', label: 'С контрастом' }]"
          />
          <FormulateInput
            class="half-width"
            type="number"
            name="contrastAmount"
            label="Введено контраста"
            placeholder="Объём, мг"
          />
        </div>
        <div class="request-fields">
          <FormulateInput
            class="full-width"
            type="text"
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
          <FormulateInput
            class="half-width"
            type="file"
            name="files"
            label="Файлы"
            :multiple="true"
            :validation="fileValidation"
            :uploader="uploadFile"
            add-label="Добавить файл"
          />
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
import { ref, watch } from 'vue';
import isEqual from 'lodash/isEqual';

const props = defineProps<{ value: Record<string, any> }>();

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'input', id: Record<string, any>): void
  (e: 'create:request'): void
}>();

const formValues = ref({ ...props.value });

// eslint-disable-next-line max-len
const fileValidation = 'mime:image/jpeg,image/png,image/gif,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';

async function uploadFile(file: File, progress: (n: number) => void, error: (msg: string) => void) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      progress(100);
      resolve({ url: (e.target?.result as string), name: file.name, type: file.type });
    };
    reader.onerror = () => {
      error('Ошибка чтения файла');
    };
    reader.readAsDataURL(file);
  });
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
});
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
        &[type="date"], &[type="number"], &[type="text"] {
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
</style>
