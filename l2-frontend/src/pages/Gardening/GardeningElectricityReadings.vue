<template>
  <div class="electricity">
    <div class="electricity__layout">
      <div class="electricity__panel">
        <div class="electricity__header">
          <button
            class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
            type="button"
            title="Развернуть"
            :disabled="rowsExpanded"
            @click="rowsExpanded = true"
          >
            <i class="fa fa-plus" />
          </button>
          <button
            class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
            type="button"
            title="Свернуть"
            :disabled="!rowsExpanded"
            @click="rowsExpanded = false"
          >
            <i class="fa fa-minus" />
          </button>
          <span class="electricity__header-title">Показания электроэнергии</span>
          <button
            class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
            type="button"
            title="Добавить счётчик"
            :disabled="!year || saving"
            @click="addMeter"
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
            v-if="metersInPeriod.length > 0"
            class="electricity__meters-bar"
          >
            <div
              v-for="meter in metersInPeriod"
              :key="`bar-${meter.id}`"
              class="electricity__meter-chip"
            >
              <span class="electricity__meter-title">{{ meter.title }}</span>
              <button
                class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                type="button"
                title="Настроить счётчик"
                :disabled="isBusy"
                @click="openMeterModal(meter)"
              >
                <i class="fa fa-pencil" />
              </button>
            </div>
          </div>
          <table class="electricity__table">
            <thead>
              <tr>
                <th class="electricity__col-month">
                  Месяц
                </th>
                <th
                  v-if="showMeterColumn"
                  class="electricity__col-meter"
                >
                  Счётчик
                </th>
                <th class="electricity__col-previous">
                  Прошлый
                </th>
                <th>Текущий</th>
                <th>Факт</th>
                <th>Тариф</th>
                <th>Начислено</th>
                <th>Списано</th>
                <th>Долг</th>
                <th>Остаток</th>
                <th>Приход</th>
                <th class="electricity__col-actions" />
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in visibleTableRows"
                :key="item.key"
                :class="{
                  'electricity__row--month-start': item.showMonthStart,
                  'electricity__row--total': item.isTotal,
                }"
              >
                <td class="electricity__col-month">
                  {{ item.isTotal && rowsExpanded ? '' : item.row.month_label }}
                </td>
                <td
                  v-if="showMeterColumn"
                  class="electricity__col-meter"
                >
                  {{ item.isTotal ? 'Итого' : (item.meter ? item.meter.title : '') }}
                </td>
                <td class="electricity__num electricity__col-previous">
                  <div
                    v-if="!item.isTotal && item.meter"
                    class="electricity__prev"
                  >
                    <input
                      v-if="isEditingRow(item.meter, item.row)"
                      v-model="formPrevious"
                      class="form-control electricity-field"
                      :class="{ 'electricity__manual': item.row.previous_manual }"
                      type="number"
                      min="0"
                      step="0.01"
                      :disabled="saving"
                    >
                    <template v-else>
                      <span :class="{ 'electricity__manual': item.row.previous_manual }">
                        {{ formatValue(item.row.previous_reading) }}
                      </span>
                      <button
                        v-if="item.row.id"
                        class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                        type="button"
                        title="Ручная корректировка"
                        :disabled="savingPrevious"
                        @click="openPreviousModal(item.row)"
                      >
                        <i class="fa fa-pencil-square-o" />
                      </button>
                    </template>
                  </div>
                  <template v-else>
                    {{ formatValue(null) }}
                  </template>
                </td>
                <td class="electricity__num">
                  <input
                    v-if="!item.isTotal && item.meter && isEditingRow(item.meter, item.row)"
                    v-model="formReading"
                    class="form-control electricity-field"
                    type="number"
                    min="0"
                    step="0.01"
                    :disabled="saving"
                  >
                  <template v-else>
                    {{ formatValue(item.isTotal ? null : item.row.current_reading) }}
                  </template>
                </td>
                <td class="electricity__num">
                  {{ formatValue(rowConsumption(item)) }}
                </td>
                <td
                  class="electricity__num"
                  :class="{ 'electricity__tariff--missing': !item.isTotal && isTariffMissing(item.row.tariff) }"
                >
                  {{ item.isTotal ? formatValue(null) : formatTariff(item.row.tariff) }}
                </td>
                <td class="electricity__num">
                  {{ formatValue(rowCharge(item)) }}
                </td>
                <td class="electricity__num">
                  {{ formatValue(item.row.written_off) }}
                </td>
                <td
                  class="electricity__num"
                  :class="item.showMoney ? debtClass(item.row.debt) : null"
                >
                  {{ formatValue(item.showMoney ? item.row.debt : null) }}
                </td>
                <td
                  class="electricity__num"
                  :class="item.showMoney ? remainderClass(item.row.remainder) : null"
                >
                  {{ item.showMoney ? formatRemainder(item.row.remainder) : formatValue(null) }}
                </td>
                <td class="electricity__num">
                  {{ formatValue(item.showMoney ? item.row.receipt : null) }}
                </td>
                <td class="electricity__col-actions">
                  <div
                    v-if="!item.isTotal && item.meter"
                    class="electricity__actions"
                  >
                    <template v-if="isEditingRow(item.meter, item.row)">
                      <button
                        class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                        type="button"
                        :title="isCurrentLessThanPrevious(formReading, formPrevious) ? READING_ORDER_ERROR : 'Сохранить'"
                        :disabled="saving || !canSaveEdit"
                        @click="saveEdit(item.meter)"
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
                        @click="startEdit(item.meter, item.row)"
                      >
                        <i class="fa fa-pencil" />
                      </button>
                      <button
                        v-if="item.row.id"
                        class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                        type="button"
                        title="Удалить"
                        :disabled="isBusy"
                        @click="removeItem(item.row)"
                      >
                        <i class="fa fa-minus" />
                      </button>
                    </template>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
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
                  :title="isCurrentLessThanPrevious(previousModalCurrent, previousModalValue) ? READING_ORDER_ERROR : 'Сохранить'"
                  :disabled="savingPrevious || !canSavePrevious"
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

    <MountingPortal
      mount-to="#portal-place-modal"
      name="GardeningElectricityMeterModal"
      append
    >
      <transition name="fade">
        <Modal
          v-if="meterModalOpen"
          show-footer="true"
          white-bg="true"
          max-width="560px"
          width="100%"
          margin-left-right="auto"
          @close="closeMeterModal"
        >
          <span slot="header">Счётчик</span>
          <div
            slot="body"
            class="modal-body-form"
          >
            <div class="form-group">
              <label>Название</label>
              <input
                v-model.trim="meterModalTitle"
                class="form-control"
                type="text"
                :disabled="savingMeter"
              >
            </div>
            <div class="form-group">
              <label>Дата начала установки</label>
              <input
                v-model="meterModalDateStart"
                class="form-control"
                type="date"
                :disabled="savingMeter"
              >
            </div>
            <div class="form-group">
              <label>Дата окончания</label>
              <input
                v-model="meterModalDateEnd"
                class="form-control"
                type="date"
                :disabled="savingMeter"
              >
            </div>
            <div class="form-group">
              <label>Адрес абонента</label>
              <input
                v-model.trim="meterModalSubscriberAddress"
                class="form-control"
                type="text"
                :disabled="savingMeter"
              >
            </div>
            <div class="form-group">
              <label>Абонент</label>
              <input
                v-model.trim="meterModalSubscriber"
                class="form-control"
                type="text"
                :disabled="savingMeter"
              >
            </div>
            <div class="form-group">
              <label>Тип прибора</label>
              <input
                v-model.trim="meterModalDeviceType"
                class="form-control"
                type="text"
                :disabled="savingMeter"
              >
            </div>
            <div class="form-group">
              <label>Серийный № прибора</label>
              <input
                v-model.trim="meterModalSerialNumber"
                class="form-control"
                type="text"
                :disabled="savingMeter"
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
                  :disabled="savingMeter || !meterModalTitle"
                  @click="saveMeterModal"
                >
                  Сохранить
                </button>
              </div>
              <div class="col-xs-3">
                <button
                  class="btn btn-primary-nb btn-blue-nb"
                  type="button"
                  :disabled="savingMeter"
                  @click="closeMeterModal"
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
  written_off: string | null;
  debt: string | null;
  receipt: string | null;
  remainder: string | null;
}

