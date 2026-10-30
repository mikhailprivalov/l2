<template>
  <div class="root">
    <div class="top-editor">
      <div class="input-group">
        <span class="input-group-addon">Группа</span>
        <input
          v-model="title"
          type="text"
          class="form-control"
          :disabled="loose"
          :placeholder="loose ? 'Без группы' : 'Название группы'"
        >
      </div>
    </div>
    <div class="content-editor">
      <div
        v-for="row in indicators"
        :key="row.clientKey"
        class="indicator-row"
      >
        <input
          v-model="row.title"
          type="text"
          class="form-control"
          placeholder="Название задачи"
        >
        <button
          class="btn btn-blue-nb"
          type="button"
          @click="removeIndicator(row)"
        >
          Удалить
        </button>
      </div>
      <button
        class="btn btn-blue-nb add-row"
        type="button"
        @click="addIndicator"
      >
        Добавить задачу
      </button>
      <div
        v-if="!loose && loosePool.length"
        class="loose-pool"
      >
        <div class="loose-pool__title">
          Без группы
        </div>
        <div
          v-for="row in loosePool"
          :key="row.id"
          class="indicator-row"
        >
          <span class="loose-pool__name">{{ row.title }}</span>
          <button
            class="btn btn-blue-nb"
            type="button"
            @click="takeLoose(row)"
          >
            В эту группу
          </button>
        </div>
      </div>
    </div>
    <div class="footer-editor">
      <button
        v-if="!loose && itemId > 0"
        class="btn btn-blue-nb"
        type="button"
        @click="removeGroup"
      >
        Удалить группу
      </button>
      <button
        class="btn btn-blue-nb"
        type="button"
        @click="emit('cancel')"
      >
        Отмена
      </button>
      <button
        class="btn btn-blue-nb"
        type="button"
        @click="save"
      >
        Сохранить
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  getCurrentInstance, ref, watch,
} from 'vue';

import api from '@/api';
import { useStore } from '@/store';
import * as actions from '@/store/action-types';

interface IndicatorRow {
  clientKey: number;
  id: number | null;
  title: string;
  fromLoose?: boolean;
}

interface LooseRow {
  id: number;
  title: string;
}

const props = defineProps<{
  itemId: number;
}>();

// eslint-disable-next-line no-spaced-func, func-call-spacing
const emit = defineEmits<{
  (e: 'saved', payload: { id: number }): void;
  (e: 'cancel'): void;
}>();

const store = useStore();
const root = getCurrentInstance().proxy.$root;
const title = ref('');
const loose = ref(false);
const indicators = ref<IndicatorRow[]>([]);
const loosePool = ref<LooseRow[]>([]);
let nextKey = 1;

const addIndicator = () => {
  nextKey += 1;
  indicators.value.push({ clientKey: nextKey, id: null, title: '' });
};

const removeIndicator = (row: IndicatorRow) => {
  indicators.value = indicators.value.filter(item => item.clientKey !== row.clientKey);
  if (row.fromLoose && row.id) {
    loosePool.value = [...loosePool.value, { id: row.id, title: row.title }];
  }
};

const takeLoose = (row: LooseRow) => {
  nextKey += 1;
  indicators.value.push({
    clientKey: nextKey,
    id: row.id,
    title: row.title,
    fromLoose: true,
  });
  loosePool.value = loosePool.value.filter(item => item.id !== row.id);
};

const loadLoosePool = async () => {
  const data = await api('document-manager/indicators/details', { id: 0 });
  if (!data?.ok) {
    return;
  }
  const taken = new Set(indicators.value.map(row => row.id).filter(id => id));
  loosePool.value = (data.indicators || [])
    .filter(row => row.id && !taken.has(row.id))
    .map(row => ({ id: row.id, title: row.title || '' }));
};

const applyData = (data) => {
  loose.value = Boolean(data.loose);
  title.value = loose.value ? 'Без группы' : (data.title || '');
  indicators.value = (data.indicators || []).map(row => {
    nextKey += 1;
    return { clientKey: nextKey, id: row.id || null, title: row.title || '' };
  });
};

const load = async () => {
  loosePool.value = [];
  await store.dispatch(actions.INC_LOADING);
  try {
    if (props.itemId === -1) {
      applyData({ loose: false, title: '', indicators: [] });
    } else {
      const data = await api('document-manager/indicators/details', { id: props.itemId });
      if (!data?.ok) {
        root.$emit('msg', 'error', data?.message || 'Группа не найдена');
        return;
      }
      applyData(data);
    }
    if (!loose.value) {
      await loadLoosePool();
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const save = async () => {
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/indicators/update', {
      id: props.itemId,
      title: loose.value ? '' : title.value,
      indicators: indicators.value.map(row => ({ id: row.id, title: row.title })),
    });
    if (result?.ok) {
      root.$emit('msg', 'ok', 'Сохранено');
      emit('saved', { id: result.id });
    } else {
      root.$emit('msg', 'error', result?.message || 'Ошибка сохранения');
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const removeGroup = async () => {
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/indicators/delete', { id: props.itemId });
    if (result?.ok) {
      root.$emit('msg', 'ok', 'Удалено');
      emit('cancel');
    } else {
      root.$emit('msg', 'error', result?.message || 'Не удалось удалить группу');
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

watch(() => props.itemId, () => {
  load();
}, { immediate: true });
</script>

<style scoped lang="scss">
.root {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f8f7f7;
}

.top-editor .input-group {
  display: flex;
  margin-bottom: 0;
  height: 34px;
}

.input-group-addon {
  display: flex;
  align-items: center;
  width: auto;
  height: 34px;
  padding: 0 10px;
  color: #fff;
  background: #aab2bd;
  border: 0;
  border-bottom: 1px solid #96a0ad;
  border-radius: 0;
}

.form-control {
  height: 34px;
  border-radius: 0;
  box-shadow: none;
}

.content-editor {
  flex: 1;
  padding: 8px;
  overflow: auto;
}

.indicator-row {
  display: flex;
  gap: 6px;
  margin-bottom: 6px;
}

.add-row {
  margin-top: 4px;
}

.loose-pool {
  margin-top: 16px;
  padding-top: 8px;
  border-top: 1px solid #ddd;
}

.loose-pool__title {
  margin-bottom: 6px;
  color: #666;
  font-size: 12px;
}

.loose-pool__name {
  flex: 1;
  min-width: 0;
  line-height: 34px;
}

.footer-editor {
  display: flex;
  justify-content: flex-end;
  background: #f4f4f4;
  border-top: 1px solid #b1b1b1;

  .btn {
    height: 34px;
    border-radius: 0;
  }
}
</style>
