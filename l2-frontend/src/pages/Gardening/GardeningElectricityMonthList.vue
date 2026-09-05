<template>
  <div class="month-list">
    <div class="month-list__toolbar">
      <label class="month-list__filter">
        <input
          v-model="filterDebt"
          type="checkbox"
        >
        Есть долг
      </label>
      <label class="month-list__filter">
        <input
          v-model="filterNoReading"
          type="checkbox"
        >
        Нет показаний
      </label>
    </div>
    <div
      v-if="!year || !month"
      class="month-list__empty"
    >
      Выберите месяц
    </div>
    <div
      v-else-if="visibleRows.length === 0"
      class="month-list__empty"
    >
      Нет данных
    </div>
    <div
      v-else
      class="month-list__body"
    >
      <table class="month-list__table">
        <thead>
          <tr>
            <th
              v-for="col in columns"
              :key="col.key"
              :class="{
                'month-list__num': col.numeric,
                'month-list__sorted': sortKey === col.key,
                'month-list__narrow': col.narrow,
                'month-list__fit': col.fit,
                'month-list__gap-after': col.gapAfter,
              }"
              @click="toggleSort(col.key)"
            >
              {{ col.label }}
              <span
                v-if="sortKey === col.key"
                class="month-list__sort"
              >{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
            </th>
            <th class="month-list__actions" />
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in visibleRows"
            :key="`${row.real_estate_id}-${row.meter_id}`"
          >
            <td>{{ formatText(row.num_object) }}</td>
            <td
              class="month-list__fit month-list__gap-after"
              :title="row.meter_title"
            >
              {{ formatText(row.meter_title) }}
            </td>
            <td
              class="month-list__num month-list__narrow month-list__gap-after"
              :class="{ 'month-list__manual': row.previous_manual }"
            >
              <input
                v-if="isEditing(row)"
                v-model="formPrevious"
                class="form-control month-list__field"
                type="number"
                min="0"
                step="0.01"
                :disabled="saving"
              >
              <template v-else>
                {{ formatValue(row.previous_reading) }}
              </template>
            </td>
            <td class="month-list__num month-list__narrow">
              <input
                v-if="isEditing(row)"
                v-model="formCurrent"
                class="form-control month-list__field"
                type="number"
                min="0"
                step="0.01"
                :disabled="saving"
              >
              <template v-else>
                {{ formatValue(row.current_reading) }}
              </template>
            </td>
            <td class="month-list__num">
              {{ formatValue(row.consumption) }}
            </td>
            <td
              class="month-list__num month-list__narrow"
              :class="{ 'month-list__missing': isMissing(row.tariff) }"
            >
              {{ formatMissingZero(row.tariff) }}
            </td>
            <td class="month-list__num">
              {{ formatValue(row.charge) }}
            </td>
            <td class="month-list__num">
              {{ formatValue(row.written_off) }}
            </td>
            <td class="month-list__num">
              {{ formatValue(row.consumption_total) }}
            </td>
            <td class="month-list__num">
              {{ formatValue(row.written_off_total) }}
            </td>
            <td
              class="month-list__num"
              :class="debtClass(row.debt)"
            >
              {{ formatValue(row.debt) }}
            </td>
            <td
              class="month-list__num"
              :class="remainderClass(row.remainder)"
            >
              {{ formatRemainder(row.remainder) }}
            </td>
            <td class="month-list__num">
              {{ formatValue(row.receipt) }}
            </td>
            <td class="month-list__actions">
              <template v-if="isEditing(row)">
                <button
                  class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                  type="button"
                  :title="isCurrentLessThanPrevious(formCurrent, formPrevious) ? READING_ORDER_ERROR : 'Сохранить'"
                  :disabled="saving || !canSave"
                  @click="saveEdit(row)"
                >
                  <i class="fa fa-check" />
                </button>
                <button
                  class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                  type="button"
                  title="Отмена"
                  :disabled="saving"
                  @click="cancelEdit"
                >
                  <i class="fa fa-times" />
                </button>
              </template>
              <button
                v-else
                class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                type="button"
                title="Ввести показания"
                :disabled="saving || editingKey !== null"
                @click="startEdit(row)"
              >
                <i class="fa fa-pencil" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  getCurrentInstance,
  ref,
  watch,
} from 'vue';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';

