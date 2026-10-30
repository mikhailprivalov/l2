<template>
  <div class="root">
    <fieldset
      class="plan-fields"
      :disabled="readonly"
    >
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
            <button
              v-if="documentMode && !readonly"
              class="btn btn-blue-nb plan-gear"
              type="button"
              title="Задачи"
              @click="openTasks"
            >
              <i class="fa fa-cog" />
            </button>
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
              :disabled="readonly"
              :disable-branch-nodes="true"
              :options="indicatorSelectOptions"
              placeholder="Показатель"
              no-options-text="Нет задач"
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
            <AddresseeField
              v-model="row.executors"
              class="executor"
              header="Исполнители"
              :disabled="readonly"
            />
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
            Добавить задачу
          </button>
          <div
            v-for="row in orderedTests(group.tests)"
            :key="row.clientKey"
            class="indicator-row"
          >
            <Treeselect
              v-model="row.testId"
              class="treeselect-wide treeselect-34px indicator-select"
              :multiple="false"
              :clearable="true"
              :append-to-body="true"
              :disabled="readonly"
              :options="testOptions"
              placeholder="Тест"
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
              @click="removeTest(group.tests, row)"
            >
              Удалить
            </button>
          </div>
          <button
            class="btn btn-blue-nb add-row"
            type="button"
            @click="addTest(group.tests)"
          >
            Добавить тест
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
              :disabled="readonly"
              :disable-branch-nodes="true"
              :options="indicatorSelectOptions"
              placeholder="Показатель"
              no-options-text="Нет задач"
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
            <AddresseeField
              v-model="row.executors"
              class="executor"
              header="Исполнители"
              :disabled="readonly"
            />
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
            Добавить задачу
          </button>
          <div
            v-for="row in orderedTests(looseTests)"
            :key="row.clientKey"
            class="indicator-row"
          >
            <Treeselect
              v-model="row.testId"
              class="treeselect-wide treeselect-34px indicator-select"
              :multiple="false"
              :clearable="true"
              :append-to-body="true"
              :disabled="readonly"
              :options="testOptions"
              placeholder="Тест"
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
              @click="removeTest(looseTests, row)"
            >
              Удалить
            </button>
          </div>
          <button
            class="btn btn-blue-nb add-row"
            type="button"
            @click="addTest(looseTests)"
          >
            Добавить тест
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
    </fieldset>
    <div class="footer-editor">
      <slot name="leading" />
      <button
        v-if="!documentMode"
        class="btn btn-blue-nb"
        type="button"
        @click="emit('cancel')"
      >
        Отмена
      </button>
      <button
        v-if="!readonly"
        class="btn btn-blue-nb"
        type="button"
        @click="save(false)"
      >
        Сохранить
      </button>
      <button
        v-if="documentMode && !readonly"
        class="btn btn-blue-nb"
        type="button"
        @click="save(true)"
      >
        Сохранить и подтвердить
      </button>
      <slot name="trailing" />
    </div>
    <Modal
      v-if="tasksOpen"
      show-footer="true"
      white-bg="true"
      width="760px"
      max-width="96vw"
      height="480px"
      margin-left-right="auto"
      @close="tasksOpen = false"
    >
      <span slot="header">Задачи</span>
      <div
        slot="body"
        class="task-board"
      >
        <div class="task-board__col">
          <div class="task-board__title">
            Глобальные
          </div>
          <div
            v-for="group in filledGlobalGroups"
            :key="group.id"
          >
            <div class="task-board__group">
              {{ group.title }}
            </div>
            <div
              v-for="row in group.indicators"
              :key="row.id"
              class="task-board__item"
            >
              {{ row.label }}
            </div>
          </div>
          <div
            v-if="!filledGlobalGroups.length"
            class="task-board__empty"
          >
            Нет задач
          </div>
        </div>
        <div class="task-board__col">
          <div class="task-board__title">
            Свои
          </div>
          <div
            v-for="row in mineTasks"
            :key="row.id"
            class="task-board__item"
          >
            {{ row.label }}
          </div>
          <div
            v-if="!mineTasks.length"
            class="task-board__empty"
          >
            Своих задач пока нет
          </div>
          <div class="task-board__add">
            <input
              v-model="taskTitle"
              type="text"
              class="form-control"
              placeholder="Название задачи"
              @keyup.enter="addTask"
            >
            <button
              class="btn btn-blue-nb"
              type="button"
              :disabled="isSavingTask"
              @click="addTask"
            >
              Добавить
            </button>
          </div>
        </div>
      </div>
      <div
        slot="footer"
        class="task-board__footer"
      >
        <button
          class="btn btn-blue-nb"
          type="button"
          @click="tasksOpen = false"
        >
          Закрыть
        </button>
      </div>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import {
  computed, getCurrentInstance, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import api from '@/api';
import AddresseeField from '@/forms/Fields/AddresseeField.vue';
import Modal from '@/ui-cards/Modal.vue';
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
  executors: string;
}

