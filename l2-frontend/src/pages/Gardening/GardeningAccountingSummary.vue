<template>
  <div class="accounting-summary">
    <div
      v-if="mode === 'table' && !loading"
      class="accounting-summary__toolbar"
    >
      <label class="accounting-summary__filter">
        <input
          v-model="filterDebt"
          type="checkbox"
        >
        Есть долг
      </label>
    </div>
    <div
      v-if="!year"
      class="accounting-summary__empty"
    >
      Выберите год
    </div>
    <div
      v-else-if="loading"
      class="accounting-summary__empty"
    >
      Загрузка…
    </div>
    <template v-else-if="mode === 'totals'">
      <div
        v-if="totalItems.length === 0"
        class="accounting-summary__empty"
      >
        Нет видов платежей за {{ year }}
      </div>
      <div
        v-for="item in totalItems"
        :key="item.payment_type_id"
        class="accounting-summary__block"
      >
        <div class="accounting-summary__block-header">
          <span>{{ item.title }}</span>
          <span class="accounting-summary__period">
            {{ formatDate(item.date_start) }} — {{ formatDate(item.date_end) }}
          </span>
          <span class="accounting-summary__sum">{{ item.receipts_total }}</span>
        </div>
      </div>
    </template>
    <div
      v-else-if="mode === 'table' && visibleRows.length === 0"
      class="accounting-summary__empty"
    >
      Нет данных
    </div>
    <div
      v-else-if="mode === 'table'"
      class="accounting-summary__body"
    >
      <table class="accounting-summary__table">
        <thead>
          <tr>
            <th
              v-for="col in columns"
              :key="col.key"
              :class="{
                'accounting-summary__num': col.numeric,
                'accounting-summary__sorted': sortKey === col.key,
              }"
              @click="toggleSort(col.key)"
            >
              {{ col.label }}
              <span
                v-if="sortKey === col.key"
                class="accounting-summary__sort"
              >{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in visibleRows"
            :key="row.real_estate_id"
          >
            <td>{{ formatText(row.num_object) }}</td>
            <td
              class="accounting-summary__num"
              :class="{ 'accounting-summary__missing': isAmountMissing(row.tariff) }"
            >
              {{ formatMissingZero(row.tariff) }}
            </td>
            <td
              class="accounting-summary__num"
              :class="{ 'accounting-summary__missing': isAmountMissing(row.coefficient) }"
            >
              {{ formatMissingZero(row.coefficient) }}
            </td>
            <td
              class="accounting-summary__num"
              :class="{ 'accounting-summary__missing': isAmountMissing(row.charge) }"
            >
              {{ formatMissingZero(row.charge) }}
            </td>
            <td class="accounting-summary__num">
              {{ formatValue(row.written_off) }}
            </td>
            <td
              class="accounting-summary__num"
              :class="debtClass(row.debt)"
            >
              {{ formatValue(row.debt) }}
            </td>
            <td
              class="accounting-summary__num"
              :class="remainderClass(row.remainder)"
            >
              {{ formatRemainder(row.remainder) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div
      v-else
      class="accounting-summary__empty"
    >
      Нет данных
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

interface TotalItem {
  payment_type_id: number;
  title: string;
  is_absolute: boolean;
  date_start: string;
  date_end: string;
  receipts_total: string;
}

interface SummaryRow {
  real_estate_id: number;
  num_object: number | null;
  tariff: string | null;
  coefficient: string | null;
  charge: string | null;
  written_off: string | null;
  debt: string | null;
  remainder: string | null;
}

type SortKey =
  | 'num_object'
  | 'tariff'
  | 'coefficient'
  | 'charge'
  | 'written_off'
  | 'debt'
  | 'remainder';

const columns: { key: SortKey; label: string; numeric: boolean }[] = [
  { key: 'num_object', label: 'Участок', numeric: false },
  { key: 'tariff', label: 'Тариф', numeric: true },
  { key: 'coefficient', label: 'Коэффициент', numeric: true },
  { key: 'charge', label: 'Начислено', numeric: true },
  { key: 'written_off', label: 'Списано', numeric: true },
  { key: 'debt', label: 'Долг', numeric: true },
  { key: 'remainder', label: 'Остаток', numeric: true },
];

const props = defineProps<{
  year: number | null;
  paymentTypeId: number | null;
}>();

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const loading = ref(false);
const mode = ref<'totals' | 'table' | null>(null);
const totalItems = ref<TotalItem[]>([]);
const rows = ref<SummaryRow[]>([]);
const filterDebt = ref(false);
const sortKey = ref<SortKey>('num_object');
const sortDir = ref<'asc' | 'desc'>('asc');

const formatDate = (value: string | null) => {
  if (!value) {
    return '—';
  }
  const [y, month, day] = value.split('-');
  if (!y || !month || !day) {
    return value;
  }
  return `${day}.${month}.${y}`;
};

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

const isAmountMissing = (value: string | null | undefined) => value == null || value === '';

const formatMissingZero = (value: string | null | undefined) => {
  if (isAmountMissing(value)) {
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
    return 'accounting-summary__remainder--zero';
  }
  return amount > 0 ? 'accounting-summary__remainder--plus' : 'accounting-summary__remainder--minus';
};

const debtClass = (value: string | null) => {
  if (value === null || value === undefined) {
    return null;
  }
  const amount = parseAmount(value);
  if (!Number.isFinite(amount) || amount <= 0.005) {
    return null;
  }
  return 'accounting-summary__debt';
};

const hasDebt = (row: SummaryRow) => {
  const amount = parseAmount(row.debt);
  return Number.isFinite(amount) && amount > 0.005;
};

const sortValue = (row: SummaryRow, key: SortKey) => {
  if (key === 'num_object') {
    return row.num_object == null ? Number.POSITIVE_INFINITY : row.num_object;
  }
  const amount = parseAmount(row[key]);
  return Number.isFinite(amount) ? amount : Number.NEGATIVE_INFINITY;
};

const visibleRows = computed(() => {
  let list = rows.value.slice();
  if (filterDebt.value) {
    list = list.filter((row) => hasDebt(row));
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

const toggleSort = (key: SortKey) => {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc';
    return;
  }
  sortKey.value = key;
  sortDir.value = 'asc';
};

const loadData = async () => {
  if (!props.year) {
    mode.value = null;
    totalItems.value = [];
    rows.value = [];
    return;
  }
  loading.value = true;
  await store.dispatch(actions.INC_LOADING);
  try {
    const { ok, message, result } = await api('gardening/get-accounting-summary', {
      year: props.year,
      payment_type_id: props.paymentTypeId,
    });
    if (ok === false) {
      root.$emit('msg', 'error', message || 'Не удалось загрузить сводку');
      mode.value = null;
      totalItems.value = [];
      rows.value = [];
      return;
    }
    mode.value = result?.mode || null;
    if (result?.mode === 'totals') {
      totalItems.value = Array.isArray(result.items) ? result.items : [];
      rows.value = [];
    } else if (result?.mode === 'table') {
      totalItems.value = [];
      rows.value = Array.isArray(result.rows) ? result.rows : [];
    } else {
      totalItems.value = [];
      rows.value = [];
    }
  } finally {
    loading.value = false;
    await store.dispatch(actions.DEC_LOADING);
  }
};

watch(
  () => [props.year, props.paymentTypeId],
  () => {
    loadData();
  },
  { immediate: true },
);
</script>

<style scoped lang="scss">
.accounting-summary {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: auto;
  background-color: #f8f7f7;
  color: #434A54;
}

.accounting-summary__toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  box-sizing: border-box;
  min-height: 34px;
  padding: 0 10px;
  border-bottom: 1px solid #b1b1b1;
  background-color: #ececec;
}

.accounting-summary__filter {
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

.accounting-summary__empty {
  padding: 10px;
  color: #666;
}

.accounting-summary__block {
  margin-bottom: 12px;
}

.accounting-summary__block-header {
  display: flex;
  align-items: center;
  gap: 12px;
  box-sizing: border-box;
  min-height: 34px;
  padding: 0 10px;
  border-bottom: 1px solid #b1b1b1;
  background-color: #aab2bd;
  color: #FFFFFF;
  font-weight: bold;
}

.accounting-summary__period {
  margin-left: auto;
  font-weight: normal;
}

.accounting-summary__sum {
  color: #000000;
  font-weight: bold;
  min-width: 90px;
  text-align: right;
}

.accounting-summary__body {
  overflow: auto;
  min-height: 0;
}

.accounting-summary__table {
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
}

.accounting-summary__num {
  text-align: right !important;
}

.accounting-summary__sorted {
  background-color: #dfe3e8 !important;
}

.accounting-summary__sort {
  margin-left: 4px;
  font-size: 10px;
}

.accounting-summary__missing,
.accounting-summary__debt {
  color: #c62828;
  font-weight: bold;
}

.accounting-summary__remainder--plus {
  color: #2e7d32;
  font-weight: bold;
}

.accounting-summary__remainder--minus {
  color: #c62828;
  font-weight: bold;
}

.accounting-summary__remainder--zero {
  font-weight: bold;
}
</style>
