<template>
  <div class="base-settings">
    <div class="base-settings__nav">
      <div class="base-section">
        <span>Виды платежей</span>
        <button
          class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
          type="button"
          title="Добавить"
          @click="openCreate"
        >
          <i class="fa fa-plus" />
        </button>
      </div>
      <div class="base-settings__list">
        <div
          v-if="paymentTypes.length === 0"
          class="payment-types-empty"
        >
          Нет записей
        </div>
        <div
          v-for="item in paymentTypes"
          :key="item.id"
          class="payment-type-row"
          :class="{ 'payment-type-row--active': selectedPaymentTypeId === item.id }"
          @click="selectPaymentType(item)"
        >
          <span class="payment-type-row__title">{{ item.title }}</span>
        </div>
      </div>
    </div>

    <div class="base-settings__detail">
      <template v-if="selectedPaymentTypeId !== null">
        <div class="detail-body">
          <div
            class="detail-row"
            :class="{ 'detail-row--error': !editTitle }"
          >
            <span class="detail-label">Название</span>
            <input
              v-model.trim="editTitle"
              class="form-control detail-input"
              type="text"
            >
          </div>
          <div
            class="detail-row detail-row--mode"
            :class="{ 'detail-row--error': !editMode }"
          >
            <span class="detail-label">Способ расчёта</span>
            <Treeselect
              v-model="editMode"
              :multiple="false"
              :disable-branch-nodes="true"
              :options="modeOptions"
              placeholder="Выберите…"
              :clearable="true"
              :append-to-body="true"
              class="treeselect-wide treeselect-34px treeselect-noborder detail-mode-select"
            />
          </div>
          <div
            class="detail-row detail-row--payment"
            :class="{ 'detail-row--error': !editPeriod }"
          >
            <span class="detail-label">Способ оплаты</span>
            <Treeselect
              v-model="editPeriod"
              :multiple="false"
              :disable-branch-nodes="true"
              :options="periodOptions"
              placeholder="Период…"
              :clearable="true"
              :append-to-body="true"
              class="treeselect-wide treeselect-34px treeselect-noborder detail-period-select"
            />
          </div>
          <div
            class="detail-row detail-row--payment"
            :class="{ 'detail-row--error': !isEditPaymentDueValid }"
          >
            <span class="detail-label">Срок оплаты</span>
            <div class="detail-payment-fields">
              <template v-if="editPeriod === 'year'">
                <Treeselect
                  v-model="editPaymentDay"
                  :multiple="false"
                  :disable-branch-nodes="true"
                  :options="dayOptions"
                  placeholder="ДЕНЬ"
                  :clearable="true"
                  :append-to-body="true"
                  class="treeselect-wide treeselect-34px treeselect-noborder detail-md-select"
                />
                <Treeselect
                  v-model="editPaymentMonth"
                  :multiple="false"
                  :disable-branch-nodes="true"
                  :options="monthOptions"
                  placeholder="МЕСЯЦ"
                  :clearable="true"
                  :append-to-body="true"
                  class="treeselect-wide treeselect-34px treeselect-noborder detail-md-select"
                />
                <span
                  v-if="editYearDueText"
                  class="detail-payment-hint"
                >{{ editYearDueText }}</span>
              </template>
              <template v-else-if="editPeriod === 'month'">
                <Treeselect
                  v-model="editPaymentDay"
                  :multiple="false"
                  :disable-branch-nodes="true"
                  :options="dayOptions"
                  placeholder="ЧИСЛО"
                  :clearable="true"
                  :append-to-body="true"
                  class="treeselect-wide treeselect-34px treeselect-noborder detail-md-select"
                />
                <span class="detail-payment-hint">след. за расч. период</span>
              </template>
            </div>
          </div>
          <div class="detail-row detail-row--block">
            <div class="detail-rates-header">
              <span class="detail-label">Тарифы</span>
            </div>
            <div class="detail-rates">
              <div
                v-for="rate in (selectedPaymentType && selectedPaymentType.rates) || []"
                :key="rate.id"
                class="detail-rate-row"
              >
                <template v-if="editingRateId === rate.id">
                  <input
                    v-model="editRateDateStart"
                    class="form-control rate-field rate-field--date"
                    type="date"
                    :disabled="savingRate"
                  >
                  <input
                    v-model="editRateDateEnd"
                    class="form-control rate-field rate-field--date"
                    type="date"
                    :disabled="savingRate"
                  >
                  <input
                    v-model="editRateAmount"
                    class="form-control rate-field rate-field--amount"
                    type="number"
                    min="0"
                    step="0.01"
                    :disabled="savingRate"
                  >
                  <button
                    class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                    type="button"
                    title="Сохранить"
                    :disabled="savingRate"
                    @click="saveEditRate"
                  >
                    <i class="fa fa-save" />
                  </button>
                  <button
                    class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                    type="button"
                    title="Удалить"
                    :disabled="savingRate"
                    @click="deleteEditRate"
                  >
                    <i class="fa fa-times" />
                  </button>
                </template>
                <template v-else>
                  <span class="detail-rate-row__period">{{ formatRatePeriod(rate) }}</span>
                  <span class="detail-rate-row__amount">{{ rate.amount }}</span>
                  <button
                    class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                    type="button"
                    title="Редактировать"
                    :disabled="savingRate || editingRateId !== null || creatingRate"
                    @click="startEditRate(rate)"
                  >
                    <i class="fa fa-pencil" />
                  </button>
                </template>
              </div>
              <div
                v-if="creatingRate"
                class="detail-rate-row detail-rate-row--form"
              >
                <input
                  v-model="rateFormDateStart"
                  class="form-control rate-field rate-field--date"
                  type="date"
                  :disabled="savingRate"
                >
                <input
                  v-model="rateFormDateEnd"
                  class="form-control rate-field rate-field--date"
                  type="date"
                  :disabled="savingRate"
                >
                <input
                  v-model="rateFormAmount"
                  class="form-control rate-field rate-field--amount"
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="тариф"
                  :disabled="savingRate"
                >
                <button
                  class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                  type="button"
                  title="Сохранить"
                  :disabled="savingRate"
                  @click="saveCreateRate"
                >
                  <i class="fa fa-save" />
                </button>
                <button
                  class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                  type="button"
                  title="Отмена"
                  :disabled="savingRate"
                  @click="cancelCreateRate"
                >
                  <i class="fa fa-times" />
                </button>
              </div>
              <div
                v-else
                class="detail-rate-row detail-rate-row--add"
              >
                <button
                  class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                  type="button"
                  title="Добавить тариф"
                  :disabled="savingRate || editingRateId !== null"
                  @click="openCreateRate"
                >
                  <i class="fa fa-plus" />
                </button>
              </div>
            </div>
          </div>
          <div class="detail-row detail-row--actions">
            <button
              class="btn btn-blue-nb nbr detail-save-btn"
              type="button"
              :disabled="saving || !editTitle || !editMode || !isEditPaymentValid"
              @click="saveSelected"
            >
              Сохранить
            </button>
          </div>
        </div>
      </template>
      <div
        v-else
        class="detail-placeholder"
      >
        Выберите вид платежа
      </div>
    </div>

    <MountingPortal
      mount-to="#portal-place-modal"
      name="GardeningPaymentTypeModal"
      append
    >
      <transition name="fade">
        <Modal
          v-if="modalOpen"
          show-footer="true"
          white-bg="true"
          max-width="520px"
          width="100%"
          margin-left-right="auto"
          @close="closeModal"
        >
          <span slot="header">Добавить вид платежа</span>
          <div
            slot="body"
            class="modal-body-form"
          >
            <div class="form-group">
              <label>Название</label>
              <input
                v-model="formTitle"
                class="form-control"
                :class="{ 'has-error-field': !formTitle }"
                type="text"
              >
            </div>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-6" />
              <div class="col-xs-3">
                <button
                  class="btn btn-primary-nb btn-blue-nb"
                  type="button"
                  :disabled="saving || !formTitle"
                  @click="saveCreate"
                >
                  Сохранить
                </button>
              </div>
              <div class="col-xs-3">
                <button
                  class="btn btn-primary-nb btn-blue-nb"
                  type="button"
                  :disabled="saving"
                  @click="closeModal"
                >
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        </Modal>
      </transition>
    </MountingPortal>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  getCurrentInstance,
  onMounted,
  ref,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';
