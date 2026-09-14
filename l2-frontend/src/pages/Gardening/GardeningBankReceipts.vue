<template>
  <div class="bank-receipts">
    <div class="bank-receipts__header">
      <span class="bank-receipts__header-title">
        Приход (Банк)
      </span>
      <span
        class="bank-receipts__date"
        aria-hidden="true"
      />
      <span
        class="bank-receipts__type"
        aria-hidden="true"
      />
      <span class="bank-receipts__amount bank-receipts__total">
        {{ receiptsTotal || '' }}
      </span>
      <span class="bank-receipts__comment" />
      <span
        class="toolbar-icon-btn bank-receipts__header-spacer"
        aria-hidden="true"
      />
      <span
        class="toolbar-icon-btn bank-receipts__header-spacer"
        aria-hidden="true"
      />
    </div>

    <div
      v-if="!year"
      class="bank-receipts__empty"
    >
      Выберите год
    </div>
    <template v-else>
      <div class="bank-receipts__list">
        <div
          v-if="receipts.length === 0 && !creatingRoot"
          class="bank-receipts__empty"
        >
          Нет поступлений
        </div>

        <div
          v-for="item in receipts"
          :key="item.id"
          class="bank-receipts__group"
        >
        <div
          class="bank-receipts__row"
          :class="{ 'bank-receipts__row--parent': item.not_control }"
        >
          <template v-if="editingId === item.id && editingParentId === null">
            <input
              v-model="formDate"
              class="form-control bank-field bank-field--date"
              type="date"
              :disabled="saving"
            >
            <Treeselect
              v-model="formPaymentTypeId"
              :multiple="false"
              :disable-branch-nodes="true"
              :options="paymentTypeOptions"
              placeholder="Вид платежа…"
              :clearable="true"
              :append-to-body="true"
              :disabled="saving"
              class="treeselect-wide treeselect-34px treeselect-noborder bank-field--type"
            />
            <input
              v-model="formAmount"
              class="form-control bank-field bank-field--amount"
              type="number"
              min="0"
              step="0.01"
              :disabled="saving"
            >
            <input
              v-model.trim="formComment"
              class="form-control bank-field bank-field--comment"
              type="text"
              placeholder="Комментарий"
              :disabled="saving"
            >
            <button
              class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
              type="button"
              title="Сохранить"
              :disabled="saving || !canSave"
              @click="saveEdit"
            >
              <i class="fa fa-save" />
            </button>
            <button
              class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
              type="button"
              title="Удалить"
              :disabled="saving"
              @click="removeItem(item)"
            >
              <i class="fa fa-minus" />
            </button>
          </template>
          <template v-else>
            <span class="bank-receipts__date">{{ formatDate(item.date) }}</span>
            <span
              class="bank-receipts__type"
              :title="item.payment_type_title"
            >{{ item.payment_type_title || '—' }}</span>
            <span
              class="bank-receipts__amount"
              :class="parentAmountClass(item)"
            >{{ formatParentAmount(item) }}</span>
            <span
              class="bank-receipts__comment"
              :title="item.comment"
            >{{ item.comment }}</span>
            <button
              class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
              type="button"
              title="Редактировать"
              :disabled="isBusy"
              @click="startEditRoot(item)"
            >
              <i class="fa fa-pencil" />
            </button>
            <button
              class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
              type="button"
              title="Удалить"
              :disabled="isBusy"
              @click="removeItem(item)"
            >
              <i class="fa fa-minus" />
            </button>
          </template>
        </div>

        <template v-if="item.not_control">
          <div
            v-for="child in (item.parent_pay_receipt || [])"
            :key="`child-${child.id}`"
            class="bank-receipts__row bank-receipts__row--child"
          >
            <template v-if="editingId === child.id && editingParentId === item.id">
              <input
                v-model="formDate"
                class="form-control bank-field bank-field--date"
                type="date"
                :disabled="saving"
              >
              <Treeselect
                v-model="formPaymentTypeId"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="paymentTypeAllocOptions"
                placeholder="Вид платежа…"
                :clearable="true"
                :append-to-body="true"
                :disabled="saving"
                class="treeselect-wide treeselect-34px treeselect-noborder bank-field--type"
              />
              <input
                v-model="formAmount"
                class="form-control bank-field bank-field--amount"
                type="number"
                min="0"
                step="0.01"
                :disabled="saving"
              >
              <input
                v-model.trim="formComment"
                class="form-control bank-field bank-field--comment"
                type="text"
                placeholder="Комментарий"
                :disabled="saving"
              >
              <button
                class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                type="button"
                title="Сохранить"
                :disabled="saving || !canSave"
                @click="saveEdit"
              >
                <i class="fa fa-save" />
              </button>
              <button
                class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                type="button"
                title="Удалить"
                :disabled="saving"
                @click="removeItem(child)"
              >
                <i class="fa fa-minus" />
              </button>
            </template>
            <template v-else>
              <span class="bank-receipts__date">{{ formatDate(child.date) }}</span>
              <span
                class="bank-receipts__type"
                :title="child.payment_type_title"
              >{{ child.payment_type_title || '—' }}</span>
              <span class="bank-receipts__amount">{{ child.amount }}</span>
              <span
                class="bank-receipts__comment"
                :title="child.comment"
              >{{ child.comment }}</span>
              <button
                class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                type="button"
                title="Редактировать"
                :disabled="isBusy"
                @click="startEditChild(item, child)"
              >
                <i class="fa fa-pencil" />
              </button>
              <button
                class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                type="button"
                title="Удалить"
                :disabled="isBusy"
                @click="removeItem(child)"
              >
                <i class="fa fa-minus" />
              </button>
            </template>
          </div>

          <div
            v-if="creatingParentId === item.id"
            class="bank-receipts__row bank-receipts__row--child bank-receipts__row--form"
          >
            <input
              v-model="formDate"
              class="form-control bank-field bank-field--date"
              type="date"
              :disabled="saving"
            >
            <Treeselect
              v-model="formPaymentTypeId"
              :multiple="false"
              :disable-branch-nodes="true"
              :options="paymentTypeAllocOptions"
              placeholder="Вид платежа…"
              :clearable="true"
              :append-to-body="true"
              :disabled="saving"
              class="treeselect-wide treeselect-34px treeselect-noborder bank-field--type"
            />
            <input
              v-model="formAmount"
              class="form-control bank-field bank-field--amount"
              type="number"
              min="0"
              step="0.01"
              placeholder="Сумма"
              :disabled="saving"
            >
            <input
              v-model.trim="formComment"
              class="form-control bank-field bank-field--comment"
              type="text"
              placeholder="Комментарий"
              :disabled="saving"
            >
            <button
              class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
              type="button"
              title="Сохранить"
              :disabled="saving || !canSave"
              @click="saveCreate"
            >
              <i class="fa fa-save" />
            </button>
            <button
              class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
              type="button"
              title="Отмена"
              :disabled="saving"
              @click="cancelForm"
            >
              <i class="fa fa-times" />
            </button>
          </div>

          <div
            v-else
            class="bank-receipts__row bank-receipts__row--child bank-receipts__row--add"
          >
            <button
              class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
              type="button"
              title="Добавить распределение"
              :disabled="isBusy"
              @click="startCreateChild(item)"
            >
              <i class="fa fa-plus" />
            </button>
          </div>
        </template>
      </div>

      <div
        v-if="creatingRoot"
        class="bank-receipts__row bank-receipts__row--form"
      >
        <input
          v-model="formDate"
          class="form-control bank-field bank-field--date"
          type="date"
          :disabled="saving"
        >
        <Treeselect
          v-model="formPaymentTypeId"
          :multiple="false"
          :disable-branch-nodes="true"
          :options="paymentTypeOptions"
          placeholder="Вид платежа…"
          :clearable="true"
          :append-to-body="true"
          :disabled="saving"
          class="treeselect-wide treeselect-34px treeselect-noborder bank-field--type"
        />
        <input
          v-model="formAmount"
          class="form-control bank-field bank-field--amount"
          type="number"
          min="0"
          step="0.01"
          placeholder="Сумма"
          :disabled="saving"
        >
        <input
          v-model.trim="formComment"
          class="form-control bank-field bank-field--comment"
          type="text"
          placeholder="Комментарий"
          :disabled="saving"
        >
        <button
          class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
          type="button"
          title="Сохранить"
          :disabled="saving || !canSave"
          @click="saveCreate"
        >
          <i class="fa fa-save" />
        </button>
        <button
          class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
          type="button"
          title="Отмена"
          :disabled="saving"
          @click="cancelForm"
        >
          <i class="fa fa-times" />
        </button>
      </div>

        <div
          v-if="!creatingRoot"
          class="bank-receipts__row bank-receipts__row--add"
        >
          <button
            class="btn btn-blue-nb nbr bank-receipts__add-btn"
            type="button"
            :disabled="isBusy"
            @click="startCreateRoot"
          >
            Добавить
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  getCurrentInstance,
  ref,
  watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';