interface MonthRow {
  real_estate_id: number;
  num_object: number | null;
  meter_id: number;
  meter_title: string;
  subscriber_address: string;
  subscriber: string;
  device_type: string;
  serial_number: string;
  reading_id: number | null;
  previous_reading: string | null;
  previous_manual?: boolean;
  current_reading: string | null;
  consumption: string | null;
  tariff: string | null;
  charge: string | null;
  written_off: string | null;
  consumption_total: string | null;
  written_off_total: string | null;
  receipt: string | null;
  debt: string | null;
  remainder: string | null;
}

type SortKey =
  | 'num_object'
  | 'meter_title'
  | 'previous_reading'
  | 'current_reading'
  | 'consumption'
  | 'tariff'
  | 'charge'
  | 'written_off'
  | 'consumption_total'
  | 'written_off_total'
  | 'receipt'
  | 'debt'
  | 'remainder';

const props = defineProps<{
  year: number | null;
  month: number | null;
}>();

const emit = defineEmits<{(e: 'readings-changed'): void;
}>();

const store = useStore();
const root = getCurrentInstance().proxy.$root;
const rows = ref<MonthRow[]>([]);
const filterDebt = ref(false);
const filterNoReading = ref(false);
const sortKey = ref<SortKey>('num_object');
const sortDir = ref<'asc' | 'desc'>('asc');
const editingKey = ref<string | null>(null);
const formPrevious = ref('');
const formCurrent = ref('');
const originalPrevious = ref<string | null>(null);
const saving = ref(false);

const pad2 = (value: number) => String(value).padStart(2, '0');

const previousHeader = computed(() => {
  if (!props.year || !props.month) {
    return 'Прошлый';
  }
  return `01.${pad2(props.month)}.${props.year}`;
});

const currentHeader = computed(() => {
  if (!props.year || !props.month) {
    return 'Текущий';
  }
  const lastDay = new Date(props.year, props.month, 0).getDate();
  return `${pad2(lastDay)}.${pad2(props.month)}.${props.year}`;
});

const columns = computed(() => ([
  { key: 'num_object' as SortKey, label: 'Участок', numeric: false },
  {
    key: 'meter_title' as SortKey,
    label: 'Счётчик',
    numeric: false,
    fit: true,
    gapAfter: true,
  },
  {
    key: 'previous_reading' as SortKey,
    label: previousHeader.value,
    numeric: true,
    narrow: true,
    gapAfter: true,
  },
  {
    key: 'current_reading' as SortKey,
    label: currentHeader.value,
    numeric: true,
    narrow: true,
  },
  { key: 'consumption' as SortKey, label: 'Потребление', numeric: true },
  {
    key: 'tariff' as SortKey,
    label: 'Тариф',
    numeric: true,
    narrow: true,
  },
  { key: 'charge' as SortKey, label: 'Начислено', numeric: true },
  { key: 'written_off' as SortKey, label: 'Списано', numeric: true },
  { key: 'consumption_total' as SortKey, label: 'Потребление общ', numeric: true },
  { key: 'written_off_total' as SortKey, label: 'Списано общ', numeric: true },
  { key: 'debt' as SortKey, label: 'Долг общ', numeric: true },
  { key: 'remainder' as SortKey, label: 'Остаток общ', numeric: true },
  { key: 'receipt' as SortKey, label: 'Приход общ', numeric: true },
]));

const formatText = (value: string | number | null | undefined) => {
  if (value === null || value === undefined || value === '') {
    return '—';
  }
  return String(value);
};

const formatValue = (value: string | null | undefined) => {
  if (value === null || value === undefined || value === '') {
    return '—';
  }
  return value;
};

const isMissing = (value: string | null | undefined) => value == null || value === '';

const formatMissingZero = (value: string | null | undefined) => {
  if (isMissing(value)) {
    return '0.00';
  }
  return value;
};

const parseAmount = (value: string | number | null | undefined) => {
  if (value === null || value === undefined || value === '') {
    return NaN;
  }
  const amount = Number(String(value).replace(',', '.'));
  return Number.isFinite(amount) ? amount : NaN;
};

const formatRemainder = (value: string | null) => {
  if (value === null || value === undefined) {
    return '—';
  }
  const amount = parseAmount(value);
  if (!Number.isFinite(amount)) {
    return value;
  }
  if (Math.abs(amount) < 0.005) {
    return '0.00';
  }
  return amount.toFixed(2);
};