import Modal from '@/ui-cards/Modal.vue';

type CalcMode = 'absolute' | 'by_area' | 'kilowatt';
type PeriodType = 'year' | 'month';

interface PaymentTypeRate {
  id: number;
  date_start: string | null;
  date_end: string | null;
  amount: string;
}

interface PaymentTypeItem {
  id: number;
  title: string;
  is_absolute: boolean;
  is_by_area: boolean;
  is_use_kilowatt: boolean;
  period: PeriodType | null;
  payment_date: string | null;
  payment_day: number | null;
  rates: PaymentTypeRate[];
}

const modeOptions = [
  { id: 'absolute', label: 'Абсолютная сумма' },
  { id: 'by_area', label: 'Площадь участка' },
  { id: 'kilowatt', label: 'кВт энергии' },
];

const periodOptions = [
  { id: 'year', label: '1 раз в год' },
  { id: 'month', label: '1 раз в месяц' },
];

const monthOptions = Array.from({ length: 12 }, (_, i) => {
  const value = i + 1;
  return { id: value, label: String(value).padStart(2, '0') };
});

const dayOptions = Array.from({ length: 31 }, (_, i) => {
  const value = i + 1;
  return { id: value, label: String(value).padStart(2, '0') };
});

const MONTH_NAMES_GENITIVE = [
  'января',
  'февраля',
  'марта',
  'апреля',
  'мая',
  'июня',
  'июля',
  'августа',
  'сентября',
  'октября',
  'ноября',
  'декабря',
];