interface PaymentTypeOption {
  id: number;
  label: string;
  not_control?: boolean;
}

interface BankReceipt {
  id: number;
  real_estate_id: number;
  payment_type_id: number | null;
  payment_type_title: string;
  date: string | null;
  amount: string;
  comment: string;
  parent_id?: number | null;
  not_control?: boolean;
  parent_pay_receipt?: BankReceipt[];
}

const props = defineProps<{
  realEstateId: number;
  year: number | null;
}>();

const emit = defineEmits<{(e: 'changed'): void;
}>();

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const receipts = ref<BankReceipt[]>([]);
const paymentTypeOptions = ref<PaymentTypeOption[]>([]);
const paymentTypeAllocOptions = ref<PaymentTypeOption[]>([]);
const saving = ref(false);
const creatingRoot = ref(false);
const creatingParentId = ref<number | null>(null);
const editingId = ref<number | null>(null);
const editingParentId = ref<number | null>(null);
const formDate = ref('');
const formPaymentTypeId = ref<number | null>(null);
const formAmount = ref('');
const formComment = ref('');

const isBusy = computed(() => (
  saving.value
  || creatingRoot.value
  || creatingParentId.value !== null
  || editingId.value !== null
));

const canSave = computed(() => (
  Boolean(formDate.value)
  && formPaymentTypeId.value !== null
  && formAmount.value !== ''
));

