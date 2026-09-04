<template>
  <div class="electricity">
    <div class="electricity__layout">
    <div class="electricity__panel">
      <div class="electricity__header">
        <span class="electricity__header-title">Показания электроэнергии</span>
      </div>

      <div
        v-if="!year"
        class="electricity__empty"
      >
        Выберите год
      </div>
      <div
        v-else
        class="electricity__body"
      >
        <table class="electricity__table">
          <thead>
            <tr>
              <th class="electricity__col-month">Месяц</th>
              <th>Предыдущий</th>
              <th>Текущий</th>
              <th>Потребление</th>
              <th>Тариф</th>
              <th>Начислено</th>
              <th>Приход</th>
              <th>Остаток</th>
              <th class="electricity__col-actions" />
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in rows"
              :key="row.month"
            >
              <td class="electricity__col-month">
                {{ row.month_label }}
              </td>
              <td class="electricity__num electricity__prev">
                <input
                  v-if="editingMonth === row.month"
                  v-model="formPrevious"
                  class="form-control electricity-field"
                  type="number"
                  min="0"
                  step="0.01"
                  :disabled="saving"
                >
                <template v-else>
                  <span>{{ formatValue(row.previous_reading) }}</span>
                  <button
                    v-if="row.id"
                    class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                    type="button"
                    title="Ручная корректировка"
                    :disabled="savingPrevious"
                    @click="openPreviousModal(row)"
                  >
                    <i class="fa fa-pencil-square-o" />
                  </button>
                </template>
              </td>
              <td class="electricity__num">
                <input
                  v-if="editingMonth === row.month"
                  v-model="formReading"
                  class="form-control electricity-field"
                  type="number"
                  min="0"
                  step="0.01"
                  :disabled="saving"
                >
                <template v-else>
                  {{ formatValue(row.current_reading) }}
                </template>
              </td>
              <td class="electricity__num">{{ formatValue(editingMonth === row.month ? editConsumption : row.consumption) }}</td>
              <td class="electricity__num">{{ formatValue(row.tariff) }}</td>
              <td class="electricity__num">{{ formatValue(editingMonth === row.month ? editCharge : row.charge) }}</td>
              <td class="electricity__num">{{ formatValue(row.receipt) }}</td>
              <td
                class="electricity__num"
                :class="remainderClass(row.remainder)"
              >
                {{ formatRemainder(row.remainder) }}
              </td>
              <td class="electricity__col-actions">
                <template v-if="editingMonth === row.month">
                  <button
                    class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                    type="button"
                    title="Сохранить"
                    :disabled="saving || !canSaveEdit"
                    @click="saveEdit"
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
                </template>
                <template v-else>
                  <button
                    class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                    type="button"
                    title="Редактировать"
                    :disabled="isBusy"
                    @click="startEdit(row)"
                  >
                    <i class="fa fa-pencil" />
                  </button>
                  <button
                    v-if="row.id"
                    class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                    type="button"
                    title="Удалить"
                    :disabled="isBusy"
                    @click="removeItem(row)"
                  >
                    <i class="fa fa-minus" />
                  </button>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <div
      v-if="year"
      class="electricity__notes"
    >
      <div class="electricity__notes-head" />
      <div
        v-for="row in rows"
        :key="`note-${row.month}`"
        class="electricity__note"
      >
        <span v-if="row.previous_manual">изменён вручную</span>
      </div>
    </div>
    </div>

    <MountingPortal
      mount-to="#portal-place-modal"
      name="GardeningElectricityPreviousModal"
      append
    >
      <transition name="fade">
        <Modal
          v-if="previousModalOpen"
          show-footer="true"
          white-bg="true"
          max-width="420px"
          width="100%"
          margin-left-right="auto"
          @close="closePreviousModal"
        >
          <span slot="header">Предыдущее показание</span>
          <div
            slot="body"
            class="modal-body-form"
          >
            <div class="form-group">
              <label>{{ previousModalMonthLabel }}</label>
              <input
                v-model="previousModalValue"
                class="form-control"
                type="number"
                min="0"
                step="0.01"
                placeholder="Показание предыдущего периода"
                :disabled="savingPrevious"
              >
            </div>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-3">
                <button
                  class="btn btn-primary-nb btn-blue-nb"
                  type="button"
                  :disabled="savingPrevious || previousModalRowId == null"
                  @click="clearPreviousManual"
                >
                  Сбросить
                </button>
              </div>
              <div class="col-xs-3" />
              <div class="col-xs-3">
                <button
                  class="btn btn-primary-nb btn-blue-nb"
                  type="button"
                  :disabled="savingPrevious || previousModalValue === ''"
                  @click="savePreviousManual"
                >
                  Сохранить
                </button>
              </div>
              <div class="col-xs-3">
                <button
                  class="btn btn-primary-nb btn-blue-nb"
                  type="button"
                  :disabled="savingPrevious"
                  @click="closePreviousModal"
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
  ref,
  watch,
} from 'vue';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';
import Modal from '@/ui-cards/Modal.vue';