interface ElectricityMeter {
  id: number;
  title: string;
  date_start?: string | null;
  date_end?: string | null;
  subscriber_address?: string;
  subscriber?: string;
  device_type?: string;
  serial_number?: string;
  show_money?: boolean;
  rows: ElectricityRow[];
}

const props = defineProps<{
  realEstateId: number;
  year: number | null;
}>();

const emit = defineEmits<{(e: 'meters-changed'): void;
}>();

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const meters = ref<ElectricityMeter[]>([]);
const editingMeterId = ref<number | null>(null);
const editingMonth = ref<number | null>(null);
const formReading = ref('');
const formPrevious = ref('');
const originalPrevious = ref<string | null>(null);
const saving = ref(false);
const previousModalOpen = ref(false);
const previousModalRowId = ref<number | null>(null);
const previousModalMonthLabel = ref('');
const previousModalValue = ref('');
const previousModalCurrent = ref('');
const savingPrevious = ref(false);
const meterModalOpen = ref(false);
const meterModalId = ref<number | null>(null);
const meterModalTitle = ref('');
const meterModalDateStart = ref('');
const meterModalDateEnd = ref('');
const meterModalSubscriberAddress = ref('');
const meterModalSubscriber = ref('');
const meterModalDeviceType = ref('');
const meterModalSerialNumber = ref('');
const savingMeter = ref(false);
const tariffsByMonth = ref<Record<string, string | null>>({});
const rowsExpanded = ref(true);

