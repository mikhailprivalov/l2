<template>
  <div class="card-no-hover card card-1">
    <h4 class="text-center">
      Штрих-коды ёмкостей
    </h4>
    <div class="fields">
      <label class="field">
        <span>Ширина штрих-кода, мм</span>
        <input
          v-model.number="widthMm"
          class="form-control"
          type="number"
          step="any"
        >
        <span class="hint">0 — формула по длине номера</span>
      </label>
      <label class="field">
        <span>Смещение по X, мм</span>
        <input
          v-model.number="offsetX"
          class="form-control"
          type="number"
          step="any"
        >
      </label>
      <button
        type="button"
        class="btn btn-blue-nb"
        :disabled="saving"
        @click="save"
      >
        Сохранить
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';

import api from '@/api';
import * as actions from '@/store/action-types';
import { useStore } from '@/store';
import useNotify from '@/hooks/useNotify';

const store = useStore();
const notify = useNotify();

const widthMm = ref<number>(0);
const offsetX = ref<number>(0);
const saving = ref(false);

const load = async () => {
  await store.dispatch(actions.INC_LOADING);
  const {
    ok, widthMm: width, offsetX: offset,
  } = await api('construct/tubes/get-barcode-settings');
  if (ok) {
    widthMm.value = width;
    offsetX.value = offset;
  }
  await store.dispatch(actions.DEC_LOADING);
};

const save = async () => {
  if (saving.value) {
    return;
  }
  saving.value = true;
  await store.dispatch(actions.INC_LOADING);
  const { ok, message } = await api('construct/tubes/save-barcode-settings', {
    widthMm: widthMm.value,
    offsetX: offsetX.value,
  });
  if (ok) {
    notify.ok('Изменения сохранены');
  } else {
    notify.error(message || 'Ошибка сохранения');
  }
  await store.dispatch(actions.DEC_LOADING);
  saving.value = false;
};

onMounted(load);
</script>

<style scoped>
.fields {
  max-width: 420px;
  margin: 0 auto;
  padding: 10px 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-weight: 600;
}

.hint {
  font-weight: 400;
  font-size: 12px;
  color: #666;
}

.btn {
  align-self: flex-start;
}
</style>