interface PlanTestRow {
  clientKey: number;
  testId: number | null;
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
  tests: PlanTestRow[];
}

interface IndicatorPayload {
  indicatorId?: number | null;
  order?: number;
  dueKind?: 'absolute' | 'employment';
  dueDate?: string;
  offsetValue?: number | null;
  offsetUnit?: 'days' | 'months' | 'years';
  executors?: string | { id: number; fio?: string; department?: string }[];
}

interface TestPayload {
  testId?: number | null;
  order?: number;
  dueKind?: 'absolute' | 'employment';
  dueDate?: string;
  offsetValue?: number | null;
  offsetUnit?: 'days' | 'months' | 'years';
}

interface IndicatorCatalogGroup {
  id: number;
  title: string;
  indicators?: IndicatorOption[];
}

interface IndicatorCatalog {
  globalGroups?: IndicatorCatalogGroup[];
  global?: IndicatorOption[];
  mine?: IndicatorOption[];
  extra?: IndicatorOption[];
}

interface PlanPreset {
  title?: string;
  indicatorCatalog?: IndicatorCatalog;
  groups?: {
    title?: string;
    order?: number;
    indicators?: IndicatorPayload[];
    tests?: TestPayload[];
  }[];
  indicators?: IndicatorPayload[];
  tests?: TestPayload[];
  indicatorOptions?: IndicatorOption[];
  testOptions?: IndicatorOption[];
}

const props = defineProps<{
  planId: number;
  documentMode?: boolean;
  documentId?: number | null;
  readonly?: boolean;
  preset?: PlanPreset | null;
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
const looseTests = ref<PlanTestRow[]>([]);
const indicatorOptions = ref<IndicatorOption[]>([]);
const globalGroups = ref<IndicatorCatalogGroup[]>([]);
const mineTasks = ref<IndicatorOption[]>([]);
const extraTasks = ref<IndicatorOption[]>([]);
const tasksOpen = ref(false);
const taskTitle = ref('');
const isSavingTask = ref(false);
const testOptions = ref<IndicatorOption[]>([]);
let nextKey = 1;

const filledGlobalGroups = computed(() => globalGroups.value.filter(
  group => (group.indicators || []).length > 0,
));

const indicatorSelectOptions = computed(() => {
  const globalChildren = [];
  globalGroups.value.forEach(group => {
    const children = group.indicators || [];
    if (!children.length) {
      return;
    }
    globalChildren.push({
      id: group.id === 0 ? 'loose' : `group-${group.id}`,
      label: group.title || 'Без группы',
      children,
    });
  });
  const branches = [];
  if (globalChildren.length) {
    branches.push({
      id: 'global',
      label: 'Глобальные',
      children: globalChildren,
    });
  }
  if (props.documentMode && mineTasks.value.length) {
    branches.push({
      id: 'mine',
      label: 'Свои',
      children: mineTasks.value,
    });
  }
  const known = new Set<number>();
  globalGroups.value.forEach(group => {
    (group.indicators || []).forEach(row => known.add(row.id));
  });
  mineTasks.value.forEach(row => known.add(row.id));
  extraTasks.value.forEach(row => {
    if (!known.has(row.id)) {
      branches.push(row);
    }
  });
  if (!branches.length) {
    return indicatorOptions.value;
  }
  return branches;
});

const orderedGroups = computed(() => [...groups.value].sort((a, b) => a.order - b.order));
const orderedIndicators = (rows: PlanIndicatorRow[]) => [...rows].sort((a, b) => a.order - b.order);
const orderedTests = (rows: PlanTestRow[]) => [...rows].sort((a, b) => a.order - b.order);

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
    executors: '[]',
  });
};