const isBusy = computed(() => (
  saving.value || savingMeter.value || editingMonth.value !== null || meterModalOpen.value
));
const READING_ORDER_ERROR = 'Текущее показание не может быть меньше предыдущего';
const isCurrentLessThanPrevious = (currentRaw: string, previousRaw: string) => {
  if (currentRaw === '' || previousRaw === '') {
    return false;
  }
  const current = Number(String(currentRaw).replace(',', '.'));
  const previous = Number(String(previousRaw).replace(',', '.'));
  if (!Number.isFinite(current) || !Number.isFinite(previous)) {
    return false;
  }
  return current < previous;
};
const canSaveEdit = computed(() => (
  formReading.value !== '' && !isCurrentLessThanPrevious(formReading.value, formPrevious.value)
));
const canSavePrevious = computed(() => (
  previousModalValue.value !== ''
  && !isCurrentLessThanPrevious(previousModalCurrent.value, previousModalValue.value)
));

const isEditingRow = (meter: ElectricityMeter, row: ElectricityRow) => (
  editingMeterId.value === meter.id && editingMonth.value === row.month
);

interface TableRow {
  key: string;
  isTotal: boolean;
  meter: ElectricityMeter | null;
  row: ElectricityRow;
  showMoney: boolean;
  showMonthStart: boolean;
}

const parseYearMonth = (value?: string | null) => {
  if (!value) {
    return null;
  }
  const [yearPart, monthPart] = String(value).slice(0, 10).split('-');
  const yearValue = Number(yearPart);
  const monthValue = Number(monthPart);
  if (!Number.isFinite(yearValue) || !Number.isFinite(monthValue) || monthValue < 1 || monthValue > 12) {
    return null;
  }
  return { year: yearValue, month: monthValue };
};

const meterActiveInMonth = (meter: ElectricityMeter, year: number, month: number) => {
  const start = parseYearMonth(meter.date_start);
  const end = parseYearMonth(meter.date_end);
  if (start && (start.year > year || (start.year === year && start.month > month))) {
    return false;
  }
  if (end && (end.year < year || (end.year === year && end.month < month))) {
    return false;
  }
  return true;
};

