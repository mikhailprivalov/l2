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
    <div class="content-editor">
      <div
        v-for="group in orderedGroups"
        :key="group.clientKey"
        class="ed-group"
      >
        <div class="input-group">
          <span class="input-group-addon">Группа</span>
          <input
            v-model="group.title"
            type="text"
            class="form-control"
            placeholder="Название группы"
          >
          <span class="input-group-btn">
            <button
              class="btn btn-blue-nb"
              type="button"
              @click="removeGroup(group)"
            >
              Удалить
            </button>
          </span>
        </div>
        <div
          v-for="row in orderedIndicators(group.indicators)"
          :key="row.clientKey"
          class="indicator-row"
        >
          <Treeselect
            v-model="row.indicatorId"
            class="treeselect-wide treeselect-34px indicator-select"
            :multiple="false"
            :clearable="true"
            :append-to-body="true"
            :options="indicatorOptions"
            placeholder="Показатель"
          />
          <select
            v-model="row.dueKind"
            class="form-control due-kind"
          >
            <option value="absolute">
              Дата
            </option>
            <option value="employment">
              От даты приема на работу
            </option>
          </select>
          <input
            v-if="row.dueKind === 'absolute'"
            v-model="row.dueDate"
            type="date"
            class="form-control due-date"
          >
          <div
            v-else
            class="offset"
          >
            <input
              v-model.number="row.offsetValue"
              type="number"
              step="1"
              class="form-control offset-value"
            >
            <select
              v-model="row.offsetUnit"
              class="form-control offset-unit"
            >
              <option value="days">
                дни
              </option>
              <option value="months">
                месяцы
              </option>
              <option value="years">
                годы
              </option>
            </select>
          </div>
          <button
            class="btn btn-blue-nb"
            type="button"
            @click="removeIndicator(group.indicators, row)"
          >
            Удалить
          </button>
        </div>
        <button
          class="btn btn-blue-nb add-row"
          type="button"
          @click="addIndicator(group.indicators)"
        >
          Добавить показатель
        </button>
      </div>
      <div class="ed-group">
        <div class="section-title">
          Без группы
        </div>
        <div
          v-for="row in orderedIndicators(looseIndicators)"
          :key="row.clientKey"
          class="indicator-row"
        >
          <Treeselect
            v-model="row.indicatorId"
            class="treeselect-wide treeselect-34px indicator-select"
            :multiple="false"
            :clearable="true"
            :append-to-body="true"
            :options="indicatorOptions"
            placeholder="Показатель"
          />
          <select
            v-model="row.dueKind"
            class="form-control due-kind"
          >
            <option value="absolute">
              Дата
            </option>
            <option value="employment">
              От даты приема на работу
            </option>
          </select>
          <input
            v-if="row.dueKind === 'absolute'"
            v-model="row.dueDate"
            type="date"
            class="form-control due-date"
          >
          <div
            v-else
            class="offset"
          >
            <input
              v-model.number="row.offsetValue"
              type="number"
              step="1"
              class="form-control offset-value"
            >
            <select
              v-model="row.offsetUnit"
              class="form-control offset-unit"
            >
              <option value="days">
                дни
              </option>
              <option value="months">
                месяцы
              </option>
              <option value="years">
                годы
              </option>
            </select>
          </div>
          <button
            class="btn btn-blue-nb"
            type="button"
            @click="removeIndicator(looseIndicators, row)"
          >
            Удалить
          </button>
        </div>
        <button
          class="btn btn-blue-nb add-row"
          type="button"
          @click="addIndicator(looseIndicators)"
        >
          Добавить показатель
        </button>
      </div>
      <button
        class="btn btn-blue-nb add-row"
        type="button"
        @click="addGroup"
      >
        Добавить группу
      </button>
    </div>
    <div class="footer-editor">
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
  computed, getCurrentInstance, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import api from '@/api';
import { useStore } from '@/store';
import * as actions from '@/store/action-types';

interface IndicatorOption {
  id: number;
  label: string;
}

interface PlanIndicatorRow {
  clientKey: number;
  indicatorId: number | null;
  order: number;
  dueKind: 'absolute' | 'employment';
  dueDate: string;
  offsetValue: number | null;
  offsetUnit: 'days' | 'months' | 'years';
}

interface PlanGroupRow {
  clientKey: number;
  title: string;
  order: number;
  indicators: PlanIndicatorRow[];
}

interface IndicatorPayload {
  indicatorId?: number | null;
  order?: number;
  dueKind?: 'absolute' | 'employment';
  dueDate?: string;
  offsetValue?: number | null;
  offsetUnit?: 'days' | 'months' | 'years';
}

const props = defineProps<{
  planId: number;
}>();

// eslint-disable-next-line no-spaced-func, func-call-spacing
const emit = defineEmits<{
  (e: 'saved', payload: { id: number }): void;
  (e: 'cancel'): void;
}>();