const remainderClass = (value: string | null) => {
  if (value === null || value === undefined) {
    return null;
  }
  const amount = parseAmount(value);
  if (!Number.isFinite(amount) || Math.abs(amount) < 0.005) {
    return 'month-list__remainder--zero';
  }
  return amount > 0 ? 'month-list__remainder--plus' : 'month-list__remainder--minus';
};

const debtClass = (value: string | null) => {
  if (value === null || value === undefined) {
    return null;
  }
  const amount = parseAmount(value);
  if (!Number.isFinite(amount) || amount <= 0.005) {
    return null;
  }
  return 'month-list__debt';
};

const rowKey = (row: MonthRow) => `${row.real_estate_id}-${row.meter_id}`;

const isEditing = (row: MonthRow) => editingKey.value === rowKey(row);

const hasDebt = (row: MonthRow) => {
  const amount = parseAmount(row.debt);
  return Number.isFinite(amount) && amount > 0.005;
};

const hasNoReading = (row: MonthRow) => isMissing(row.current_reading);

const sortValue = (row: MonthRow, key: SortKey) => {
  const value = row[key];
  if (key === 'num_object') {
    return row.num_object == null ? Number.POSITIVE_INFINITY : row.num_object;
  }
  if (
    key === 'previous_reading'
    || key === 'current_reading'
    || key === 'consumption'
    || key === 'tariff'
    || key === 'charge'
    || key === 'written_off'
    || key === 'consumption_total'
    || key === 'written_off_total'
    || key === 'receipt'
    || key === 'debt'
    || key === 'remainder'
  ) {
    const amount = parseAmount(value as string | null);
    return Number.isFinite(amount) ? amount : Number.NEGATIVE_INFINITY;
  }
  return String(value || '').toLowerCase();
};

const visibleRows = computed(() => {
  let list = rows.value.slice();
  if (filterDebt.value && filterNoReading.value) {
    list = list.filter((row) => hasDebt(row) || hasNoReading(row));
  } else if (filterDebt.value) {
    list = list.filter((row) => hasDebt(row));
  } else if (filterNoReading.value) {
    list = list.filter((row) => hasNoReading(row));
  }
  const dir = sortDir.value === 'asc' ? 1 : -1;
  const key = sortKey.value;
  list.sort((left, right) => {
    const a = sortValue(left, key);
    const b = sortValue(right, key);
    if (a < b) {
      return -1 * dir;
    }
    if (a > b) {
      return 1 * dir;
    }
    return 0;
  });
  return list;
});

const READING_ORDER_ERROR = 'Текущее показание не может быть меньше предыдущего';

const isCurrentLessThanPrevious = (currentRaw: string, previousRaw: string) => {
  const current = parseAmount(currentRaw);
  const previous = parseAmount(previousRaw);
  if (!Number.isFinite(current) || !Number.isFinite(previous)) {
    return false;
  }
  return current < previous;
};

const canSave = computed(() => (
  formCurrent.value !== '' && !isCurrentLessThanPrevious(formCurrent.value, formPrevious.value)
));

const toggleSort = (key: SortKey) => {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc';
    return;
  }
  sortKey.value = key;
  sortDir.value = 'asc';
};

const cancelEdit = () => {
  editingKey.value = null;
  formPrevious.value = '';
  formCurrent.value = '';
  originalPrevious.value = null;
};

const startEdit = (row: MonthRow) => {
  if (saving.value || editingKey.value !== null) {
    return;
  }
  editingKey.value = rowKey(row);
  formPrevious.value = row.previous_reading || '';
  formCurrent.value = row.current_reading || '';
  originalPrevious.value = row.previous_reading;
};

const previousPayload = () => {
  if (formPrevious.value === '') {
    return null;
  }
  if (formPrevious.value !== (originalPrevious.value || '')) {
    return formPrevious.value;
  }
  return undefined;
};

const fetchRows = async () => {
  if (!props.year || !props.month) {
    rows.value = [];
    return;
  }
  const { ok, message, result } = await api('gardening/get-electricity-month-rows', {
    year: props.year,
    month: props.month,
  });
  if (ok === false) {
    root.$emit('msg', 'error', message || 'Не удалось загрузить показания');
    rows.value = [];
    return;
  }
  rows.value = Array.isArray(result?.rows) ? result.rows : [];
};