const PAYMENT_DATE_YEAR = 2000;

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const paymentTypes = ref<PaymentTypeItem[]>([]);
const selectedPaymentTypeId = ref<number | null>(null);
const modalOpen = ref(false);
const formTitle = ref('');
const editTitle = ref('');
const editMode = ref<CalcMode | null>(null);
const editPeriod = ref<PeriodType | null>(null);
const editPaymentMonth = ref<number | null>(null);
const editPaymentDay = ref<number | null>(null);
const saving = ref(false);
const rateFormDateStart = ref('');
const rateFormDateEnd = ref('');
const rateFormAmount = ref('');
const savingRate = ref(false);
const creatingRate = ref(false);
const editingRateId = ref<number | null>(null);
const editRateDateStart = ref('');
const editRateDateEnd = ref('');
const editRateAmount = ref('');

const selectedPaymentType = computed(() => (
  paymentTypes.value.find((item) => item.id === selectedPaymentTypeId.value) || null
));

const isPaymentDayValid = (value: number | null) => (
  value != null && Number.isInteger(value) && value >= 1 && value <= 31
);

const isYearDueValid = (month: number | null, day: number | null) => {
  if (month == null || day == null || month < 1 || month > 12 || !isPaymentDayValid(day)) {
    return false;
  }
  const date = new Date(PAYMENT_DATE_YEAR, month - 1, day);
  return date.getFullYear() === PAYMENT_DATE_YEAR && date.getMonth() === month - 1 && date.getDate() === day;
};

const formatYearDueText = (month: number | null, day: number | null) => {
  if (!isYearDueValid(month, day)) {
    return '';
  }
  const dayText = String(day).padStart(2, '0');
  const monthText = MONTH_NAMES_GENITIVE[month - 1];
  return `до ${dayText} ${monthText}`;
};

