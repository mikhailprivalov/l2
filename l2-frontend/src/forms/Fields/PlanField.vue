<template>
  <div class="plan-field">
    <Treeselect
      v-if="!disabled"
      :key="pickerKey"
      :value="null"
      class="treeselect-wide treeselect-34px"
      :multiple="false"
      :options="options"
      :clearable="true"
      :append-to-body="true"
      :disable-branch-nodes="true"
      placeholder="Добавить план"
      no-results-text="Не найдено"
      no-options-text="Нет планов"
      @input="onPick"
    />
    <div
      v-if="rows.length"
      class="plan-field__list"
    >
      <div
        v-for="plan in rows"
        :key="plan.id"
        class="plan-field__item"
        :class="{ 'plan-field__item--open': isOpen(plan.id) }"
      >
        <button
          class="plan-field__toggle"
          type="button"
          :title="isOpen(plan.id) ? 'Свернуть' : 'Развернуть'"
          @click="togglePlan(plan.id)"
        >
          {{ isOpen(plan.id) ? '−' : '+' }}
        </button>
        <div class="plan-field__main">
          <div class="plan-field__head">
            <div class="plan-field__name">
              {{ plan.title }}
            </div>
            <button
              v-if="!disabled"
              type="button"
              class="plan-field__remove"
              title="Удалить план"
              @click="removePlan(plan.id)"
            >
              ×
            </button>
          </div>
          <div
            v-if="isOpen(plan.id)"
            class="plan-field__body"
          >
            <div
              v-if="!plan.loaded"
              class="plan-field__empty-body"
            >
              Загрузка...
            </div>
            <div
              v-else
              class="plan-preview"
            >
              <div
                v-for="group in shownGroups(plan)"
                :key="group.id"
                class="ed-group"
              >
                <div class="input-group">
                  <span class="input-group-addon">Группа</span>
                  <input
                    class="form-control"
                    type="text"
                    readonly
                    placeholder="Название группы"
                    :value="group.title"
                  >
                </div>
                <div
                  v-for="row in curatorTasks(group.indicators, plan.id)"
                  :key="`i-${row.id}`"
                  class="indicator-row"
                >
                  <input
                    class="form-control name"
                    type="text"
                    readonly
                    placeholder="Показатель"
                    :value="row.title"
                  >
                  <PlanDue :row="row" />
                  <span class="executor-label">Исполнитель</span>
                  <AddresseeField
                    class="executor"
                    header="Исполнители"
                    :disabled="peopleLocked"
                    :value="shownExecutors(row)"
                    @input="onPeople(plan.id, row, 'executors', $event)"
                  />
                  <button
                    v-if="showPeopleCopy(plan, row)"
                    type="button"
                    class="column-copy"
                    title="Такой же исполнитель у остальных задач"
                    :disabled="copyingPeople"
                    @click="applyPeopleToRest(plan, 'executors')"
                  >
                    <i class="glyphicon glyphicon-arrow-down" />
                  </button>
                  <span class="executor-label">Куратор</span>
                  <AddresseeField
                    class="executor"
                    header="Куратор"
                    :disabled="peopleLocked"
                    :value="row.curator"
                    @input="onPeople(plan.id, row, 'curator', $event)"
                  />
                  <button
                    v-if="showPeopleCopy(plan, row)"
                    type="button"
                    class="column-copy"
                    title="Такой же куратор у остальных задач"
                    :disabled="copyingPeople"
                    @click="applyPeopleToRest(plan, 'curator')"
                  >
                    <i class="glyphicon glyphicon-arrow-down" />
                  </button>
                </div>
                <div
                  v-for="row in shownTests(group.tests, plan.id)"
                  :key="`t-${row.id}`"
                  class="indicator-row"
                >
                  <input
                    class="form-control name"
                    type="text"
                    readonly
                    placeholder="Тест"
                    :value="row.title"
                  >
                  <PlanDue :row="row" />
                </div>
              </div>
              <div
                v-if="curatorTasks(plan.indicators, plan.id).length || shownTests(plan.tests, plan.id).length"
                class="ed-group"
              >
                <div class="section-title">
                  Без группы
                </div>
                <div
                  v-for="row in curatorTasks(plan.indicators, plan.id)"
                  :key="`li-${row.id}`"
                  class="indicator-row"
                >
                  <input
                    class="form-control name"
                    type="text"
                    readonly
                    placeholder="Показатель"
                    :value="row.title"
                  >
                  <PlanDue :row="row" />
                  <span class="executor-label">Исполнитель</span>
                  <AddresseeField
                    class="executor"
                    header="Исполнители"
                    :disabled="peopleLocked"
                    :value="shownExecutors(row)"
                    @input="onPeople(plan.id, row, 'executors', $event)"
                  />
                  <button
                    v-if="showPeopleCopy(plan, row)"
                    type="button"
                    class="column-copy"
                    title="Такой же исполнитель у остальных задач"
                    :disabled="copyingPeople"
                    @click="applyPeopleToRest(plan, 'executors')"
                  >
                    <i class="glyphicon glyphicon-arrow-down" />
                  </button>
                  <span class="executor-label">Куратор</span>
                  <AddresseeField
                    class="executor"
                    header="Куратор"
                    :disabled="peopleLocked"
                    :value="row.curator"
                    @input="onPeople(plan.id, row, 'curator', $event)"
                  />
                  <button
                    v-if="showPeopleCopy(plan, row)"
                    type="button"
                    class="column-copy"
                    title="Такой же куратор у остальных задач"
                    :disabled="copyingPeople"
                    @click="applyPeopleToRest(plan, 'curator')"
                  >
                    <i class="glyphicon glyphicon-arrow-down" />
                  </button>
                </div>
                <div
                  v-for="row in shownTests(plan.tests, plan.id)"
                  :key="`lt-${row.id}`"
                  class="indicator-row"
                >
                  <input
                    class="form-control name"
                    type="text"
                    readonly
                    placeholder="Тест"
                    :value="row.title"
                  >
                  <PlanDue :row="row" />
                </div>
              </div>
              <div
                v-if="!planHasBody(plan)"
                class="plan-field__empty-body"
              >
                В плане нет показателей и тестов
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div
      v-else
      class="plan-field__empty"
    >
      Планы пока не добавлены
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
import AddresseeField from '@/forms/Fields/AddresseeField.vue';
import PlanDue from '@/forms/Fields/PlanDue.vue';

