<template>
  <div class="year-rates">
    <div class="year-rates__header">
      Виды платежей и тарифы за {{ year }}
    </div>
    <div
      v-if="rows.length === 0"
      class="year-rates__empty"
    >
      Нет видов платежей с тарифами за {{ year }}
    </div>
    <div
      v-for="item in rows"
      :key="item.id"
      class="year-rates__item"
    >
      <div class="year-rates__title">
        {{ item.title }}
      </div>
      <div
        v-for="rate in item.rates"
        :key="rate.id"
        class="year-rates__rate"
      >
        <span>{{ formatRatePeriod(rate) }}</span>
        <span>{{ rate.amount }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  onMounted,
  ref,
  watch,
} from 'vue';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';

interface PaymentTypeRate {
  id: number;
  date_start: string | null;
  date_end: string | null;
  amount: string;
}

interface PaymentTypeItem {
  id: number;
  title: string;
  rates: PaymentTypeRate[];
}

interface YearPaymentRow {
  id: number;
  title: string;
  rates: PaymentTypeRate[];
}

const props = defineProps<{
  year: number;
}>();

const store = useStore();
const paymentTypes = ref<PaymentTypeItem[]>([]);

const rateOverlapsYear = (rate: PaymentTypeRate, year: number) => {
  if (!rate.date_start || !rate.date_end) {
    return false;
  }
  const yearStart = `${year}-01-01`;
  const yearEnd = `${year}-12-31`;
  return rate.date_start <= yearEnd && rate.date_end >= yearStart;
};

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

const formatRatePeriod = (rate: PaymentTypeRate) => (
  `${formatDate(rate.date_start)} — ${formatDate(rate.date_end)}`
);

const rows = computed<YearPaymentRow[]>(() => (
  paymentTypes.value
    .map((item) => ({
      id: item.id,
      title: item.title,
      rates: (item.rates || []).filter((rate) => rateOverlapsYear(rate, props.year)),
    }))
    .filter((item) => item.rates.length > 0)
));

const loadPaymentTypes = async () => {
  await store.dispatch(actions.INC_LOADING);
  try {
    const { result } = await api('gardening/get-payment-types');
    paymentTypes.value = result || [];
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

onMounted(() => {
  loadPaymentTypes();
});

watch(() => props.year, () => {
  // rows recomputed from already loaded data; reload in case base changed
  loadPaymentTypes();
});
</script>

<style scoped lang="scss">
.year-rates {
  display: flex;
  flex-direction: column;
  width: 50%;
  max-width: 50%;
  height: 100%;
  min-height: 0;
  background-color: #f8f7f7;
}

.year-rates__header {
  box-sizing: border-box;
  height: 34px;
  min-height: 34px;
  padding: 0 10px;
  line-height: 34px;
  border-bottom: 1px solid #b1b1b1;
  color: #FFFFFF;
  font-weight: bold;
  background-color: #aab2bd;
  flex-shrink: 0;
}

.year-rates__empty {
  box-sizing: border-box;
  height: 34px;
  min-height: 34px;
  padding: 0 10px;
  line-height: 34px;
  color: #666;
}

.year-rates__item {
  border-bottom: 1px solid #b1b1b1;
}

.year-rates__title {
  box-sizing: border-box;
  height: 34px;
  min-height: 34px;
  padding: 0 10px;
  line-height: 34px;
  font-weight: bold;
  color: #434A54;
  background-color: #ececec;
  border-bottom: 1px solid #b1b1b1;
}

.year-rates__rate {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  box-sizing: border-box;
  height: 34px;
  min-height: 34px;
  padding: 0 10px;
  border-bottom: 1px solid #b1b1b1;
  color: #434A54;
  line-height: 34px;
}

.year-rates__rate:last-child {
  border-bottom: none;
}
</style>
