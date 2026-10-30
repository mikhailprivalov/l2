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
      >
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
  computed, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import api from '@/api';

interface PlanOption {
  id: number;
  title?: string;
  label?: string;
}

interface PlanTitle {
  id: number;
  title: string;
}

const props = defineProps<{
  value?: string | number[] | null;
  disabled?: boolean;
  documentId?: number | null;
}>();

// eslint-disable-next-line no-spaced-func, func-call-spacing
const emit = defineEmits<{
  (e: 'input', value: string): void;
}>();

const pickerKey = ref(0);
const globalPlans = ref<PlanOption[]>([]);
const minePlans = ref<PlanOption[]>([]);
const titles = ref<PlanTitle[]>([]);

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

const titleById = computed(() => {
  const map = new Map<number, string>();
  const remember = (row: PlanOption | PlanTitle) => {
    const title = row.title || ('label' in row ? row.label : '') || '';
    if (title) {
      map.set(row.id, title);
    }
  };
  globalPlans.value.forEach(remember);
  minePlans.value.forEach(remember);
  titles.value.forEach(remember);
  return map;
});

const rows = computed(() => selectedIds.value.map(id => ({
  id,
  title: titleById.value.get(id) || `План ${id}`,
})));

const optionLabel = (row: PlanOption) => row.title || row.label || String(row.id);

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
    titles.value = [];
    return;
  }
  const data = await api('document-manager/plans/preview', {
    ids,
    documentId: props.documentId || null,
  });
  if (!data?.ok) {
    return;
  }
  titles.value = (data.result || []).map(plan => ({
    id: plan.id,
    title: plan.title || '',
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

watch(
  () => [selectedIds.value.join(','), props.documentId],
  () => {
    loadTitles(selectedIds.value);
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
  align-items: center;
  gap: 10px;
  padding: 8px;
  border: 1px solid #e2e6ea;
  border-radius: 6px;
  background: #fff;
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