const parseAmount = (value: string) => {
  const normalized = String(value || '').replace(',', '.').trim();
  const amount = Number(normalized);
  return Number.isFinite(amount) ? amount : NaN;
};

const receiptsTotal = computed(() => {
  if (receipts.value.length === 0) {
    return null;
  }
  const total = receipts.value.reduce((sum, item) => sum + (parseAmount(item.amount) || 0), 0);
  return total.toFixed(2);
});

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

const resetForm = () => {
  formDate.value = '';
  formPaymentTypeId.value = null;
  formAmount.value = '';
  formComment.value = '';
};

const cancelForm = () => {
  creatingRoot.value = false;
  creatingParentId.value = null;
  editingId.value = null;
  editingParentId.value = null;
  resetForm();
};

const applyResult = (result: {
  receipts?: BankReceipt[];
  payment_types?: PaymentTypeOption[];
  payment_types_alloc?: PaymentTypeOption[];
} | null) => {
  receipts.value = Array.isArray(result?.receipts) ? result.receipts : [];
  paymentTypeOptions.value = Array.isArray(result?.payment_types) ? result.payment_types : [];
  paymentTypeAllocOptions.value = Array.isArray(result?.payment_types_alloc)
    ? result.payment_types_alloc
    : paymentTypeOptions.value.filter((item) => !item.not_control);
};