const removeIndicator = (rows: PlanIndicatorRow[], row: PlanIndicatorRow) => {
  const index = rows.findIndex(item => item.clientKey === row.clientKey);
  if (index >= 0) {
    rows.splice(index, 1);
  }
};

const addTest = (rows: PlanTestRow[]) => {
  const order = rows.reduce((max, row) => Math.max(max, row.order), 0) + 1;
  nextKey += 1;
  rows.push({
    clientKey: nextKey,
    testId: null,
    order,
    dueKind: 'absolute',
    dueDate: '',
    offsetValue: null,
    offsetUnit: 'days',
  });
};

const removeTest = (rows: PlanTestRow[], row: PlanTestRow) => {
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
    tests: [],
  });
};

const removeGroup = (group: PlanGroupRow) => {
  groups.value = groups.value.filter(row => row.clientKey !== group.clientKey);
};

const executorsValue = (value: IndicatorPayload['executors']) => {
  if (typeof value === 'string') {
    return value || '[]';
  }
  return JSON.stringify(value || []);
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
    executors: executorsValue(row.executors),
  };
};

const payloadIndicator = (row: PlanIndicatorRow, index: number) => ({
  indicatorId: row.indicatorId,
  order: index,
  dueKind: row.dueKind,
  dueDate: row.dueDate,
  offsetValue: row.dueKind === 'employment' ? row.offsetValue : null,
  offsetUnit: row.offsetUnit,
  executors: row.executors || '[]',
});

const mapTest = (row: TestPayload, index: number): PlanTestRow => {
  nextKey += 1;
  return {
    clientKey: nextKey,
    testId: row.testId ?? null,
    order: row.order ?? index,
    dueKind: row.dueKind === 'employment' ? 'employment' : 'absolute',
    dueDate: row.dueDate || '',
    offsetValue: row.offsetValue ?? null,
    offsetUnit: row.offsetUnit || 'days',
  };
};

const payloadTest = (row: PlanTestRow, index: number) => ({
  testId: row.testId,
  order: index,
  dueKind: row.dueKind,
  dueDate: row.dueDate,
  offsetValue: row.dueKind === 'employment' ? row.offsetValue : null,
  offsetUnit: row.offsetUnit,
});

const applyCatalog = (data: PlanPreset) => {
  const catalog = data.indicatorCatalog;
  if (catalog?.globalGroups) {
    globalGroups.value = catalog.globalGroups;
  } else {
    globalGroups.value = [{
      id: 0,
      title: 'Без группы',
      indicators: catalog?.global || data.indicatorOptions || [],
    }];
  }
  mineTasks.value = catalog?.mine || [];
  extraTasks.value = catalog?.extra || [];
};

const applyData = (data: PlanPreset) => {
  title.value = data.title || '';
  indicatorOptions.value = data.indicatorOptions || [];
  applyCatalog(data);
  testOptions.value = data.testOptions || [];
  groups.value = (data.groups || []).map((group, index) => {
    nextKey += 1;
    return {
      clientKey: nextKey,
      title: group.title || '',
      order: group.order ?? index,
      indicators: (group.indicators || []).map(mapIndicator),
      tests: (group.tests || []).map(mapTest),
    };
  });
  looseIndicators.value = (data.indicators || []).map(mapIndicator);
  looseTests.value = (data.tests || []).map(mapTest);
};

const openTasks = () => {
  taskTitle.value = '';
  tasksOpen.value = true;
};