const store = useStore();
const root = getCurrentInstance().proxy.$root;
const title = ref('');
const groups = ref<PlanGroupRow[]>([]);
const looseIndicators = ref<PlanIndicatorRow[]>([]);
const indicatorOptions = ref<IndicatorOption[]>([]);
let nextKey = 1;

const orderedGroups = computed(() => [...groups.value].sort((a, b) => a.order - b.order));
const orderedIndicators = (rows: PlanIndicatorRow[]) => [...rows].sort((a, b) => a.order - b.order);

const addIndicator = (rows: PlanIndicatorRow[]) => {
  const order = rows.reduce((max, row) => Math.max(max, row.order), 0) + 1;
  nextKey += 1;
  rows.push({
    clientKey: nextKey,
    indicatorId: null,
    order,
    dueKind: 'absolute',
    dueDate: '',
    offsetValue: null,
    offsetUnit: 'days',
  });
};

const removeIndicator = (rows: PlanIndicatorRow[], row: PlanIndicatorRow) => {
  const index = rows.findIndex(item => item.clientKey === row.clientKey);
  if (index >= 0) {
    rows.splice(index, 1);
  }
};

const addGroup = () => {
  const order = groups.value.reduce((max, row) => Math.max(max, row.order), 0) + 1;
  nextKey += 1;
  groups.value.push({
    clientKey: nextKey,
    title: '',
    order,
    indicators: [],
  });
};

const removeGroup = (group: PlanGroupRow) => {
  groups.value = groups.value.filter(row => row.clientKey !== group.clientKey);
};

const mapIndicator = (row: IndicatorPayload, index: number): PlanIndicatorRow => {
  nextKey += 1;
  return {
    clientKey: nextKey,
    indicatorId: row.indicatorId ?? null,
    order: row.order ?? index,
    dueKind: row.dueKind === 'employment' ? 'employment' : 'absolute',
    dueDate: row.dueDate || '',
    offsetValue: row.offsetValue ?? null,
    offsetUnit: row.offsetUnit || 'days',
  };
};

const payloadIndicator = (row: PlanIndicatorRow, index: number) => ({
  indicatorId: row.indicatorId,
  order: index,
  dueKind: row.dueKind,
  dueDate: row.dueDate,
  offsetValue: row.dueKind === 'employment' ? row.offsetValue : null,
  offsetUnit: row.offsetUnit,
});

const load = async () => {
  title.value = '';
  groups.value = [];
  looseIndicators.value = [];
  await store.dispatch(actions.INC_LOADING);
  try {
    const data = await api('document-manager/plans/details', { id: props.planId });
    if (!data?.ok) {
      root.$emit('msg', 'error', data?.message || 'План не найден');
      return;
    }
    title.value = data.title || '';
    indicatorOptions.value = data.indicatorOptions || [];
    groups.value = (data.groups || []).map((group, index) => {
      nextKey += 1;
      return {
        clientKey: nextKey,
        title: group.title || '',
        order: group.order ?? index,
        indicators: (group.indicators || []).map(mapIndicator),
      };
    });
    looseIndicators.value = (data.indicators || []).map(mapIndicator);
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const save = async () => {
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/plans/update', {
      id: props.planId,
      title: title.value,
      groups: orderedGroups.value.map((group, index) => ({
        title: group.title,
        order: index,
        indicators: orderedIndicators(group.indicators).map(payloadIndicator),
      })),
      indicators: orderedIndicators(looseIndicators.value).map(payloadIndicator),
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

watch(() => props.planId, load, { immediate: true });
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
    border-right: none;
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
}

.content-editor {
  flex: 1;
  padding: 5px;
  overflow-y: auto;
}

.ed-group {
  padding: 5px;
  margin: 5px;
  background: #f0f0f0;
}

.section-title {
  height: 34px;
  line-height: 34px;
  padding: 0 10px;
  color: #434a54;
}

.indicator-row {
  display: flex;
  align-items: stretch;
  margin-top: 5px;
  min-width: 0;
}

.indicator-select {
  flex: 1 1 220px;
  min-width: 160px;
}

.due-kind,
.due-date,
.offset-value,
.offset-unit {
  height: 34px;
  border-radius: 0;
  box-shadow: none;
}

.due-kind {
  flex: 0 0 230px;
}

.due-date {
  flex: 0 0 160px;
}

.offset {
  display: flex;
  flex: 0 0 220px;
}

.offset-value {
  width: 90px;
}

.offset-unit {
  width: 130px;
}

.add-row {
  margin-top: 5px;
}

.footer-editor {
  flex: 0 0 34px;
  display: flex;
  justify-content: flex-end;
  background-color: #f4f4f4;
  border-top: 1px solid #b1b1b1;

  .btn {
    border-radius: 0;
    height: 34px;
  }
}
</style>