interface PlanOption {
  id: number;
  title?: string;
  shortTitle?: string;
  label?: string;
}

interface PlanLine {
  id: number;
  indicatorId: number;
  title: string;
  dueKind: 'absolute' | 'employment';
  dueDate: string;
  offsetValue: number | null;
  offsetUnit: string;
  executors: string;
  curator: string;
}

interface PlanGroup {
  id: number;
  title: string;
  indicators: PlanLine[];
  tests: PlanLine[];
}

interface PlanPreview {
  id: number;
  title: string;
  shortTitle?: string;
  groups: PlanGroup[];
  indicators: PlanLine[];
  tests: PlanLine[];
}

interface PlanRow extends PlanPreview {
  loaded: boolean;
}

const props = defineProps<{
  value?: string | number[] | null;
  disabled?: boolean;
  documentId?: number | null;
  addressees?: string | null;
  controlPlanId?: number | null;
  curatorId?: number | null;
}>();

// eslint-disable-next-line no-spaced-func, func-call-spacing
const emit = defineEmits<{
  (e: 'input', value: string): void;
}>();

const root = getCurrentInstance()?.proxy?.$root;
const pickerKey = ref(0);
const copyingPeople = ref(false);
const globalPlans = ref<PlanOption[]>([]);
const minePlans = ref<PlanOption[]>([]);
const previews = ref<PlanPreview[]>([]);
const openIds = ref<number[]>([]);

const parseIds = (value: unknown): number[] => {
  let raw: unknown = value;
  if (typeof value === 'string') {
    if (!value) {
      return [];
    }
    try {
      raw = JSON.parse(value);
    } catch {
      return [];
    }
  }
  if (!Array.isArray(raw)) {
    return [];
  }
  const ids: number[] = [];
  raw.forEach(item => {
    const pk = Number(item && typeof item === 'object' ? item.id : item);
    if (Number.isFinite(pk) && pk > 0 && !ids.includes(pk)) {
      ids.push(pk);
    }
  });
  return ids;
};

const selectedIds = computed(() => parseIds(props.value));
const peopleLocked = computed(() => Boolean(props.disabled) || !props.documentId);

const titleById = computed(() => {
  const map = new Map<number, string>();
  const remember = (row: PlanOption | PlanPreview) => {
    const title = row.shortTitle || row.title || ('label' in row ? row.label : '') || '';
    if (title) {
      map.set(row.id, title);
    }
  };
  globalPlans.value.forEach(remember);
  minePlans.value.forEach(remember);
  previews.value.forEach(remember);
  return map;
});