interface ElectricityRow {
  id: number | null;
  year: number;
  month: number;
  month_label: string;
  previous_reading: string | null;
  previous_manual?: boolean;
  current_reading: string | null;
  consumption: string | null;
  tariff: string | null;
  charge: string | null;
  receipt: string;
  remainder: string | null;
}

const props = defineProps<{
  realEstateId: number;
  year: number | null;
}>();

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const rows = ref<ElectricityRow[]>([]);
const editingMonth = ref<number | null>(null);
const formReading = ref('');
const formPrevious = ref('');
const originalPrevious = ref<string | null>(null);
const saving = ref(false);
const previousModalOpen = ref(false);
const previousModalRowId = ref<number | null>(null);
const previousModalMonthLabel = ref('');
const previousModalValue = ref('');
const savingPrevious = ref(false);
const tariffsByMonth = ref<Record<string, string | null>>({});

const isBusy = computed(() => saving.value || editingMonth.value !== null);
const canSaveEdit = computed(() => formReading.value !== '');

const parseAmount = (value: string | null | undefined) => {
  if (value == null || value === '') {
    return null;
  }
  const amount = Number(String(value).replace(',', '.'));
  return Number.isFinite(amount) ? amount : null;
};

const tariffForMonth = (month: number | null) => {
  if (month == null) {
    return null;
  }
  const value = tariffsByMonth.value[String(month)];
  if (value == null || value === '') {
    return null;
  }
  return value;
};

const editConsumption = computed(() => {
  const prev = parseAmount(formPrevious.value);
  const current = parseAmount(formReading.value);
  if (prev == null || current == null) {
    return null;
  }
  return (current - prev).toFixed(2);
});

const editCharge = computed(() => {
  const consumption = parseAmount(editConsumption.value);
  const tariff = parseAmount(tariffForMonth(editingMonth.value));
  if (consumption == null || tariff == null) {
    return null;
  }
  return (consumption * tariff).toFixed(2);
});