const addTask = async () => {
  const nextTitle = taskTitle.value.trim();
  if (!nextTitle) {
    root.$emit('msg', 'error', 'Укажите название задачи');
    return;
  }
  if (isSavingTask.value) {
    return;
  }
  isSavingTask.value = true;
  try {
    const data = await api('document-manager/indicators/create', { title: nextTitle });
    if (!data?.ok) {
      root.$emit('msg', 'error', data?.message || 'Не удалось добавить задачу');
      return;
    }
    const id = Number(data.id);
    if (Number.isFinite(id) && id > 0 && !mineTasks.value.some(row => row.id === id)) {
      mineTasks.value = [...mineTasks.value, { id, label: data.label || nextTitle }];
    }
    taskTitle.value = '';
  } finally {
    isSavingTask.value = false;
  }
};

const planBody = () => ({
  title: title.value,
  groups: orderedGroups.value.map((group, index) => ({
    title: group.title,
    order: index,
    indicators: orderedIndicators(group.indicators).map(payloadIndicator),
    tests: orderedTests(group.tests).map(payloadTest),
  })),
  indicators: orderedIndicators(looseIndicators.value).map(payloadIndicator),
  tests: orderedTests(looseTests.value).map(payloadTest),
});

const load = async () => {
  if (props.documentMode) {
    applyData(props.preset || {});
    return;
  }
  title.value = '';
  groups.value = [];
  looseIndicators.value = [];
  looseTests.value = [];
  await store.dispatch(actions.INC_LOADING);
  try {
    const data = await api('document-manager/plans/details', { id: props.planId });
    if (!data?.ok) {
      root.$emit('msg', 'error', data?.message || 'План не найден');
      return;
    }
    applyData(data);
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const save = async (withConfirm = false) => {
  await store.dispatch(actions.INC_LOADING);
  try {
    const body = planBody();
    const result = props.documentMode
      ? await api('document-manager/documents/plan', {
        id: props.documentId,
        withConfirm,
        ...body,
      })
      : await api('document-manager/plans/update', {
        id: props.planId,
        ...body,
      });
    if (result?.ok) {
      root.$emit('msg', 'ok', withConfirm ? 'Подтверждено' : 'Сохранено');
      emit('saved', { id: result.id });
    } else {
      root.$emit('msg', 'error', result?.message || 'Ошибка сохранения');
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

watch(() => props.planId, () => {
  if (!props.documentMode) {
    load();
  }
}, { immediate: true });

watch(() => props.preset, () => {
  if (props.documentMode) {
    applyData(props.preset || {});
  }
}, { immediate: true });
</script>

<style scoped lang="scss">
.root {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  height: 100%;
  background-color: #f8f7f7;
}

.plan-fields {
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  min-height: 0;
  margin: 0;
  padding: 0;
  border: 0;
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
  flex-wrap: wrap;
  margin-top: 5px;
  min-width: 0;
}

.executor {
  flex: 1 1 280px;
  min-width: 220px;
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

.plan-gear {
  flex: 0 0 34px;
  width: 34px;
  height: 34px;
  padding: 0;
  border-radius: 0;
}

.task-board {
  display: flex;
  gap: 16px;
  min-height: 240px;
}

.task-board__col {
  flex: 1 1 0;
  min-width: 0;
}

.task-board__title {
  margin-bottom: 8px;
  font-weight: 600;
}

.task-board__group {
  margin-top: 8px;
  color: #666;
  font-size: 12px;
}

.task-board__item {
  padding: 4px 0;
}

.task-board__empty {
  color: #888;
}

.task-board__add {
  display: flex;
  gap: 6px;
  margin-top: 8px;
}

.task-board__footer {
  display: flex;
  justify-content: flex-end;
}

.footer-editor {
  flex: 0 0 34px;
  display: flex;
  justify-content: flex-end;
  align-items: stretch;
  background-color: #f4f4f4;
  border-top: 1px solid #b1b1b1;

  .btn,
  ::v-deep .btn {
    border-radius: 0;
    height: 34px;
  }

  ::v-deep .print-link {
    align-self: center;
    margin-right: 12px;
    white-space: nowrap;
  }
}
</style>