const previewById = computed(() => new Map(previews.value.map(plan => [plan.id, plan])));

const executorsText = (value: unknown) => {
  if (typeof value === 'string') {
    return value || '[]';
  }
  return JSON.stringify(value || []);
};

const planLines = (rows: Record<string, unknown>[] | undefined): PlanLine[] => (
  (rows || []).map(row => ({
    id: Number(row.id) || 0,
    indicatorId: Number(row.indicatorId) || 0,
    title: String(row.title || ''),
    dueKind: row.dueKind === 'employment' ? 'employment' : 'absolute',
    dueDate: String(row.dueDate || ''),
    offsetValue: row.offsetValue == null || row.offsetValue === '' ? null : Number(row.offsetValue),
    offsetUnit: String(row.offsetUnit || 'days'),
    executors: executorsText(row.executors),
    curator: executorsText(row.curator),
  }))
);

const rows = computed((): PlanRow[] => selectedIds.value.map(id => {
  const preview = previewById.value.get(id);
  return {
    id,
    title: preview?.title || titleById.value.get(id) || `План ${id}`,
    groups: preview?.groups || [],
    indicators: preview?.indicators || [],
    tests: preview?.tests || [],
    loaded: Boolean(preview),
  };
}));

const peopleIds = (value: string) => {
  try {
    const parsed = JSON.parse(value || '[]');
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed
      .map(row => Number(row?.id))
      .filter(id => Number.isFinite(id) && id > 0);
  } catch {
    return [];
  }
};

const controlsPlan = (planId: number) => {
  const selected = Number(props.controlPlanId);
  const curatorId = Number(props.curatorId);
  return Number.isFinite(selected) && selected === planId && Number.isFinite(curatorId) && curatorId > 0;
};

const curatorTasks = (tasks: PlanLine[], planId: number) => {
  if (!controlsPlan(planId)) {
    return tasks;
  }
  const curatorId = Number(props.curatorId);
  return tasks.filter(row => peopleIds(row.curator).includes(curatorId));
};

const shownTests = (tests: PlanLine[], planId: number) => (controlsPlan(planId) ? [] : tests);

const shownGroups = (plan: PlanRow) => {
  if (!controlsPlan(plan.id)) {
    return plan.groups;
  }
  return plan.groups.filter(group => curatorTasks(group.indicators, plan.id).length > 0);
};

const isOpen = (id: number) => openIds.value.includes(id) || controlsPlan(id);

const togglePlan = (id: number) => {
  openIds.value = isOpen(id)
    ? openIds.value.filter(item => item !== id)
    : [...openIds.value, id];
};

const visibleCuratorTasks = (plan: PlanRow) => [
  ...shownGroups(plan).flatMap(group => curatorTasks(group.indicators, plan.id)),
  ...curatorTasks(plan.indicators, plan.id),
];

const showPeopleCopy = (plan: PlanRow, row: PlanLine) => (
  !peopleLocked.value
  && visibleCuratorTasks(plan).length > 1
  && visibleCuratorTasks(plan)[0]?.id === row.id
);

const samePeople = (left: string, right: string) => {
  const first = peopleIds(left);
  const second = peopleIds(right);
  return first.length === second.length && first.every((id, index) => id === second[index]);
};

const shownExecutors = (row: PlanLine) => (
  peopleIds(row.executors).length ? row.executors : (props.addressees || '[]')
);

const planHasBody = (plan: PlanRow) => {
  if (controlsPlan(plan.id)) {
    return curatorTasks(plan.indicators, plan.id).length > 0 || shownGroups(plan).length > 0;
  }
  return plan.groups.length > 0 || plan.indicators.length > 0 || plan.tests.length > 0;
};

const optionLabel = (row: PlanOption) => row.shortTitle || row.title || row.label || String(row.id);

const options = computed(() => {
  const selected = new Set(selectedIds.value);
  const groups = [];
  const globalChildren = globalPlans.value
    .filter(row => !selected.has(row.id))
    .map(row => ({ id: row.id, label: optionLabel(row) }));
  const mineChildren = minePlans.value
    .filter(row => !selected.has(row.id))
    .map(row => ({ id: row.id, label: optionLabel(row) }));
  if (globalChildren.length) {
    groups.push({
      id: 'global',
      label: 'Глобальные планы',
      children: globalChildren,
    });
  }
  if (mineChildren.length) {
    groups.push({
      id: 'mine',
      label: 'Мои планы',
      children: mineChildren,
    });
  }
  return groups;
});

