<template>
  <div class="debts-list">
    <div
      v-if="year && paymentTypeId && !loading"
      class="debts-list__toolbar"
    >
      <div class="debts-list__print">
        <button
          class="btn btn-blue-nb btn-sm nbr debts-list__print-btn"
          type="button"
          title="Печать PDF"
          @click="printFile('pdf')"
        >
          PDF
        </button>
        <button
          class="btn btn-blue-nb btn-sm nbr debts-list__print-btn"
          type="button"
          title="Выгрузить Excel"
          @click="printFile('xlsx')"
        >
          Excel
        </button>
      </div>
    </div>
    <div
      v-if="!year || !paymentTypeId"
      class="debts-list__empty"
    >
      Выберите вид платежа
    </div>
    <div
      v-else-if="loading"
      class="debts-list__empty"
    >
      Загрузка…
    </div>
    <div
      v-else-if="visibleRows.length === 0"
      class="debts-list__empty"
    >
      Нет долгов
    </div>
    <div
      v-else
      class="debts-list__body"
    >
      <table class="debts-list__table">
        <thead>
          <tr>
            <th
              v-for="col in columns"
              :key="col.key"
              :class="{
                'debts-list__num': col.numeric,
                'debts-list__sorted': sortKey === col.key,
              }"
              @click="toggleSort(col.key)"
            >
              {{ col.label }}
              <span
                v-if="sortKey === col.key"
                class="debts-list__sort"
              >{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in visibleRows"
            :key="row.real_estate_id"
          >
            <td>
              <a
                class="a-under"
                :href="plotHref(row.real_estate_id)"
                target="_blank"
                rel="noopener"
              >{{ formatText(row.num_object) }}</a>
            </td>
            <td :title="row.owner || ''">
              {{ formatText(row.owner) }}
            </td>
            <td class="debts-list__num">
              {{ formatValue(row.charge) }}
            </td>
            <td class="debts-list__num">
              {{ formatValue(row.written_off) }}
            </td>
            <td
              class="debts-list__num"
              :class="debtClass(row.debt)"
            >
              {{ formatValue(row.debt) }}
            </td>
            <td
              class="debts-list__num"
              :class="remainderClass(row.remainder)"
            >
              {{ formatRemainder(row.remainder) }}
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
import { gardeningPlotHref, openGardeningAllPrint } from '@/pages/Gardening/plotUrl';

interface DebtRow {
  real_estate_id: number;
  num_object: number | null;
  owner: string;
  charge: string | null;
  written_off: string | null;
  debt: string | null;
  remainder: string | null;
}

type SortKey =
  | 'num_object'
  | 'owner'
  | 'charge'
  | 'written_off'
  | 'debt'
  | 'remainder';

const columns: { key: SortKey; label: string; numeric: boolean }[] = [
  { key: 'num_object', label: 'Участок', numeric: false },
  { key: 'owner', label: 'Владелец', numeric: false },
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
const rows = ref<DebtRow[]>([]);
const sortKey = ref<SortKey>('num_object');
const sortDir = ref<'asc' | 'desc'>('asc');

const plotHref = (realEstateId: number) => gardeningPlotHref(realEstateId, props.year);

const printFile = (format: 'pdf' | 'xlsx') => {
  if (!props.year || !props.paymentTypeId) {
    return;
  }
  openGardeningAllPrint(format, {
    year: props.year,
    payment_type_id: props.paymentTypeId,
    debts: true,
    sort_key: sortKey.value,
    sort_dir: sortDir.value,
  });
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
    return 'debts-list__remainder--zero';
  }
  return amount > 0 ? 'debts-list__remainder--plus' : 'debts-list__remainder--minus';
};

const debtClass = (value: string | null) => {
  if (value === null || value === undefined) {
    return null;
  }
  const amount = parseAmount(value);
  if (!Number.isFinite(amount) || amount <= 0.005) {
    return null;
  }
  return 'debts-list__debt';
};

const sortValue = (row: DebtRow, key: SortKey) => {
  if (key === 'num_object') {
    return row.num_object == null ? Number.POSITIVE_INFINITY : row.num_object;
  }
  if (key === 'owner') {
    return (row.owner || '').toLowerCase();
  }
  const amount = parseAmount(row[key]);
  return Number.isFinite(amount) ? amount : Number.NEGATIVE_INFINITY;
};

const visibleRows = computed(() => {
  const list = rows.value.slice();
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
  if (!props.year || !props.paymentTypeId) {
    rows.value = [];
    return;
  }
  loading.value = true;
  await store.dispatch(actions.INC_LOADING);
  try {
    const { ok, message, result } = await api('gardening/get-payment-type-debts', {
      year: props.year,
      payment_type_id: props.paymentTypeId,
    });
    if (ok === false) {
      root.$emit('msg', 'error', message || 'Не удалось загрузить долги');
      rows.value = [];
      return;
    }
    rows.value = Array.isArray(result?.rows) ? result.rows : [];
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
.debts-list {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: auto;
  background-color: #f8f7f7;
  color: #434A54;
}

.debts-list__toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  box-sizing: border-box;
  min-height: 34px;
  padding: 0 10px;
  border-bottom: 1px solid #b1b1b1;
  background-color: #ececec;
}

.debts-list__print {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
}

.debts-list__print-btn {
  height: 22px;
  min-height: 22px;
  max-height: 22px;
  padding: 0 8px;
  line-height: 20px;
  flex-shrink: 0;
}

.debts-list__empty {
  padding: 10px;
  color: #666;
}

.debts-list__body {
  overflow: auto;
  min-height: 0;
}

.debts-list__table {
  width: max-content;
  min-width: 0;
  border-collapse: collapse;
  table-layout: auto;

  th,
  td {
    box-sizing: border-box;
    height: 34px;
    padding: 0 14px;
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

.debts-list__num {
  text-align: right !important;
}

.debts-list__sorted {
  background-color: #dfe3e8 !important;
}

.debts-list__sort {
  margin-left: 4px;
  font-size: 10px;
}

.debts-list__debt {
  color: #c62828;
  font-weight: bold;
}

.debts-list__remainder--plus {
  color: #2e7d32;
  font-weight: bold;
}

.debts-list__remainder--minus {
  color: #c62828;
  font-weight: bold;
}

.debts-list__remainder--zero {
  font-weight: bold;
}
</style>