const metersInPeriod = computed(() => {
  const { year } = props;
  if (!year) {
    return [];
  }
  return meters.value.filter((meter) => {
    for (let month = 1; month <= 12; month += 1) {
      if (meterActiveInMonth(meter, year, month)) {
        return true;
      }
    }
    return false;
  });
});

const showMeterColumn = computed(() => metersInPeriod.value.length > 1);

const parseAmount = (value: string | null | undefined) => {
  if (value == null || value === '') {
    return null;
  }
  const amount = Number(String(value).replace(',', '.'));
  return Number.isFinite(amount) ? amount : null;
};

const sumAmounts = (values: (string | null | undefined)[]) => {
  let total = 0;
  let hasValue = false;
  values.forEach((value) => {
    const amount = parseAmount(value);
    if (amount == null) {
      return;
    }
    total += amount;
    hasValue = true;
  });
  return hasValue ? total.toFixed(2) : null;
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

const tableRows = computed(() => {
  const result: TableRow[] = [];
  const { year } = props;
  if (!year) {
    return result;
  }
  for (let month = 1; month <= 12; month += 1) {
    const monthItems: TableRow[] = [];
    metersInPeriod.value.forEach((meter) => {
      if (!meterActiveInMonth(meter, year, month)) {
        return;
      }
      const row = meter.rows.find((item) => item.month === month);
      if (!row) {
        return;
      }
      monthItems.push({
        key: `${meter.id}-${row.month}`,
        isTotal: false,
        meter,
        row,
        showMoney: false,
        showMonthStart: false,
      });
    });
    if (monthItems.length === 0) {
      continue;
    }
    monthItems[0].showMonthStart = month > 1 && (
      monthItems.length > 1 || metersInPeriod.value.length > 1
    );
    if (monthItems.length === 1) {
      monthItems[0].showMoney = true;
      result.push(...monthItems);
      continue;
    }
    result.push(...monthItems);
    const moneySource = monthItems.find((item) => (
      item.row.remainder !== null && item.row.remainder !== undefined
    )) || monthItems[0];
    const { row: moneyRow } = moneySource;
    const consumptionValues = monthItems.map((item) => (
      item.meter && isEditingRow(item.meter, item.row) ? editConsumption.value : item.row.consumption
    ));
    const chargeValues = monthItems.map((item) => (
      item.meter && isEditingRow(item.meter, item.row) ? editCharge.value : item.row.charge
    ));
    const writtenOffValues = monthItems.map((item) => item.row.written_off);
    result.push({
      key: `total-${month}`,
      isTotal: true,
      meter: null,
      row: {
        ...moneyRow,
        id: null,
        previous_reading: null,
        previous_manual: false,
        current_reading: null,
        consumption: sumAmounts(consumptionValues),
        tariff: null,
        charge: sumAmounts(chargeValues),
        written_off: sumAmounts(writtenOffValues),
      },
      showMoney: true,
      showMonthStart: false,
    });
  }
  return result;
});

const visibleTableRows = computed(() => {
  if (rowsExpanded.value) {
    return tableRows.value;
  }
  const monthsWithTotal = new Set(
    tableRows.value.filter((item) => item.isTotal).map((item) => item.row.month),
  );
  const collapsed = tableRows.value.filter((item) => (
    item.isTotal || !monthsWithTotal.has(item.row.month)
  ));
  return collapsed.map((item, index) => {
    const { month } = item.row;
    const prev = collapsed[index - 1];
    return {
      ...item,
      showMonthStart: Boolean(prev) && prev.row.month !== month,
    };
  });
});

const rowConsumption = (item: TableRow) => {
  if (item.isTotal || !item.meter) {
    return item.row.consumption;
  }
  return isEditingRow(item.meter, item.row) ? editConsumption.value : item.row.consumption;
};

const rowCharge = (item: TableRow) => {
  if (item.isTotal || !item.meter) {
    return item.row.charge;
  }
  return isEditingRow(item.meter, item.row) ? editCharge.value : item.row.charge;
};

const formatValue = (value: string | null | undefined) => {
  if (value === null || value === undefined || value === '') {
    return '—';
  }
  return value;
};

const isTariffMissing = (value: string | null | undefined) => value == null || value === '';

const formatTariff = (value: string | null | undefined) => {
  if (isTariffMissing(value)) {
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
    return 'electricity__remainder--zero';
  }
  return amount > 0 ? 'electricity__remainder--plus' : 'electricity__remainder--minus';
};

const debtClass = (value: string | null) => {
  if (value === null || value === undefined) {
    return null;
  }
  const amount = Number(String(value).replace(',', '.'));
  if (!Number.isFinite(amount) || amount <= 0.005) {
    return null;
  }
  return 'electricity__debt';
};

interface ElectricityResult {
  meters?: ElectricityMeter[];
  rows?: ElectricityRow[];
  tariffs?: Record<string, string | null>;
}

const applyResult = (result?: ElectricityResult | null) => {
  if (Array.isArray(result?.meters) && result.meters.length > 0) {
    meters.value = result.meters;
  } else {
    meters.value = Array.isArray(result?.rows)
      ? [{
        id: 0,
        title: 'Счётчик 1',
        show_money: true,
        rows: result.rows,
      }]
      : [];
  }
  tariffsByMonth.value = result?.tariffs && typeof result.tariffs === 'object' ? result.tariffs : {};
};

const cancelForm = () => {
  editingMeterId.value = null;
  editingMonth.value = null;
  formReading.value = '';
  formPrevious.value = '';
  originalPrevious.value = null;
};

const closeMeterModal = () => {
  if (savingMeter.value) {
    return;
  }
  meterModalOpen.value = false;
  meterModalId.value = null;
  meterModalTitle.value = '';
  meterModalDateStart.value = '';
  meterModalDateEnd.value = '';
  meterModalSubscriberAddress.value = '';
  meterModalSubscriber.value = '';
  meterModalDeviceType.value = '';
  meterModalSerialNumber.value = '';
};

const openMeterModal = (meter: ElectricityMeter) => {
  if (isBusy.value && !meterModalOpen.value) {
    return;
  }
  cancelForm();
  meterModalId.value = meter.id;
  meterModalTitle.value = meter.title;
  meterModalDateStart.value = meter.date_start || '';
  meterModalDateEnd.value = meter.date_end || '';
  meterModalSubscriberAddress.value = meter.subscriber_address || '';
  meterModalSubscriber.value = meter.subscriber || '';
  meterModalDeviceType.value = meter.device_type || '';
  meterModalSerialNumber.value = meter.serial_number || '';
  meterModalOpen.value = true;
};

const saveMeterModal = async () => {
  const title = meterModalTitle.value.trim();
  if (!title || savingMeter.value || meterModalId.value == null || !props.year) {
    return;
  }
  savingMeter.value = true;
  await store.dispatch(actions.INC_LOADING);
  try {
    const { ok, message, result } = await api('gardening/update-electricity-meter', {
      real_estate_id: props.realEstateId,
      year: props.year,
      id: meterModalId.value,
      title,
      date_start: meterModalDateStart.value || null,
      date_end: meterModalDateEnd.value || null,
      subscriber_address: meterModalSubscriberAddress.value.trim(),
      subscriber: meterModalSubscriber.value.trim(),
      device_type: meterModalDeviceType.value.trim(),
      serial_number: meterModalSerialNumber.value.trim(),
    });
    if (!ok) {
      root.$emit('msg', 'error', message || 'Не удалось сохранить счётчик');
      return;
    }
    applyResult(result);
    emit('meters-changed');
    savingMeter.value = false;
    closeMeterModal();
    root.$emit('msg', 'ok', 'Счётчик сохранён');
  } finally {
    savingMeter.value = false;
    await store.dispatch(actions.DEC_LOADING);
  }
};

const closePreviousModal = (force?: boolean) => {
  if (savingPrevious.value && force !== true) {
    return;
  }
  previousModalOpen.value = false;
  previousModalRowId.value = null;
  previousModalMonthLabel.value = '';
  previousModalValue.value = '';
  previousModalCurrent.value = '';
};

const openPreviousModal = (row: ElectricityRow) => {
  if (!row.id) {
    return;
  }
  previousModalRowId.value = row.id;
  previousModalMonthLabel.value = row.month_label;
  previousModalValue.value = row.previous_reading || '';
  previousModalCurrent.value = row.current_reading || '';
  previousModalOpen.value = true;
};

const savePreviousManual = async () => {
  if (savingPrevious.value || previousModalRowId.value == null || !canSavePrevious.value || !props.year) {
    if (isCurrentLessThanPrevious(previousModalCurrent.value, previousModalValue.value)) {
      root.$emit('msg', 'error', READING_ORDER_ERROR);
    }
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
    meters.value = [];
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
      meters.value = [];
      tariffsByMonth.value = {};
      return;
    }
    applyResult(result);
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const startEdit = (meter: ElectricityMeter, row: ElectricityRow) => {
  if (editingMonth.value !== null || meterModalOpen.value) {
    return;
  }
  editingMeterId.value = meter.id;
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

const saveEdit = async (meter: ElectricityMeter) => {
  if (!canSaveEdit.value || saving.value || editingMonth.value == null || !props.year) {
    if (isCurrentLessThanPrevious(formReading.value, formPrevious.value)) {
      root.$emit('msg', 'error', READING_ORDER_ERROR);
    }
    return;
  }
  const row = meter.rows.find((item) => item.month === editingMonth.value);
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
        meter_id: meter.id,
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

const addMeter = async () => {
  if (!props.year || saving.value) {
    return;
  }
  saving.value = true;
  await store.dispatch(actions.INC_LOADING);
  try {
    const { ok, message, result } = await api('gardening/create-electricity-meter', {
      real_estate_id: props.realEstateId,
      year: props.year,
    });
    if (!ok) {
      root.$emit('msg', 'error', message || 'Не удалось добавить счётчик');
      return;
    }
    applyResult(result);
    emit('meters-changed');
  } finally {
    saving.value = false;
    await store.dispatch(actions.DEC_LOADING);
  }
};

watch(
  () => [props.realEstateId, props.year],
  () => {
    cancelForm();
    closeMeterModal();
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
  flex: 0 0 auto;
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
  flex: 0 0 auto;
  overflow: visible;
}

.electricity__panel {
  display: flex;
  flex-direction: column;
  width: 81.25%;
  max-width: 81.25%;
  min-height: 0;
  flex: 0 0 81.25%;
  overflow: visible;
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
  overflow: visible;
  min-height: 0;
  flex: 0 0 auto;
}

.electricity__meters-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  box-sizing: border-box;
  min-height: 34px;
  padding: 4px 6px;
  border-bottom: 1px solid #b1b1b1;
  background-color: #ececec;
}

.electricity__meter-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
}

.electricity__meter-title {
  font-weight: bold;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.electricity__table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
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
  width: 12%;
}

.electricity__col-meter {
  width: 14%;
}

.electricity__col-previous {
  width: 14%;
  min-width: 128px;
}

.electricity__row--month-start td {
  border-top: 2px solid #8a8a8a;
}

.electricity__row--total td {
  font-weight: bold;
  background-color: #ececec;
}

.electricity__num {
  text-align: right !important;
}

.electricity__prev,
.electricity__actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  height: 32px;
  min-width: 0;
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

.electricity__manual {
  font-style: italic;
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

.electricity__debt,
.electricity__tariff--missing {
  color: #c62828;
  font-weight: bold;
}
</style>
