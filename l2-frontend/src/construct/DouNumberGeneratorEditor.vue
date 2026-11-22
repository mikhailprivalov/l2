<template>
  <div class="root">
    <div class="top-editor">
      <div class="left">
        <div class="input-group">
          <div class="field-slot">
            <span class="input-group-addon">Название</span>
            <input
              v-model="title"
              type="text"
              class="form-control"
            >
          </div>
        </div>
      </div>
    </div>
    <div class="top-editor">
      <div class="left">
        <div class="input-group">
          <div class="field-slot field-slot--mask">
            <span class="input-group-addon">Старт</span>
            <input
              v-model="mask"
              type="text"
              class="form-control"
            >
          </div>
          <div class="field-slot field-slot--last">
            <span class="input-group-addon">Последний</span>
            <input
              :value="lastNumber"
              type="text"
              class="form-control"
              readonly
            >
          </div>
        </div>
      </div>
    </div>
    <div class="hint">
      {n} номер, {n:05} с нулями, {yyyy} {yy} {mm} {dd} дата. Пример: ВХ-{n:05}/{yyyy}
    </div>
    <div class="template-row">
      <span class="input-group-addon">Журнал куда отнести</span>
      <select
        v-model.number="journalId"
        class="form-control journal-select"
        :disabled="journalLocked"
      >
        <option :value="-1">
          Не выбран
        </option>
        <option
          v-for="journal in journals || []"
          :key="journal.id"
          :value="journal.id"
        >
          {{ journal.title }}
        </option>
      </select>
    </div>
    <div class="template-row">
      <div class="row-part">
        <span class="input-group-addon">Сбрасывать номер каждый год</span>
        <label class="plan-flag">
          <input
            v-model="resetEachYear"
            type="checkbox"
          >
        </label>
      </div>
    </div>
    <div
      v-if="itemId > 0 && !active"
      class="hint"
    >
      Неактивный. Новый генератор этого журнала заменил его.
    </div>
    <div class="footer-editor">
      <button
        class="btn btn-blue-nb"
        type="button"
        @click="$emit('cancel')"
      >
        Отмена
      </button>
      <button
        class="btn btn-blue-nb"
        type="button"
        :disabled="!title.trim() || !mask.trim()"
        @click="save"
      >
        Сохранить
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed, getCurrentInstance, onMounted, ref, watch,
} from 'vue';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';

const props = defineProps<{
  itemId: number;
  journals: { id: number; title: string }[];
}>();

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'saved', payload: { id: number }): void;
  (e: 'cancel'): void;
}>();

const store = useStore();
const root = getCurrentInstance().proxy.$root;
const title = ref('');
const mask = ref('');
const journalId = ref(-1);
const journalLocked = ref(false);
const resetEachYear = ref(true);
const active = ref(true);
const lastValue = ref(0);
const lastYear = ref(0);

const renderMask = (source: string, number: number, year: number) => {
  const now = new Date();
  const usedYear = year || now.getFullYear();
  const month = now.getMonth() + 1;
  const day = now.getDate();
  const token = /\{(n(?::(\d{1,2}))?|yyyy|yy|mm|dd)\}/g;
  return source.replace(token, (_match, kind: string, width?: string) => {
    if (String(kind).startsWith('n')) {
      const text = String(number);
      if (!width) {
        return text;
      }
      return text.padStart(Math.min(Number(width), 20), '0');
    }
    if (kind === 'yyyy') {
      return String(usedYear).padStart(4, '0');
    }
    if (kind === 'yy') {
      return String(usedYear % 100).padStart(2, '0');
    }
    if (kind === 'mm') {
      return String(month).padStart(2, '0');
    }
    return String(day).padStart(2, '0');
  });
};

const lastNumber = computed(() => {
  if (!lastValue.value) {
    return '';
  }
  return renderMask(mask.value || '', lastValue.value, lastYear.value);
});

const resetForm = () => {
  title.value = '';
  mask.value = '';
  journalId.value = -1;
  journalLocked.value = false;
  resetEachYear.value = true;
  active.value = true;
  lastValue.value = 0;
  lastYear.value = 0;
};