const buildPaymentDate = (month: number, day: number) => (
  `${PAYMENT_DATE_YEAR}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
);

const parsePaymentDateParts = (value: string | null) => {
  if (!value) {
    return { month: null as number | null, day: null as number | null };
  }
  const parts = value.split('-');
  if (parts.length < 3) {
    return { month: null, day: null };
  }
  const month = Number(parts[1]);
  const day = Number(parts[2]);
  return {
    month: Number.isInteger(month) ? month : null,
    day: Number.isInteger(day) ? day : null,
  };
};

const isEditPaymentDueValid = computed(() => {
  if (editPeriod.value === 'year') {
    return isYearDueValid(editPaymentMonth.value, editPaymentDay.value);
  }
  if (editPeriod.value === 'month') {
    return isPaymentDayValid(editPaymentDay.value);
  }
  return false;
});

const isEditPaymentValid = computed(() => (
  Boolean(editPeriod.value) && isEditPaymentDueValid.value
));

const editYearDueText = computed(() => (
  formatYearDueText(editPaymentMonth.value, editPaymentDay.value)
));

const paymentPayload = (
  period: PeriodType,
  paymentMonth: number | null,
  paymentDay: number | null,
) => ({
  period,
  payment_date: period === 'year' && paymentMonth != null && paymentDay != null
    ? buildPaymentDate(paymentMonth, paymentDay)
    : null,
  payment_day: period === 'month' ? paymentDay : null,
});

const modeFromItem = (item: PaymentTypeItem): CalcMode | null => {
  if (item.is_use_kilowatt) {
    return 'kilowatt';
  }
  if (item.is_by_area) {
    return 'by_area';
  }
  if (item.is_absolute) {
    return 'absolute';
  }
  return null;
};

const modeFlags = (mode: CalcMode) => ({
  is_absolute: mode === 'absolute',
  is_by_area: mode === 'by_area',
  is_use_kilowatt: mode === 'kilowatt',
});

const formatDate = (value: string | null) => {
  if (!value) {
    return '—';
  }
  const [year, month, day] = value.split('-');
  if (!year || !month || !day) {
    return value;
  }
  return `${day}.${month}.${year}`;
};

const formatRatePeriod = (rate: PaymentTypeRate) => (
  `${formatDate(rate.date_start)} — ${formatDate(rate.date_end)}`
);

const fillEditForm = (item: PaymentTypeItem) => {
  editTitle.value = item.title;
  editMode.value = modeFromItem(item);
  editPeriod.value = item.period || null;
  if (item.period === 'year') {
    const parts = parsePaymentDateParts(item.payment_date);
    editPaymentMonth.value = parts.month;
    editPaymentDay.value = parts.day;
  } else {
    editPaymentMonth.value = null;
    editPaymentDay.value = item.payment_day != null ? item.payment_day : null;
  }
};

const resetRateForm = () => {
  rateFormDateStart.value = '';
  rateFormDateEnd.value = '';
  rateFormAmount.value = '';
};

const cancelCreateRate = () => {
  creatingRate.value = false;
  resetRateForm();
};

const cancelEditRate = () => {
  editingRateId.value = null;
  editRateDateStart.value = '';
  editRateDateEnd.value = '';
  editRateAmount.value = '';
};

const openCreateRate = () => {
  if (editingRateId.value !== null) {
    return;
  }
  cancelEditRate();
  resetRateForm();
  creatingRate.value = true;
};

const selectPaymentType = (item: PaymentTypeItem) => {
  selectedPaymentTypeId.value = item.id;
  fillEditForm(item);
  cancelEditRate();
  cancelCreateRate();
};

const loadPaymentTypes = async () => {
  await store.dispatch(actions.INC_LOADING);
  try {
    const { result } = await api('gardening/get-payment-types');
    paymentTypes.value = result || [];
    if (selectedPaymentTypeId.value !== null) {
      const selected = paymentTypes.value.find((item) => item.id === selectedPaymentTypeId.value);
      if (selected) {
        fillEditForm(selected);
      } else {
        selectedPaymentTypeId.value = null;
      }
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const resetCreateForm = () => {
  formTitle.value = '';
};

const openCreate = () => {
  resetCreateForm();
  modalOpen.value = true;
};

const closeModal = () => {
  modalOpen.value = false;
  resetCreateForm();
};

const ratesOverlapLocal = (dateStart: string, dateEnd: string, excludeId: number | null = null) => {
  const rates = selectedPaymentType.value?.rates || [];
  return rates.some((rate) => {
    if (excludeId !== null && rate.id === excludeId) {
      return false;
    }
    if (!rate.date_start || !rate.date_end) {
      return false;
    }
    return dateStart <= rate.date_end && rate.date_start <= dateEnd;
  });
};

const startEditRate = (rate: PaymentTypeRate) => {
  cancelCreateRate();
  editingRateId.value = rate.id;
  editRateDateStart.value = rate.date_start || '';
  editRateDateEnd.value = rate.date_end || '';
  editRateAmount.value = rate.amount || '';
};

const validateRateFields = (dateStart: string, dateEnd: string, amount: string, excludeId: number | null = null) => {
  if (!dateStart || !dateEnd) {
    return 'Укажите даты начала и окончания';
  }
  if (dateStart > dateEnd) {
    return 'Дата начала не может быть позже даты окончания';
  }
  if (amount === '' || amount === null) {
    return 'Укажите тариф';
  }
  if (ratesOverlapLocal(dateStart, dateEnd, excludeId)) {
    return 'Период пересекается с другим тарифом этого вида платежа';
  }
  return null;
};

const applyPaymentTypeResult = (result: PaymentTypeItem | undefined) => {
  if (result?.id) {
    selectedPaymentTypeId.value = result.id;
    fillEditForm(result);
  }
};

const saveCreateRate = async () => {
  if (savingRate.value || selectedPaymentTypeId.value === null || !creatingRate.value) {
    return;
  }
  const error = validateRateFields(rateFormDateStart.value, rateFormDateEnd.value, rateFormAmount.value);
  if (error) {
    root.$emit('msg', 'error', error);
    return;
  }

  savingRate.value = true;
  await store.dispatch(actions.INC_LOADING);
  try {
    const { ok, message, result } = await api('gardening/create-payment-type-rate', {
      payment_type_id: selectedPaymentTypeId.value,
      date_start: rateFormDateStart.value,
      date_end: rateFormDateEnd.value,
      amount: rateFormAmount.value,
    });
    if (!ok) {
      root.$emit('msg', 'error', message || 'Не удалось сохранить тариф');
      return;
    }
    root.$emit('msg', 'ok', 'Тариф сохранён');
    cancelCreateRate();
    await loadPaymentTypes();
    applyPaymentTypeResult(result);
  } finally {
    savingRate.value = false;
    await store.dispatch(actions.DEC_LOADING);
  }
};

const saveEditRate = async () => {
  if (savingRate.value || editingRateId.value === null) {
    return;
  }
  const error = validateRateFields(
    editRateDateStart.value,
    editRateDateEnd.value,
    editRateAmount.value,
    editingRateId.value,
  );
  if (error) {
    root.$emit('msg', 'error', error);
    return;
  }

  savingRate.value = true;
  await store.dispatch(actions.INC_LOADING);
  try {
    const { ok, message, result } = await api('gardening/update-payment-type-rate', {
      id: editingRateId.value,
      date_start: editRateDateStart.value,
      date_end: editRateDateEnd.value,
      amount: editRateAmount.value,
    });
    if (!ok) {
      root.$emit('msg', 'error', message || 'Не удалось сохранить тариф');
      return;
    }
    root.$emit('msg', 'ok', 'Тариф сохранён');
    cancelEditRate();
    await loadPaymentTypes();
    applyPaymentTypeResult(result);
  } finally {
    savingRate.value = false;
    await store.dispatch(actions.DEC_LOADING);
  }
};

const deleteEditRate = async () => {
  if (savingRate.value || editingRateId.value === null) {
    return;
  }
  try {
    await root.$dialog.confirm('Удалить тариф?');
  } catch (_) {
    return;
  }

  savingRate.value = true;
  await store.dispatch(actions.INC_LOADING);
  try {
    const { ok, message, result } = await api('gardening/delete-payment-type-rate', {
      id: editingRateId.value,
    });
    if (!ok) {
      root.$emit('msg', 'error', message || 'Не удалось удалить тариф');
      return;
    }
    root.$emit('msg', 'ok', 'Тариф удалён');
    cancelEditRate();
    await loadPaymentTypes();
    applyPaymentTypeResult(result);
  } finally {
    savingRate.value = false;
    await store.dispatch(actions.DEC_LOADING);
  }
};

const saveCreate = async () => {
  if (saving.value) {
    return;
  }
  if (!formTitle.value) {
    root.$emit('msg', 'error', 'Укажите название');
    return;
  }
  saving.value = true;
  await store.dispatch(actions.INC_LOADING);
  try {
    const { ok, message, result } = await api('gardening/create-payment-type', {
      title: formTitle.value,
    });
    if (!ok) {
      root.$emit('msg', 'error', message || 'Не удалось сохранить');
      return;
    }
    root.$emit('msg', 'ok', 'Сохранено');
    closeModal();
    await loadPaymentTypes();
    if (result?.id) {
      selectedPaymentTypeId.value = result.id;
      fillEditForm(result);
    }
  } finally {
    saving.value = false;
    await store.dispatch(actions.DEC_LOADING);
  }
};

const saveSelected = async () => {
  if (saving.value || selectedPaymentTypeId.value === null) {
    return;
  }
  if (!editTitle.value) {
    root.$emit('msg', 'error', 'Укажите название');
    return;
  }
  if (!editMode.value) {
    root.$emit('msg', 'error', 'Укажите способ расчёта');
    return;
  }
  if (!editPeriod.value) {
    root.$emit('msg', 'error', 'Укажите период учета');
    return;
  }
  if (!isEditPaymentValid.value) {
    root.$emit('msg', 'error', editPeriod.value === 'month' ? 'Укажите день оплаты (1–31)' : 'Укажите дату оплаты');
    return;
  }
  saving.value = true;
  await store.dispatch(actions.INC_LOADING);
  try {
    const { ok, message, result } = await api('gardening/update-payment-type', {
      id: selectedPaymentTypeId.value,
      title: editTitle.value,
      ...modeFlags(editMode.value),
      ...paymentPayload(editPeriod.value, editPaymentMonth.value, editPaymentDay.value),
    });
    if (!ok) {
      root.$emit('msg', 'error', message || 'Не удалось сохранить');
      return;
    }
    root.$emit('msg', 'ok', 'Сохранено');
    await loadPaymentTypes();
    if (result?.id) {
      selectedPaymentTypeId.value = result.id;
      fillEditForm(result);
    }
  } finally {
    saving.value = false;
    await store.dispatch(actions.DEC_LOADING);
  }
};

onMounted(() => {
  loadPaymentTypes();
});
</script>

<style scoped lang="scss">
.base-settings {
  display: flex;
  flex-direction: row;
  width: 100%;
  height: 100%;
  min-height: 0;
  background-color: #f8f7f7;
}

.base-settings__nav {
  display: flex;
  flex-direction: column;
  width: 42%;
  min-width: 280px;
  max-width: 480px;
  height: 100%;
  min-height: 0;
  border-right: 1px solid #b1b1b1;
  flex-shrink: 0;
}

.base-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  box-sizing: border-box;
  height: 34px;
  min-height: 34px;
  max-height: 34px;
  padding: 0 10px;
  border-bottom: 1px solid #b1b1b1;
  color: #434A54;
  background-color: #aab2bd;
  flex-shrink: 0;
}

.base-section span {
  color: #FFFFFF;
  line-height: 34px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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

.base-settings__list {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.payment-types-empty {
  box-sizing: border-box;
  height: 34px;
  min-height: 34px;
  padding: 0 10px;
  line-height: 34px;
  color: #666;
}

.payment-type-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  box-sizing: border-box;
  width: 100%;
  height: 34px;
  min-height: 34px;
  max-height: 34px;
  padding: 0 10px;
  border: none;
  border-bottom: 1px solid #b1b1b1;
  border-radius: 0;
  background-color: transparent;
  color: #434A54;
  cursor: pointer;
}

.payment-type-row:hover {
  background-color: #434a54;
  color: #FFFFFF;
}

.payment-type-row--active,
.payment-type-row--active:hover {
  background-color: #049372;
  color: #FFFFFF;
}

.payment-type-row__title {
  flex: 1;
  min-width: 0;
  line-height: 34px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.base-settings__detail {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.detail-body {
  padding: 0;
}

.detail-row {
  display: flex;
  align-items: center;
  gap: 12px;
  box-sizing: border-box;
  height: 34px;
  min-height: 34px;
  max-height: 34px;
  padding: 0 10px;
  border-bottom: 1px solid #b1b1b1;
  color: #434A54;
  overflow: hidden;
}

.detail-row--block {
  height: auto;
  min-height: 34px;
  max-height: none;
  flex-direction: column;
  align-items: stretch;
  gap: 0;
  padding: 0;
}

.detail-row--block > .detail-label,
.detail-row--block > .detail-rates-header {
  box-sizing: border-box;
  height: 34px;
  min-height: 34px;
  max-height: 34px;
  padding: 0 10px;
  line-height: 34px;
  border-bottom: 1px solid #b1b1b1;
}

.detail-row--actions {
  justify-content: flex-start;
  padding-left: 0;
}

.detail-row--error {
  border-bottom-color: #f00;
}

.detail-label {
  flex: 0 0 180px;
  color: #666;
  font-weight: bold;
  line-height: 34px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-value {
  flex: 1;
  min-width: 0;
  line-height: 34px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-value--padded {
  padding: 0 10px;
}

.detail-input {
  flex: 1;
  min-width: 0;
  height: 28px !important;
  border: none !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  background: transparent;
  padding: 2px 8px;
}

.detail-row--mode {
  overflow: visible;
}

.detail-row--payment {
  overflow: visible;
}

.detail-mode-select {
  flex: 0 0 25%;
  width: 25%;
  max-width: 25%;
  min-width: 0;
}

.detail-mode-select :deep(.vue-treeselect__control) {
  border: none !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  background: transparent;
}

.detail-payment-fields {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.detail-period-select {
  flex: 0 0 25%;
  width: 25%;
  max-width: 25%;
  min-width: 0;
}

.detail-period-select :deep(.vue-treeselect__control) {
  border: none !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  background: transparent;
}

.detail-md-select {
  flex: 0 0 88px;
  width: 88px;
  max-width: 88px;
  min-width: 0;
}

.detail-md-select :deep(.vue-treeselect__control) {
  border: none !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  background: transparent;
}

.detail-payment-hint {
  flex-shrink: 0;
  margin-left: 8px;
  color: #666;
  white-space: nowrap;
}

.detail-save-btn {
  height: 28px;
  padding: 0 12px;
  border-radius: 0;
}

.detail-rates-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
}

.detail-rates-header .detail-label {
  flex: 1;
  min-width: 0;
  padding: 0;
  border-bottom: none;
}

.detail-rates {
  width: 50%;
  max-width: 50%;
}

.detail-rate-row {
  display: flex;
  align-items: center;
  gap: 8px;
  box-sizing: border-box;
  min-height: 34px;
  padding: 3px 10px;
  border-bottom: 1px solid #b1b1b1;
  line-height: 28px;
}

.detail-rate-row__period {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-rate-row__amount {
  flex: 0 0 90px;
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-rate-row--form {
  background-color: #f3f3f3;
}

.detail-rate-row--add {
  justify-content: flex-end;
  background-color: transparent;
  border-bottom: none;
}

.rate-field {
  height: 28px !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  padding: 2px 6px;
}

.rate-field--date {
  flex: 1;
  min-width: 0;
}

.rate-field--amount {
  flex: 0 0 100px;
}

.detail-placeholder {
  box-sizing: border-box;
  height: 34px;
  min-height: 34px;
  padding: 0 10px;
  line-height: 34px;
  color: #666;
}

.modal-body-form {
  padding: 10px 0;
}

.modal-body-form .form-group {
  margin-bottom: 12px;
}

.modal-body-form label {
  display: block;
  margin-bottom: 6px;
  font-weight: 600;
}
</style>