const loadData = async () => {
  if (!props.year) {
    receipts.value = [];
    paymentTypeOptions.value = [];
    paymentTypeAllocOptions.value = [];
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    const { ok, message, result } = await api('gardening/get-bank-receipts', {
      real_estate_id: props.realEstateId,
      year: props.year,
    });
    if (ok === false) {
      root.$emit('msg', 'error', message || 'Не удалось загрузить поступления');
      receipts.value = [];
      paymentTypeOptions.value = [];
      paymentTypeAllocOptions.value = [];
      return;
    }
    applyResult(result);
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const startCreateRoot = () => {
  if (isBusy.value) {
    return;
  }
  cancelForm();
  creatingRoot.value = true;
};

const startCreateChild = (parent: BankReceipt) => {
  if (isBusy.value) {
    return;
  }
  cancelForm();
  creatingParentId.value = parent.id;
  formDate.value = parent.date || '';
};

const startEditRoot = (item: BankReceipt) => {
  if (creatingRoot.value || creatingParentId.value !== null || editingId.value !== null) {
    return;
  }
  creatingRoot.value = false;
  creatingParentId.value = null;
  editingId.value = item.id;
  editingParentId.value = null;
  formDate.value = item.date || '';
  formPaymentTypeId.value = item.payment_type_id;
  formAmount.value = item.amount || '';
  formComment.value = item.comment || '';
};

const startEditChild = (parent: BankReceipt, child: BankReceipt) => {
  if (creatingRoot.value || creatingParentId.value !== null || editingId.value !== null) {
    return;
  }
  editingId.value = child.id;
  editingParentId.value = parent.id;
  formDate.value = child.date || '';
  formPaymentTypeId.value = child.payment_type_id;
  formAmount.value = child.amount || '';
  formComment.value = child.comment || '';
};

const childrenTotal = (item: BankReceipt) => (
  (item.parent_pay_receipt || [])
    .reduce((sum, child) => sum + (parseAmount(child.amount) || 0), 0)
);

const parentAmountClass = (item: BankReceipt) => {
  if (!item.not_control) {
    return null;
  }
  const parentAmount = parseAmount(item.amount);
  if (!Number.isFinite(parentAmount)) {
    return null;
  }
  const allocated = childrenTotal(item);
  const fullyAllocated = Math.abs(allocated - parentAmount) < 0.005;
  return fullyAllocated
    ? 'bank-receipts__amount--full'
    : 'bank-receipts__amount--partial';
};

const formatAmountNumber = (value: number) => Number(value.toFixed(2)).toString();

const formatParentAmount = (item: BankReceipt) => {
  if (!item.not_control) {
    return item.amount;
  }
  const parentAmount = parseAmount(item.amount);
  if (!Number.isFinite(parentAmount)) {
    return item.amount;
  }
  const allocated = childrenTotal(item);
  const remaining = parentAmount - allocated;
  if (remaining < 0.005) {
    return item.amount;
  }
  return `${item.amount} — ${formatAmountNumber(remaining)}`;
};

const validateChildAllocation = (parentId: number, amountRaw: string, excludeId: number | null = null) => {
  const parent = receipts.value.find((item) => item.id === parentId);
  if (!parent) {
    return 'Родительский приход не найден';
  }
  const amount = parseAmount(amountRaw);
  if (!Number.isFinite(amount) || amount < 0) {
    return 'Сумма должна быть числом';
  }
  const parentAmount = parseAmount(parent.amount);
  const childrenSum = (parent.parent_pay_receipt || [])
    .filter((child) => child.id !== excludeId)
    .reduce((sum, child) => sum + (parseAmount(child.amount) || 0), 0);
  if (childrenSum + amount > parentAmount) {
    return 'Сумма распределений превышает сумму прихода';
  }
  return null;
};

const saveCreate = async () => {
  if (saving.value || !canSave.value || !props.year) {
    return;
  }
  if (creatingParentId.value !== null) {
    const error = validateChildAllocation(creatingParentId.value, formAmount.value);
    if (error) {
      root.$emit('msg', 'error', error);
      return;
    }
  }
  saving.value = true;
  await store.dispatch(actions.INC_LOADING);
  try {
    const payload: Record<string, unknown> = {
      real_estate_id: props.realEstateId,
      date: formDate.value,
      payment_type_id: formPaymentTypeId.value,
      amount: formAmount.value,
      comment: formComment.value,
      year: props.year,
    };
    if (creatingParentId.value !== null) {
      payload.parent_id = creatingParentId.value;
    }
    const { ok, message, result } = await api('gardening/create-bank-receipt', payload);
    if (!ok) {
      root.$emit('msg', 'error', message || 'Не удалось сохранить');
      return;
    }
    root.$emit('msg', 'ok', 'Сохранено');
    applyResult(result);
    emit('changed');
    cancelForm();
  } finally {
    saving.value = false;
    await store.dispatch(actions.DEC_LOADING);
  }
};

const saveEdit = async () => {
  if (saving.value || !canSave.value || editingId.value === null || !props.year) {
    return;
  }
  if (editingParentId.value !== null) {
    const error = validateChildAllocation(editingParentId.value, formAmount.value, editingId.value);
    if (error) {
      root.$emit('msg', 'error', error);
      return;
    }
  } else {
    const parent = receipts.value.find((item) => item.id === editingId.value);
    if (parent?.not_control) {
      const amount = parseAmount(formAmount.value);
      const childrenSum = (parent.parent_pay_receipt || [])
        .reduce((sum, child) => sum + (parseAmount(child.amount) || 0), 0);
      if (Number.isFinite(amount) && amount < childrenSum) {
        root.$emit('msg', 'error', 'Сумма прихода меньше суммы распределений');
        return;
      }
    }
  }
  saving.value = true;
  await store.dispatch(actions.INC_LOADING);
  try {
    const { ok, message, result } = await api('gardening/update-bank-receipt', {
      id: editingId.value,
      date: formDate.value,
      payment_type_id: formPaymentTypeId.value,
      amount: formAmount.value,
      comment: formComment.value,
      year: props.year,
    });
    if (!ok) {
      root.$emit('msg', 'error', message || 'Не удалось сохранить');
      return;
    }
    root.$emit('msg', 'ok', 'Сохранено');
    applyResult(result);
    emit('changed');
    cancelForm();
  } finally {
    saving.value = false;
    await store.dispatch(actions.DEC_LOADING);
  }
};

const removeItem = async (item: BankReceipt) => {
  try {
    await root.$dialog.confirm('Удалить поступление?');
  } catch (_) {
    return;
  }

  saving.value = true;
  await store.dispatch(actions.INC_LOADING);
  try {
    const { ok, message, result } = await api('gardening/delete-bank-receipt', {
      id: item.id,
      year: props.year,
    });
    if (!ok) {
      root.$emit('msg', 'error', message || 'Не удалось удалить');
      return;
    }
    root.$emit('msg', 'ok', 'Удалено');
    applyResult(result);
    emit('changed');
    if (editingId.value === item.id) {
      cancelForm();
    }
  } finally {
    saving.value = false;
    await store.dispatch(actions.DEC_LOADING);
  }
};

watch(
  () => [props.realEstateId, props.year],
  () => {
    cancelForm();
    loadData();
  },
  { immediate: true },
);
</script>

<style scoped lang="scss">
.bank-receipts {
  display: flex;
  flex-direction: column;
  width: auto;
  max-width: none;
  flex: 1 1 0;
  min-width: 0;
  height: auto;
  min-height: 0;
  background-color: #f8f7f7;
}

.bank-receipts__header {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  box-sizing: border-box;
  min-height: 34px;
  padding: 3px 10px;
  border-bottom: 1px solid #b1b1b1;
  color: #FFFFFF;
  font-weight: bold;
  background-color: #aab2bd;
  flex-shrink: 0;
  line-height: 28px;
}

.bank-receipts__header-title {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 1;
  max-width: calc(100% - 160px);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  pointer-events: none;
}

.bank-receipts__total {
  color: #000000;
  font-weight: bold;
  white-space: nowrap;
}

.bank-receipts__header-spacer {
  visibility: hidden;
  pointer-events: none;
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

.bank-receipts__empty {
  box-sizing: border-box;
  padding: 10px;
  color: #666;
}

.bank-receipts__list {
  overflow: visible;
  min-height: 0;
  flex: 0 0 auto;
}

.bank-receipts__add-btn {
  border-radius: 0 !important;
  min-height: 28px;
  padding: 0 12px;
}

.bank-receipts__group {
  display: contents;
}

.bank-receipts__row {
  display: flex;
  align-items: center;
  gap: 8px;
  box-sizing: border-box;
  min-height: 34px;
  padding: 3px 10px;
  border-bottom: 1px solid #b1b1b1;
  line-height: 28px;
  color: #434A54;
}

.bank-receipts__row--child {
  padding-left: 28px;
  background-color: #f3f3f3;
}

.bank-receipts__row--form {
  background-color: #f3f3f3;
}

.bank-receipts__row--parent {
  font-weight: bold;
}

.bank-receipts__row--add {
  justify-content: flex-end;
  background-color: transparent;
  border-bottom: none;
}

.bank-receipts__date {
  flex: 0 0 100px;
}

.bank-receipts__type {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bank-receipts__amount {
  flex: 0 0 130px;
  min-width: 130px;
  max-width: 130px;
  text-align: right;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bank-receipts__amount--full {
  color: #2e7d32;
  font-weight: bold;
}

.bank-receipts__amount--partial {
  color: #c62828;
  font-weight: bold;
}

.bank-receipts__comment {
  flex: 1;
  min-width: 0;
  margin-left: 40px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bank-field {
  height: 28px !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  padding: 2px 6px;
}

.bank-field--date {
  flex: 0 0 130px;
}

.bank-field--amount {
  flex: 0 0 130px;
}

.bank-field--comment {
  flex: 1;
  min-width: 0;
  margin-left: 40px;
}

.bank-field--type {
  flex: 1;
  min-width: 140px;
}

:deep(.bank-field--type) {
  .vue-treeselect__control {
    height: 28px;
    border: none !important;
    border-radius: 0 !important;
    border-bottom: 1px solid #b1b1b1 !important;
  }

  .vue-treeselect__value-container,
  .vue-treeselect__input-container {
    height: 28px;
    line-height: 28px;
  }
}
</style>
