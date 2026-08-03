<template>
  <div class="accounting-summary">
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
    <template v-else-if="mode === 'table' && paymentType">
      <div class="accounting-summary__block">
        <div class="accounting-summary__block-header">
          <span>{{ paymentType.title }}</span>
          <span class="accounting-summary__period">
            {{ formatDate(paymentType.date_start) }} — {{ formatDate(paymentType.date_end) }}
          </span>
          <span class="accounting-summary__sum">{{ paymentType.receipts_total }}</span>
        </div>
        <table class="accounting-summary__table">
          <thead>
            <tr>
              <th>№ участка</th>
              <th>Приход</th>
              <th>Остаток</th>
              <th>Тариф</th>
              <th>Итого</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in rows"
              :key="row.real_estate_id"
            >
              <td>{{ row.num_object ?? '—' }}</td>
              <td class="accounting-summary__num">{{ row.receipt }}</td>
              <td class="accounting-summary__num">{{ row.balance }}</td>
              <td class="accounting-summary__num">{{ row.tariff }}</td>
              <td
                class="accounting-summary__num"
                :class="totalClass(row.total)"
              >
                {{ formatTotal(row.total) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
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

interface PaymentTypeInfo {
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
  receipt: string;
  balance: string;
  tariff: string;
  total: string | null;
}

const props = defineProps<{
  year: number | null;
  paymentTypeId: number | null;
}>();

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const loading = ref(false);
const mode = ref<'totals' | 'table' | null>(null);
const totalItems = ref<TotalItem[]>([]);
const paymentType = ref<PaymentTypeInfo | null>(null);
const rows = ref<SummaryRow[]>([]);

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

const formatTotal = (value: string | null) => {
  if (value === null || value === undefined) {
    return '—';
  }
  const amount = Number(String(value).replace(',', '.'));
  if (!Number.isFinite(amount)) {
    return value;
  }
  if (Math.abs(amount) < 0.005) {
    return '0.00';
  }
  const sign = amount > 0 ? '+' : '';
  return `${sign}${amount.toFixed(2)}`;
};

const totalClass = (value: string | null) => {
  if (value === null || value === undefined) {
    return null;
  }
  const amount = Number(String(value).replace(',', '.'));
  if (!Number.isFinite(amount) || Math.abs(amount) < 0.005) {
    return 'accounting-summary__total--zero';
  }
  return amount > 0 ? 'accounting-summary__total--plus' : 'accounting-summary__total--minus';
};

const loadData = async () => {
  if (!props.year) {
    mode.value = null;
    totalItems.value = [];
    paymentType.value = null;
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
      paymentType.value = null;
      rows.value = [];
      return;
    }
    mode.value = result?.mode || null;
    if (result?.mode === 'totals') {
      totalItems.value = Array.isArray(result.items) ? result.items : [];
      paymentType.value = null;
      rows.value = [];
    } else if (result?.mode === 'table') {
      totalItems.value = [];
      paymentType.value = result.payment_type || null;
      rows.value = Array.isArray(result.rows) ? result.rows : [];
    } else {
      totalItems.value = [];
      paymentType.value = null;
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

.accounting-summary__table {
  width: 100%;
  max-width: 900px;
  border-collapse: collapse;
  table-layout: fixed;

  th,
  td {
    box-sizing: border-box;
    height: 34px;
    padding: 0 8px;
    border-bottom: 1px solid #b1b1b1;
    text-align: left;
    vertical-align: middle;
  }

  th {
    font-weight: bold;
    background-color: #ececec;
  }
}

.accounting-summary__num {
  text-align: right !important;
  white-space: nowrap;
}

.accounting-summary__total--plus {
  color: #2e7d32;
  font-weight: bold;
}

.accounting-summary__total--minus {
  color: #c62828;
  font-weight: bold;
}

.accounting-summary__total--zero {
  font-weight: bold;
}
</style>