const loadDetails = async () => {
  if (props.itemId < 1) {
    resetForm();
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/number-generators/details', { id: props.itemId });
    if (!result?.ok) {
      root.$emit('msg', 'error', result?.message || 'Генератор не найден');
      return;
    }
    title.value = result.title || '';
    mask.value = result.mask || '';
    journalId.value = Number(result.journalId) > 0 ? Number(result.journalId) : -1;
    journalLocked.value = journalId.value > 0;
    resetEachYear.value = result.resetEachYear !== false;
    active.value = Boolean(result.active);
    lastValue.value = Number(result.last) || 0;
    lastYear.value = Number(result.year) || 0;
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const save = async () => {
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/number-generators/update', {
      id: props.itemId,
      title: title.value,
      mask: mask.value,
      journalId: journalId.value,
      resetEachYear: resetEachYear.value,
    });
    if (result?.ok) {
      if (journalId.value > 0) {
        journalLocked.value = true;
      }
      root.$emit('msg', 'ok', 'Сохранено');
      emit('saved', { id: result.id });
    } else {
      root.$emit('msg', 'error', result?.message || 'Ошибка сохранения');
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

watch(() => props.itemId, loadDetails);
onMounted(loadDetails);
</script>

<style scoped lang="scss">
.root {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  height: 100%;
  background-color: #f8f7f7;
}

.top-editor {
  display: flex;
  flex: 0 0 34px;
  align-self: stretch;
  width: 100%;
  min-width: 0;
  height: 34px;

  .left {
    flex: 1 1 auto;
    width: 100%;
    min-width: 0;
  }

  .input-group {
    display: flex !important;
    flex-wrap: nowrap;
    align-items: stretch;
    width: 100%;
    margin-bottom: 0;
    height: 34px;
  }

  .input-group-addon {
    display: flex !important;
    align-items: center;
    flex: 0 0 auto;
    float: none !important;
    width: auto;
    height: 34px;
    padding: 0 10px;
    line-height: 22px;
    font-size: 14px;
    font-weight: normal;
    color: #fff;
    white-space: nowrap;
    background-color: #aab2bd;
    border-top: none;
    border-left: none;
    border-right: none;
    border-bottom: 1px solid #96a0ad;
    border-radius: 0;
  }

  .form-control {
    flex: 1 1 0;
    float: none !important;
    width: auto !important;
    min-width: 0;
    height: 34px;
    padding: 0 10px;
    line-height: 22px;
    font-size: 14px;
    color: #434a54;
    border-top: none;
    border-left: 1px solid #96a0ad;
    border-right: 1px solid #96a0ad;
    border-bottom: 1px solid #96a0ad;
    border-radius: 0;
    display: block !important;
    box-shadow: none;
  }

  .field-slot {
    display: flex;
    flex: 1 1 0;
    min-width: 0;
    align-items: stretch;
  }

  .field-slot--mask {
    flex: 2 1 0;
  }

  .field-slot--last {
    flex: 1 1 0;
  }

  .field-slot:last-child .form-control {
    border-right: none;
  }

  .form-control[readonly] {
    background-color: #fff;
  }
}

.hint {
  padding: 6px 10px;
  color: #656d78;
  font-size: 12px;
  line-height: 16px;
}

.template-row {
  display: flex;
  align-items: stretch;
  height: 34px;

  .input-group-addon {
    display: flex;
    align-items: center;
    flex: 0 0 auto;
    flex-shrink: 0;
    width: auto !important;
    height: 34px;
    padding: 0 10px;
    line-height: 22px;
    font-size: 14px;
    font-weight: normal;
    color: #fff;
    white-space: nowrap;
    background-color: #aab2bd;
    border-top: none;
    border-left: none;
    border-right: none;
    border-bottom: 1px solid #96a0ad;
    border-radius: 0;
  }
}

.row-part {
  display: flex;
  align-items: stretch;
  flex: 0 0 auto;
  min-width: 0;
}

.plan-flag {
  display: flex;
  align-items: center;
  height: 34px;
  padding: 0 10px;
  background: #fff;
  border: 1px solid #ccc;
  border-left: 0;

  input {
    margin: 0;
  }
}

.journal-select {
  flex: 1 1 0;
  min-width: 0;
  height: 34px;
  padding: 0 10px;
  line-height: 22px;
  font-size: 14px;
  color: #434a54;
  background: #fff;
  border-top: none;
  border-left: 1px solid #96a0ad;
  border-right: none;
  border-bottom: 1px solid #96a0ad;
  border-radius: 0;
  box-shadow: none;
}

.footer-editor {
  flex: 0 0 34px;
  display: flex;
  justify-content: flex-end;
  align-self: stretch;
  margin-top: auto;
  background-color: #f4f4f4;
  border-top: 1px solid #b1b1b1;

  .btn {
    border-radius: 0 !important;
    height: 34px;
    padding: 0 10px;
    line-height: 22px;
    font-size: 14px;
  }
}
</style>