const loadChoices = async () => {
  const data = await api('document-manager/plans/choices', {});
  if (!data?.ok) {
    return;
  }
  globalPlans.value = data.global || [];
  minePlans.value = data.mine || [];
};

const loadTitles = async (ids: number[]) => {
  if (!ids.length) {
    previews.value = [];
    return;
  }
  const body: { ids: number[]; documentId: number | null; addressees?: string } = {
    ids,
    documentId: props.documentId || null,
  };
  if (props.addressees != null) {
    body.addressees = props.addressees;
  }
  const data = await api('document-manager/plans/preview', body);
  if (!data?.ok) {
    return;
  }
  previews.value = (data.result || []).map(plan => ({
    id: Number(plan.id),
    title: plan.title || '',
    groups: (plan.groups || []).map(group => ({
      id: Number(group.id),
      title: group.title || '',
      indicators: planLines(group.indicators),
      tests: planLines(group.tests),
    })),
    indicators: planLines(plan.indicators),
    tests: planLines(plan.tests),
  }));
};

const onPick = (value: unknown) => {
  const id = Number(value);
  pickerKey.value += 1;
  if (Number.isFinite(id) && id > 0 && !selectedIds.value.includes(id)) {
    emit('input', JSON.stringify([...selectedIds.value, id]));
  }
};

const removePlan = (id: number) => {
  emit('input', JSON.stringify(selectedIds.value.filter(item => item !== id)));
};

const peopleLine = (planId: number, row: PlanLine) => {
  const plan = previews.value.find(item => item.id === planId);
  const lines = [
    ...(plan?.indicators || []),
    ...(plan?.groups || []).flatMap(group => group.indicators),
  ];
  return lines.find(item => item.id === row.id) || null;
};

const setPeople = (planId: number, row: PlanLine, kind: 'executors' | 'curator', value: string) => {
  const line = peopleLine(planId, row);
  if (!line) {
    return;
  }
  if (kind === 'executors') {
    line.executors = value;
  } else {
    line.curator = value;
  }
};

const onPeople = async (planId: number, row: PlanLine, kind: 'executors' | 'curator', value: string) => {
  const next = value || '[]';
  setPeople(planId, row, kind, next);
  if (!props.documentId || !row.indicatorId) {
    return false;
  }
  const data = await api('document-manager/plans/people', {
    documentId: props.documentId,
    planId,
    indicatorId: row.indicatorId,
    kind,
    people: next,
  });
  if (!data?.ok) {
    root?.$emit('msg', 'error', data?.message || 'Не удалось сохранить');
    loadTitles(selectedIds.value);
    return false;
  }
  setPeople(planId, row, kind, JSON.stringify(data.people || []));
  return true;
};

const applyPeopleToRest = async (plan: PlanRow, kind: 'executors' | 'curator') => {
  const tasks = visibleCuratorTasks(plan);
  const source = tasks[0];
  if (copyingPeople.value || !source || tasks.length < 2 || peopleLocked.value) {
    return;
  }
  copyingPeople.value = true;
  try {
    const value = kind === 'executors' ? shownExecutors(source) : (source.curator || '[]');
    for (const row of tasks.slice(1)) {
      const current = kind === 'executors' ? row.executors : row.curator;
      if (samePeople(current, value)) {
        continue;
      }
      const saved = await onPeople(plan.id, row, kind, value);
      if (!saved) {
        break;
      }
    }
  } finally {
    copyingPeople.value = false;
  }
};

watch(
  () => [selectedIds.value.join(','), props.documentId, props.addressees || ''],
  () => {
    const ids = selectedIds.value;
    openIds.value = openIds.value.filter(id => ids.includes(id));
    loadTitles(ids);
  },
  { immediate: true },
);

loadChoices();
</script>

<style scoped lang="scss">
.plan-field {
  width: 100%;
}

.plan-field__list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.plan-field__item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px;
  border: 1px solid #e2e6ea;
  border-radius: 6px;
  background: #fff;
}

.plan-field__item--open {
  border-color: #ccd1d9;
}

.plan-field__toggle {
  flex: 0 0 auto;
  width: 16px;
  margin-top: 4px;
  padding: 0;
  border: 0;
  background: transparent;
  color: #434a54;
  font-size: 16px;
  font-weight: bold;
  line-height: 1;
  cursor: pointer;
}