const formatValue = (value: string | null | undefined) => {
  if (value === null || value === undefined || value === '') {
    return '—';
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
  const sign = amount > 0 ? '+' : '';
  return `${sign}${amount.toFixed(2)}`;
};

const remainderClass = (value: string | null) => {
  if (value === null || value === undefined) {
    return null;
  }
  const amount = Number(String(value).replace(',', '.'));
  if (!Number.isFinite(amount) || Math.abs(amount) < 0.005) {
    return 'electricity__remainder--zero';
  }
  return amount > 0 ? 'electricity__remainder--plus' : 'electricity__remainder--minus';
};

interface ElectricityResult {
  rows?: ElectricityRow[];
  tariffs?: Record<string, string | null>;
}

const applyResult = (result?: ElectricityResult | null) => {
  rows.value = Array.isArray(result?.rows) ? result.rows : [];
  tariffsByMonth.value = result?.tariffs && typeof result.tariffs === 'object' ? result.tariffs : {};
};

const cancelForm = () => {
  editingMonth.value = null;
  formReading.value = '';
  formPrevious.value = '';
  originalPrevious.value = null;
};

const closePreviousModal = (force?: boolean) => {
  if (savingPrevious.value && force !== true) {
    return;
  }
  previousModalOpen.value = false;
  previousModalRowId.value = null;
  previousModalMonthLabel.value = '';
  previousModalValue.value = '';
};

const openPreviousModal = (row: ElectricityRow) => {
  if (!row.id) {
    return;
  }
  previousModalRowId.value = row.id;
  previousModalMonthLabel.value = row.month_label;
  previousModalValue.value = row.previous_reading || '';
  previousModalOpen.value = true;
};

const savePreviousManual = async () => {
  if (savingPrevious.value || previousModalRowId.value == null || previousModalValue.value === '' || !props.year) {
    return;
  }
  savingPrevious.value = true;
  await store.dispatch(actions.INC_LOADING);
  try {
    const { ok, message, result } = await api('gardening/update-electricity-reading', {
      id: previousModalRowId.value,
      year: props.year,
      previous_reading: previousModalValue.value,
    });
    if (!ok) {
      root.$emit('msg', 'error', message || 'Не удалось сохранить предыдущее показание');
      return;
    }
    root.$emit('msg', 'ok', 'Предыдущее показание сохранено');
    applyResult(result);
    closePreviousModal(true);
  } finally {
    savingPrevious.value = false;
    await store.dispatch(actions.DEC_LOADING);
  }
};

const clearPreviousManual = async () => {
  if (savingPrevious.value || previousModalRowId.value == null || !props.year) {
    return;
  }
  savingPrevious.value = true;
  await store.dispatch(actions.INC_LOADING);
  try {
    const { ok, message, result } = await api('gardening/update-electricity-reading', {
      id: previousModalRowId.value,
      year: props.year,
      previous_reading: null,
    });
    if (!ok) {
      root.$emit('msg', 'error', message || 'Не удалось сбросить предыдущее показание');
      return;
    }
    root.$emit('msg', 'ok', 'Предыдущее показание сброшено');
    applyResult(result);
    closePreviousModal(true);
  } finally {
    savingPrevious.value = false;
    await store.dispatch(actions.DEC_LOADING);
  }
};

const loadData = async () => {
  if (!props.year || !props.realEstateId) {
    rows.value = [];
    tariffsByMonth.value = {};
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    const { ok, message, result } = await api('gardening/get-electricity-readings', {
      real_estate_id: props.realEstateId,
      year: props.year,
    });
    if (ok === false) {
      root.$emit('msg', 'error', message || 'Не удалось загрузить показания');
      rows.value = [];
      tariffsByMonth.value = {};
      return;
    }
    applyResult(result);
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const startEdit = (row: ElectricityRow) => {
  if (editingMonth.value !== null) {
    return;
  }
  editingMonth.value = row.month;
  formReading.value = row.current_reading || '';
  formPrevious.value = row.previous_reading || '';
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

const saveEdit = async () => {
  if (!canSaveEdit.value || saving.value || editingMonth.value == null || !props.year) {
    return;
  }
  const row = rows.value.find((item) => item.month === editingMonth.value);
  if (!row) {
    return;
  }
  saving.value = true;
  await store.dispatch(actions.INC_LOADING);
  try {
    const previousReading = previousPayload();
    let response;
    if (row.id) {
      const payload: Record<string, unknown> = {
        id: row.id,
        year: props.year,
        reading: formReading.value,
      };
      if (previousReading !== undefined) {
        payload.previous_reading = previousReading;
      }
      response = await api('gardening/update-electricity-reading', payload);
    } else {
      const payload: Record<string, unknown> = {
        real_estate_id: props.realEstateId,
        year: props.year,
        month: row.month,
        reading: formReading.value,
      };
      if (previousReading !== undefined) {
        payload.previous_reading = previousReading;
      }
      response = await api('gardening/create-electricity-reading', payload);
    }
    const { ok, message, result } = response;
    if (!ok) {
      root.$emit('msg', 'error', message || 'Не удалось сохранить показание');
      return;
    }
    root.$emit('msg', 'ok', 'Показание сохранено');
    applyResult(result);
    cancelForm();
  } finally {
    saving.value = false;
    await store.dispatch(actions.DEC_LOADING);
  }
};

const removeItem = async (row: ElectricityRow) => {
  if (!row.id) {
    return;
  }
  try {
    await root.$dialog.confirm('Удалить показание?');
  } catch (_) {
    return;
  }

  saving.value = true;
  await store.dispatch(actions.INC_LOADING);
  try {
    const { ok, message, result } = await api('gardening/delete-electricity-reading', {
      id: row.id,
      year: props.year,
    });
    if (!ok) {
      root.$emit('msg', 'error', message || 'Не удалось удалить');
      return;
    }
    root.$emit('msg', 'ok', 'Удалено');
    applyResult(result);
    cancelForm();
  } finally {
    saving.value = false;
    await store.dispatch(actions.DEC_LOADING);
  }
};

watch(
  () => [props.realEstateId, props.year],
  () => {
    cancelForm();
    closePreviousModal(true);
    loadData();
  },
  { immediate: true },
);
</script>

<style scoped lang="scss">
.electricity {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 100%;
  flex: 1 1 auto;
  min-height: 0;
  background-color: #f8f7f7;
  border-top: none;
  margin-top: 20px;
}

.electricity__layout {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  min-height: 0;
  flex: 1;
  overflow: hidden;
}

.electricity__panel {
  display: flex;
  flex-direction: column;
  width: 65%;
  max-width: 65%;
  min-height: 0;
  flex: 0 0 65%;
  overflow: hidden;
}

.electricity__header {
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

.electricity__header-title {
  flex: 1;
  min-width: 0;
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

.electricity__empty {
  box-sizing: border-box;
  padding: 10px;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.electricity__body {
  overflow: auto;
  min-height: 0;
  flex: 1;
}

.electricity__table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;

  th,
  td {
    box-sizing: border-box;
    height: 34px;
    padding: 0 6px;
    border: none;
    border-bottom: 1px solid #b1b1b1;
    text-align: left;
    vertical-align: middle;
    white-space: nowrap;
    overflow: hidden;
    line-height: 32px;
  }

  th {
    font-weight: bold;
    background-color: #ececec;
    position: sticky;
    top: 0;
    z-index: 1;
  }
}

.electricity__col-month {
  width: 15%;
}

.electricity__num {
  text-align: right !important;
}

.electricity__prev {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  height: 34px;
}

.electricity-field {
  height: 32px !important;
  width: 100%;
  max-width: 100%;
  border: none !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  padding: 0 6px;
  margin: 0;
  display: block;
  line-height: 32px;
}

.electricity__notes {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  padding: 0 10px;
  color: #8a6d3b;
  font-size: 12px;
}

.electricity__notes-head {
  height: 68px;
  flex-shrink: 0;
}

.electricity__note {
  height: 34px;
  line-height: 34px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.modal-body-form {
  padding: 10px 0;
}

.modal-body-form .form-group {
  margin-bottom: 0;
}

.modal-body-form label {
  display: block;
  margin-bottom: 6px;
}

.electricity__col-actions {
  width: 56px;
  min-width: 56px;
  text-align: right !important;
  white-space: nowrap;
}

.electricity__remainder--plus {
  color: #2e7d32;
  font-weight: bold;
}

.electricity__remainder--minus {
  color: #c62828;
  font-weight: bold;
}

.electricity__remainder--zero {
  font-weight: bold;
}
</style>