const loadData = async () => {
  cancelEdit();
  if (!props.year || !props.month) {
    rows.value = [];
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    await fetchRows();
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const saveEdit = async (row: MonthRow) => {
  if (!canSave.value || saving.value || !props.year || !props.month) {
    if (isCurrentLessThanPrevious(formCurrent.value, formPrevious.value)) {
      root.$emit('msg', 'error', READING_ORDER_ERROR);
    }
    return;
  }
  saving.value = true;
  await store.dispatch(actions.INC_LOADING);
  try {
    const previousReading = previousPayload();
    let response;
    if (row.reading_id) {
      const payload: Record<string, unknown> = {
        id: row.reading_id,
        year: props.year,
        reading: formCurrent.value,
      };
      if (previousReading !== undefined) {
        payload.previous_reading = previousReading;
      }
      response = await api('gardening/update-electricity-reading', payload);
    } else {
      const payload: Record<string, unknown> = {
        real_estate_id: row.real_estate_id,
        year: props.year,
        meter_id: row.meter_id,
        month: props.month,
        reading: formCurrent.value,
      };
      if (previousReading !== undefined) {
        payload.previous_reading = previousReading;
      }
      response = await api('gardening/create-electricity-reading', payload);
    }
    const { ok, message } = response;
    if (!ok) {
      root.$emit('msg', 'error', message || 'Не удалось сохранить показание');
      return;
    }
    root.$emit('msg', 'ok', 'Показание сохранено');
    emit('readings-changed');
    cancelEdit();
    await fetchRows();
  } finally {
    saving.value = false;
    await store.dispatch(actions.DEC_LOADING);
  }
};

watch(
  () => [props.year, props.month],
  () => {
    loadData();
  },
  { immediate: true },
);
</script>

<style scoped lang="scss">
.month-list {
  display: flex;
  flex-direction: column;
  width: 100%;
  min-height: 0;
  overflow: auto;
  background-color: #f8f7f7;
  color: #434A54;
}

.month-list__toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  box-sizing: border-box;
  min-height: 34px;
  padding: 0 10px;
  border-bottom: 1px solid #b1b1b1;
  background-color: #ececec;
}

.month-list__filter {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  font-weight: normal;
  cursor: pointer;
  white-space: nowrap;

  input {
    margin: 0;
    cursor: pointer;
  }
}

.month-list__empty {
  padding: 10px;
  color: #666;
}

.month-list__body {
  overflow: auto;
  min-height: 0;
}

.month-list__table {
  width: max-content;
  min-width: 0;
  border-collapse: collapse;
  table-layout: auto;

  th,
  td {
    box-sizing: border-box;
    height: 34px;
    padding: 0 6px;
    border-bottom: 1px solid #b1b1b1;
    text-align: left;
    vertical-align: middle;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    width: 1%;
  }

  th {
    font-weight: bold;
    background-color: #ececec;
    position: sticky;
    top: 0;
    z-index: 1;
    cursor: pointer;
    user-select: none;
  }

  th.month-list__narrow,
  td.month-list__narrow {
    max-width: 100px;
    padding-left: 4px;
    padding-right: 4px;
  }

  th.month-list__fit,
  td.month-list__fit {
    max-width: none;
    overflow: visible;
    text-overflow: clip;
  }

  th.month-list__gap-after,
  td.month-list__gap-after {
    padding-right: 18px;
  }
}

.month-list__num {
  text-align: right !important;
}

.month-list__narrow .month-list__field {
  max-width: 100%;
}

.month-list__sorted {
  background-color: #dfe3e8 !important;
}

.month-list__sort {
  margin-left: 4px;
  font-size: 10px;
}

.month-list__actions {
  width: 72px;
  min-width: 72px;
  max-width: 72px;
  text-align: right !important;
  white-space: nowrap;
  overflow: visible;
}

.month-list__field {
  height: 32px !important;
  width: 100%;
  max-width: 110px;
  border: none !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  padding: 0 6px;
  margin: 0;
  text-align: right;
}

.month-list__manual {
  font-style: italic;
}

.month-list__missing,
.month-list__debt {
  color: #c62828;
  font-weight: bold;
}

.month-list__remainder--plus {
  color: #2e7d32;
  font-weight: bold;
}

.month-list__remainder--minus {
  color: #c62828;
  font-weight: bold;
}

.month-list__remainder--zero {
  font-weight: bold;
}

.toolbar-icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 22px;
  min-height: 22px;
  max-height: 22px;
  min-width: 22px;
  padding: 0 6px;
  flex-shrink: 0;
  line-height: 1;
  box-sizing: border-box;
}
</style>
