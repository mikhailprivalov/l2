<template>
  <div class="contributions">
    <div class="contributions__header">
      <span class="contributions__header-title">Взносы</span>
    </div>

    <div
      v-if="!year"
      class="contributions__empty"
    >
      Выберите год
    </div>
    <div
      v-else-if="!rows.length"
      class="contributions__empty"
    >
      Нет взносов
    </div>
    <div
      v-else
      class="contributions__body"
    >
      <table class="contributions__table">
        <thead>
          <tr>
            <th class="contributions__col-title">
              Взнос
            </th>
            <th class="contributions__num">
              Тариф
            </th>
            <th class="contributions__num">
              Коэффициент
            </th>
            <th class="contributions__num">
              Начислено
            </th>
            <th class="contributions__num">
              Списано
            </th>
            <th class="contributions__num">
              Долг
            </th>
            <th class="contributions__num">
              Остаток
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in rows"
            :key="row.payment_type_id"
          >
            <td
              class="contributions__col-title"
              :title="row.title"
            >
              {{ row.title }}
            </td>
            <td
              class="contributions__num"
              :class="{ 'contributions__charge--missing': isAmountMissing(row.tariff) }"
            >
              {{ formatMissingZero(row.tariff) }}
            </td>
            <td
              class="contributions__num"
              :class="{ 'contributions__charge--missing': isAmountMissing(row.coefficient) }"
            >
              {{ formatMissingZero(row.coefficient) }}
            </td>
            <td
              class="contributions__num"
              :class="{ 'contributions__charge--missing': isAmountMissing(row.charge) }"
            >
              {{ formatMissingZero(row.charge) }}
            </td>
            <td class="contributions__num">
              {{ formatValue(row.written_off) }}
            </td>
            <td
              class="contributions__num"
              :class="debtClass(row.debt)"
            >
              {{ formatValue(row.debt) }}
            </td>
            <td
              class="contributions__num"
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
  getCurrentInstance,
  ref,
  watch,
} from 'vue';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';

interface ContributionRow {
  payment_type_id: number;
  title: string;
  tariff: string | null;
  coefficient: string | null;
  charge: string | null;
  written_off: string | null;
  debt: string | null;
  remainder: string | null;
}

const props = defineProps<{
  realEstateId: number;
  year: number | null;
}>();

const store = useStore();
const root = getCurrentInstance().proxy.$root;
const rows = ref<ContributionRow[]>([]);

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

const formatRemainder = (value: string | null) => {
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
  return amount.toFixed(2);
};

const remainderClass = (value: string | null) => {
  if (value === null || value === undefined) {
    return null;
  }
  const amount = Number(String(value).replace(',', '.'));
  if (!Number.isFinite(amount) || Math.abs(amount) < 0.005) {
    return 'contributions__remainder--zero';
  }
  return amount > 0 ? 'contributions__remainder--plus' : 'contributions__remainder--minus';
};

const debtClass = (value: string | null) => {
  if (value === null || value === undefined) {
    return null;
  }
  const amount = Number(String(value).replace(',', '.'));
  if (!Number.isFinite(amount) || amount <= 0.005) {
    return null;
  }
  return 'contributions__debt';
};

const loadData = async () => {
  if (!props.year || !props.realEstateId) {
    rows.value = [];
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    const { ok, message, result } = await api('gardening/get-plot-contributions', {
      real_estate_id: props.realEstateId,
      year: props.year,
    });
    if (ok === false) {
      root.$emit('msg', 'error', message || 'Не удалось загрузить взносы');
      rows.value = [];
      return;
    }
    rows.value = Array.isArray(result?.rows) ? result.rows : [];
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

watch(
  () => [props.realEstateId, props.year],
  () => {
    loadData();
  },
  { immediate: true },
);
</script>

<style scoped lang="scss">
.contributions {
  display: flex;
  flex-direction: column;
  width: auto;
  max-width: none;
  flex: 1 1 0;
  min-width: 0;
  height: auto;
  min-height: 0;
  background-color: #f8f7f7;
  border-bottom: none;
}

.contributions__header {
  display: flex;
  align-items: center;
  gap: 8px;
  box-sizing: border-box;
  height: 34px;
  min-height: 34px;
  padding: 0 10px;
  border-bottom: 1px solid #b1b1b1;
  color: #FFFFFF;
  font-weight: bold;
  background-color: #aab2bd;
  flex-shrink: 0;
}

.contributions__header-title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.contributions__empty {
  box-sizing: border-box;
  padding: 10px;
  color: #666;
}

.contributions__body {
  overflow: visible;
  min-height: 0;
}

.contributions__table {
  width: 100%;
  max-width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  color: #434A54;

  th,
  td {
    box-sizing: border-box;
    height: 34px;
    padding: 0 6px;
    border-bottom: 1px solid #b1b1b1;
    text-align: left;
    vertical-align: middle;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  th {
    font-weight: bold;
    background-color: #ececec;
  }
}

.contributions__col-title {
  width: auto;
}

.contributions__num {
  width: 13%;
  text-align: right !important;
}

.contributions__remainder--plus {
  color: #2e7d32;
  font-weight: bold;
}

.contributions__remainder--minus {
  color: #c62828;
  font-weight: bold;
}

.contributions__remainder--zero {
  font-weight: bold;
}

.contributions__debt,
.contributions__charge--missing {
  color: #c62828;
  font-weight: bold;
}
</style>
