<template>
  <div class="electricity">
    <div class="electricity__header">
      <span class="electricity__header-title">Показания электроэнергии</span>
      <button
        class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
        type="button"
        title="Добавить"
        :disabled="isBusy || !year || !canCreate"
        @click="startCreate"
      >
        <i class="fa fa-plus" />
      </button>
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
      <div
        v-if="rows.length === 0 && !creating"
        class="electricity__empty"
      >
        <span>Нет показаний</span>
        <button
          class="btn btn-blue-nb nbr electricity__add-btn"
          type="button"
          :disabled="isBusy || !canCreate"
          @click="startCreate"
        >
          Добавить
        </button>
      </div>
      <table
        v-else
        class="electricity__table"
      >
        <thead>
          <tr>
            <th>Месяц</th>
            <th>Предыдущий</th>
            <th>Текущий</th>
            <th>Потребление</th>
            <th>Тариф</th>
            <th>Начислено</th>
            <th>Переплата</th>
            <th>Остаток</th>
            <th class="electricity__col-actions" />
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in rows"
            :key="row.id"
          >
            <td>{{ row.month_label }}</td>
            <td class="electricity__num">{{ formatValue(row.previous_reading) }}</td>
            <td class="electricity__num">
              <input
                v-if="editingId === row.id"
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
            <td class="electricity__num">{{ formatValue(row.consumption) }}</td>
            <td class="electricity__num">{{ formatValue(row.tariff) }}</td>
            <td class="electricity__num">{{ formatValue(row.charge) }}</td>
            <td class="electricity__num">{{ formatValue(row.overpayment) }}</td>
            <td
              class="electricity__num"
              :class="remainderClass(row.remainder)"
            >
              {{ formatRemainder(row.remainder) }}
            </td>
            <td class="electricity__col-actions">
              <template v-if="editingId === row.id">
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
          <tr v-if="creating">
            <td>
              <Treeselect
                v-model="formMonth"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="availableMonths"
                placeholder="Месяц…"
                :clearable="true"
                :append-to-body="true"
                :disabled="saving"
                class="treeselect-wide treeselect-34px treeselect-noborder electricity-field--month"
              />
            </td>
            <td class="electricity__num">{{ formatValue(previousPreview) }}</td>
            <td class="electricity__num">
              <input
                v-model="formReading"
                class="form-control electricity-field"
                type="number"
                min="0"
                step="0.01"
                placeholder="Показание"
                :disabled="saving"
              >
            </td>
            <td class="electricity__num">{{ formatValue(null) }}</td>
            <td class="electricity__num">{{ formatValue(null) }}</td>
            <td class="electricity__num">{{ formatValue(null) }}</td>
            <td class="electricity__num">{{ formatValue(null) }}</td>
            <td class="electricity__num">{{ formatValue(null) }}</td>
            <td class="electricity__col-actions">
              <button
                class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                type="button"
                title="Сохранить"
                :disabled="saving || !canSaveCreate"
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
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';

interface MonthOption {
  id: number;
  label: string;
}

interface ElectricityRow {
  id: number;
  year: number;
  month: number;
  month_label: string;
  previous_reading: string | null;
  current_reading: string | null;
  consumption: string | null;
  tariff: string | null;
  charge: string | null;
  overpayment: string;
  remainder: string | null;
}

const props = defineProps<{
  realEstateId: number;
  year: number | null;
}>();

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const rows = ref<ElectricityRow[]>([]);
const availableMonths = ref<MonthOption[]>([]);
const previousYearDecember = ref<string | null>(null);
const creating = ref(false);
const editingId = ref<number | null>(null);
const formMonth = ref<number | null>(null);
const formReading = ref('');
const saving = ref(false);

const isBusy = computed(() => saving.value || creating.value || editingId.value !== null);
const canCreate = computed(() => availableMonths.value.length > 0);
const canSaveCreate = computed(() => formMonth.value != null && formReading.value !== '');
const canSaveEdit = computed(() => formReading.value !== '');

const previousPreview = computed(() => {
  if (formMonth.value == null) {
    return null;
  }
  if (formMonth.value === 1) {
    return previousYearDecember.value;
  }
  const prev = rows.value.find((row) => row.month === formMonth.value - 1);
  return prev ? prev.current_reading : null;
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
  available_months?: MonthOption[];
  previous_year_december?: string | null;
}

const applyResult = (result?: ElectricityResult | null) => {
  rows.value = Array.isArray(result?.rows) ? result.rows : [];
  availableMonths.value = Array.isArray(result?.available_months) ? result.available_months : [];
  previousYearDecember.value = result?.previous_year_december ?? null;
};

const cancelForm = () => {
  creating.value = false;
  editingId.value = null;
  formMonth.value = null;
  formReading.value = '';
};

const loadData = async () => {
  if (!props.year || !props.realEstateId) {
    rows.value = [];
    availableMonths.value = [];
    previousYearDecember.value = null;
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
      availableMonths.value = [];
      previousYearDecember.value = null;
      return;
    }
    applyResult(result);
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const startCreate = () => {
  if (isBusy.value || !canCreate.value) {
    return;
  }
  cancelForm();
  creating.value = true;
  formReading.value = '';
};

const startEdit = (row: ElectricityRow) => {
  if (creating.value || editingId.value !== null) {
    return;
  }
  editingId.value = row.id;
  formReading.value = row.current_reading || '';
};

const saveCreate = async () => {
  if (!canSaveCreate.value || saving.value || !props.year) {
    return;
  }
  saving.value = true;
  await store.dispatch(actions.INC_LOADING);
  try {
    const { ok, message, result } = await api('gardening/create-electricity-reading', {
      real_estate_id: props.realEstateId,
      year: props.year,
      month: formMonth.value,
      reading: formReading.value,
    });
    if (!ok) {
      root.$emit('msg', 'error', message || 'Не удалось сохранить показание');
      return;
    }
    root.$emit('msg', 'ok', 'Показание добавлено');
    applyResult(result);
    cancelForm();
  } finally {
    saving.value = false;
    await store.dispatch(actions.DEC_LOADING);
  }
};

const saveEdit = async () => {
  if (!canSaveEdit.value || saving.value || editingId.value == null || !props.year) {
    return;
  }
  saving.value = true;
  await store.dispatch(actions.INC_LOADING);
  try {
    const { ok, message, result } = await api('gardening/update-electricity-reading', {
      id: editingId.value,
      year: props.year,
      reading: formReading.value,
    });
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
  flex: 1 1 0;
  min-height: 0;
  background-color: #f8f7f7;
  border-top: 1px solid #b1b1b1;
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

.electricity__add-btn {
  border-radius: 0 !important;
  min-height: 28px;
  padding: 0 12px;
}

.electricity__body {
  overflow: auto;
  min-height: 0;
  flex: 1;
}

.electricity__table {
  width: 100%;
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
  }

  th {
    font-weight: bold;
    background-color: #ececec;
    position: sticky;
    top: 0;
    z-index: 1;
  }
}

.electricity__num {
  text-align: right !important;
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

.electricity-field {
  height: 28px !important;
  width: 88px;
  border-radius: 0 !important;
  box-shadow: none !important;
  padding: 2px 6px;
  display: inline-block;
}

.electricity-field--month {
  min-width: 120px;
}

:deep(.electricity-field--month) {
  .vue-treeselect__control {
    height: 28px;
    min-height: 28px;
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