.plan-field__main {
  min-width: 0;
  flex: 1 1 auto;
}

.plan-field__head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.plan-field__name {
  min-width: 0;
  flex: 1 1 auto;
  overflow: hidden;
  color: #222;
  font-size: 13px;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plan-field__body {
  margin-top: 8px;
}

.plan-preview {
  .ed-group {
    margin-top: 4px;
    padding: 4px;
    background: #f0f0f0;
  }

  .input-group {
    display: flex;
    align-items: stretch;
    width: 100%;
    height: 28px;
  }

  .input-group-addon {
    display: flex;
    align-items: center;
    flex: 0 0 auto;
    height: 28px;
    padding: 0 8px;
    color: #fff;
    font-size: 12px;
    line-height: 18px;
    white-space: nowrap;
    background: #aab2bd;
    border-bottom: 1px solid #96a0ad;
  }

  .form-control,
  .form-control[readonly],
  .form-control:disabled {
    height: 28px;
    padding: 0 8px;
    color: #434a54;
    font-size: 12px;
    line-height: 18px;
    background: #fff;
    opacity: 1;
    border: 0;
    border-bottom: 1px solid #96a0ad;
    border-left: 1px solid #96a0ad;
    border-radius: 0;
    box-shadow: none;
  }

  .input-group .form-control {
    flex: 1 1 auto;
    min-width: 0;
  }

  .section-title {
    height: 28px;
    padding: 0 8px;
    color: #434a54;
    font-size: 12px;
    line-height: 28px;
  }

  .indicator-row {
    display: flex;
    align-items: stretch;
    flex-wrap: wrap;
    gap: 0;
    margin-top: 4px;
    min-width: 0;
  }

  .name {
    flex: 1 1 180px;
    min-width: 140px;
  }

  :deep(.plan-due) {
    display: contents;
  }

  :deep(.due-kind) {
    flex: 0 0 92px;
    width: 92px;
    max-width: 92px;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .executor-label {
    display: flex;
    align-items: center;
    flex: 0 0 auto;
    height: 28px;
    padding: 0 8px;
    color: #fff;
    font-size: 12px;
    line-height: 26px;
    white-space: nowrap;
    background: #aab2bd;
    border-bottom: 1px solid #96a0ad;
    border-left: 1px solid #96a0ad;
  }

  :deep(.due-date) {
    flex: 0 0 132px;
  }

  :deep(.offset) {
    display: flex;
    flex: 0 0 180px;
  }

  :deep(.offset-value) {
    width: 72px;
  }

  :deep(.offset-unit) {
    width: 108px;
  }

  :deep(.form-control),
  :deep(.form-control[readonly]),
  :deep(.form-control:disabled) {
    height: 28px;
    padding: 0 8px;
    color: #434a54;
    font-size: 12px;
    line-height: 18px;
    background: #fff;
    opacity: 1;
    border: 0;
    border-bottom: 1px solid #96a0ad;
    border-left: 1px solid #96a0ad;
    border-radius: 0;
    box-shadow: none;
  }

  .executor {
    flex: 1 1 220px;
    min-width: 180px;
  }

  :deep(.addressee-field) {
    min-height: 28px;
  }

  :deep(.addressee-field__preview) {
    padding: 4px 8px;
    font-size: 12px;
    line-height: 18px;
  }

  :deep(.executor.addressee-field) {
    height: 28px;
    min-height: 28px;
  }

  :deep(.executor .addressee-field__btn) {
    height: 28px;
    min-height: 28px;
    padding: 0 8px;
    border-radius: 0;
    line-height: 26px;
  }

  .column-copy {
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 0 0 28px;
    width: 28px;
    height: 28px;
    padding: 0;
    color: #fff;
    background: #aab2bd;
    border: 0;
    border-bottom: 1px solid #96a0ad;
    border-left: 1px solid #96a0ad;
    cursor: pointer;

    &:hover:not(:disabled) {
      background: #656d78;
    }

    &:disabled {
      cursor: default;
      opacity: 0.6;
    }
  }
}

.plan-field__empty-body {
  color: #888;
  font-size: 13px;
}

.plan-field__remove {
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

  &:hover {
    background: #fff2f2;
  }
}

.plan-field__empty {
  margin-top: 12px;
  padding: 12px;
  border-radius: 6px;
  background: #fff;
  color: #888;
  font-size: 13px;
  text-align: center;
}
</style>
