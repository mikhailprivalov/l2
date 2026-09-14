<template>
  <div
    class="gardening-layout"
    :class="{ 'gardening-layout--page-scroll': showOwnerPanel }"
  >
    <div class="header-row">
      <div class="header-row__nav">
        <div class="search">
          <input
            v-model.trim="searchQuery"
            type="text"
            class="form-control nbr"
            placeholder="поиск"
          >
          <button
            class="btn btn-blue-nb nbr nba"
            type="button"
            @click="openAddModal"
          >
            добавить
          </button>
        </div>
      </div>
      <div class="header-row__years">
        <div class="header-row__years-top">
          <label class="mode-checkbox">
            <input
              v-model="settingsMode"
              type="checkbox"
            >
            <span class="mode-checkbox__label">
              <span
                class="mode-checkbox__measure"
                aria-hidden="true"
              >Настройка</span>
              <span class="mode-checkbox__text">{{ settingsMode ? 'Настройка' : 'Учет' }}</span>
            </span>
          </label>
          <div class="years-strip">
            <button
              v-if="settingsMode"
              class="year-button nbr"
              :class="{ 'active-button': selectedYear === null }"
              type="button"
              @click="selectedYear = null"
            >
              База
            </button>
            <button
              v-if="settingsMode"
              class="year-button nbr"
              type="button"
              title="Скачать SQL-дамп базы"
              :disabled="backingUp"
              @click="downloadSqlBackup"
            >
              Бэкап SQL
            </button>
            <button
              v-for="year in years"
              :key="year"
              class="year-button nbr"
              :class="{ 'active-button': selectedYear === year }"
              type="button"
              @click="selectedYear = year"
            >
              {{ year }}
            </button>
          </div>
        </div>
        <div
          v-if="showPaymentTypesStrip"
          class="header-row__years-bottom"
        >
          <div class="payment-types-strip">
            <button
              class="year-button nbr"
              :class="{ 'active-button': selectedPaymentTypeId === null }"
              type="button"
              @click="selectedPaymentTypeId = null"
            >
              Итого
            </button>
            <button
              v-for="item in yearPaymentTypes"
              :key="item.id"
              class="year-button nbr"
              :class="{ 'active-button': selectedPaymentTypeId === item.id }"
              type="button"
              @click="selectedPaymentTypeId = item.id"
            >
              {{ item.label }}
            </button>
          </div>
        </div>
        <div
          v-if="showMonthsStrip"
          class="header-row__years-bottom"
        >
          <div class="months-strip">
            <button
              v-for="month in months"
              :key="month.id"
              class="year-button nbr"
              :class="{ 'active-button': !selectedDebts && selectedMonth === month.id }"
              type="button"
              @click="selectMonth(month.id)"
            >
              {{ month.label }}
            </button>
            <button
              class="year-button nbr"
              :class="{ 'active-button': selectedDebts }"
              type="button"
              @click="selectedDebts = true"
            >
              Долги
            </button>
          </div>
        </div>
      </div>
    </div>
    <div
      class="body-row"
      :class="{ 'body-row--page-scroll': showOwnerPanel }"
    >
      <div class="side-col side-col--nav">
        <div class="object-list">
          <div
            class="object-row"
            :class="{ 'object-row--active': selectedId === null }"
            role="button"
            tabindex="0"
            @click="selectedId = null"
            @keydown.enter.prevent="selectedId = null"
            @keydown.space.prevent="selectedId = null"
          >
            Все
          </div>
          <div
            v-for="item in filteredRealEstates"
            :key="item.id"
            class="object-row"
            :class="{ 'object-row--active': selectedId === item.id }"
            role="button"
            tabindex="0"
            @click="selectedId = item.id"
            @keydown.enter.prevent="selectedId = item.id"
            @keydown.space.prevent="selectedId = item.id"
          >
            <span class="object-row__label">{{ item.num_object }}</span>
            <button
              class="object-row__edit"
              type="button"
              title="Редактировать"
              @click.stop="openEditModal(item)"
            >
              <i class="fa fa-pencil" />
            </button>
          </div>
        </div>
      </div>
      <div class="side-col side-col--main">
        <div class="main-body">
          <GardeningPaymentTypes v-if="showBasePanel" />
          <GardeningYearRates
            v-else-if="showYearPanel"
            :year="selectedYear"
          />
          <GardeningDebtsList
            v-else-if="showDebtsList"
            :key="`debts-${selectedYear}-${selectedPaymentTypeId}-${electricityRefresh}`"
            :year="selectedYear"
            :payment-type-id="selectedPaymentTypeId"
          />
          <GardeningElectricityMonthList
            v-else-if="showMonthsStrip && !selectedDebts"
            :key="`month-${selectedYear}-${selectedMonth}-${electricityRefresh}`"
            :year="selectedYear"
            :month="selectedMonth"
            :payment-type-id="selectedPaymentTypeId"
            :importing="importing"
            @readings-changed="electricityRefresh += 1"
            @xlsx-selected="onXlsxSelected"
          />
          <GardeningAccountingSummary
            v-else-if="showAllPanel"
            :key="`summary-${selectedYear}-${selectedPaymentTypeId}-${electricityRefresh}`"
            :year="selectedYear"
            :payment-type-id="selectedPaymentTypeId"
          />
          <div
            v-else-if="showOwnerPanel"
            class="accounting-main"
          >
            <div class="accounting-main__owner">
              <GardeningObjectOwner
                :real-estate-id="selectedId"
                :year="selectedYear"
                :meters-revision="ownerMetersRevision"
                @meters-changed="onOwnerMetersChanged"
              />
            </div>
            <div class="accounting-main__rest">
              <div class="accounting-main__receipts">
                <GardeningBankReceipts
                  :real-estate-id="selectedId"
                  :year="selectedYear"
                  @changed="contributionsRefresh += 1"
                />
                <GardeningPlotContributions
                  :key="`contrib-${selectedId}-${selectedYear}-${contributionsRefresh}`"
                  :real-estate-id="selectedId"
                  :year="selectedYear"
                />
              </div>
              <GardeningElectricityReadings
                :key="`elec-${selectedId}-${selectedYear}-${electricityRefresh}`"
                :real-estate-id="selectedId"
                :year="selectedYear"
                @meters-changed="ownerMetersRevision += 1"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <MountingPortal
      mount-to="#portal-place-modal"
      name="GardeningAddRealEstate"
      append
    >
      <transition name="fade">
        <Modal
          v-if="showAddModal"
          show-footer="true"
          white-bg="true"
          max-width="480px"
          width="100%"
          margin-left-right="auto"
          @close="closeAddModal"
        >
          <span slot="header">{{ editingId ? 'Редактировать объект' : 'Добавить объект' }}</span>
          <div
            slot="body"
            class="modal-body-form"
          >
            <div class="form-group">
              <label>Номер объекта</label>
              <input
                v-model="newNumObject"
                class="form-control"
                type="text"
                placeholder="Введите номер"
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
                  :disabled="saving"
                  @click="saveRealEstate"
                >
                  Сохранить
                </button>
              </div>
              <div class="col-xs-3">
                <button
                  class="btn btn-primary-nb btn-blue-nb"
                  type="button"
                  :disabled="saving"
                  @click="closeAddModal"
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
      name="GardeningImportElectricity"
      append
    >
      <transition name="fade">
        <Modal
          v-if="importResult"
          show-footer="true"
          white-bg="true"
          max-width="560px"
          width="100%"
          margin-left-right="auto"
          @close="importResult = null"
        >
          <span slot="header">Загрузка показаний</span>
          <div
            slot="body"
            class="modal-body-form"
          >
            <div class="import-summary">
              <div>Период: {{ importPeriodLabel }}</div>
              <div>Участков создано: {{ importResult.plots_created }}</div>
              <div>Счётчиков создано: {{ importResult.meters_created }}</div>
              <div>Владельцев создано: {{ importResult.owners_created }}</div>
              <div>Показаний записано: {{ importResult.readings_created }}</div>
              <div>Показаний обновлено: {{ importResult.readings_updated }}</div>
              <div>Без показаний: {{ importResult.skipped_no_reading }}</div>
              <div v-if="importResult.errors.length">
                Ошибки: {{ importResult.errors.length }}
              </div>
            </div>
            <div
              v-if="importResult.errors.length"
              class="import-errors"
            >
              <div
                v-for="(item, index) in importResult.errors.slice(0, 20)"
                :key="`${item.row}-${index}`"
              >
                Строка {{ item.row }}{{ item.plot ? ` (${item.plot})` : '' }}: {{ item.message }}
              </div>
            </div>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-9" />
              <div class="col-xs-3">
                <button
                  class="btn btn-primary-nb btn-blue-nb"
                  type="button"
                  @click="importResult = null"
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
  nextTick,
  onMounted,
  ref,
  watch,
} from 'vue';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';
import Modal from '@/ui-cards/Modal.vue';
import GardeningPaymentTypes from '@/pages/Gardening/GardeningPaymentTypes.vue';
import GardeningYearRates from '@/pages/Gardening/GardeningYearRates.vue';
import GardeningObjectOwner from '@/pages/Gardening/GardeningObjectOwner.vue';
import GardeningPlotContributions from '@/pages/Gardening/GardeningPlotContributions.vue';
import GardeningBankReceipts from '@/pages/Gardening/GardeningBankReceipts.vue';
import GardeningElectricityReadings from '@/pages/Gardening/GardeningElectricityReadings.vue';
import GardeningAccountingSummary from '@/pages/Gardening/GardeningAccountingSummary.vue';
import GardeningElectricityMonthList from '@/pages/Gardening/GardeningElectricityMonthList.vue';
import GardeningDebtsList from '@/pages/Gardening/GardeningDebtsList.vue';
import { parseGardeningPlotQuery } from '@/pages/Gardening/plotUrl';

interface RealEstateItem {
  id: number;
  num_object: string | number | null;
}

interface ImportErrorItem {
  row: number;
  plot: string;
  message: string;
}

interface ImportResult {
  year: number | null;
  month: number | null;
  plots_created: number;
  meters_created: number;
  owners_created: number;
  readings_created: number;
  readings_updated: number;
  skipped_no_reading: number;
  errors: ImportErrorItem[];
}

interface YearPaymentTypeOption {
  id: number;
  label: string;
  not_control?: boolean;
  is_electricity?: boolean;
}

const store = useStore();
const vm = getCurrentInstance().proxy;
const root = vm.$root;
const currentYear = new Date().getFullYear();

const realEstates = ref<RealEstateItem[]>([]);
const selectedId = ref<number | null>(null);
const searchQuery = ref('');
const showAddModal = ref(false);
const editingId = ref<number | null>(null);
const newNumObject = ref('');
const saving = ref(false);
const yearMin = ref(2000);
const yearMaxOffset = ref(2);
const selectedYear = ref<number | null>(currentYear);
const electricityRefresh = ref(0);
const contributionsRefresh = ref(0);
const ownerMetersRevision = ref(0);
const settingsMode = ref(false);
const yearPaymentTypes = ref<YearPaymentTypeOption[]>([]);
const selectedPaymentTypeId = ref<number | null>(null);
const selectedMonth = ref<number>(1);
const selectedDebts = ref(false);
const importing = ref(false);
const backingUp = ref(false);
const importResult = ref<ImportResult | null>(null);

const months = [
  { id: 1, label: 'Январь' },
  { id: 2, label: 'Февраль' },
  { id: 3, label: 'Март' },
  { id: 4, label: 'Апрель' },
  { id: 5, label: 'Май' },
  { id: 6, label: 'Июнь' },
  { id: 7, label: 'Июль' },
  { id: 8, label: 'Август' },
  { id: 9, label: 'Сентябрь' },
  { id: 10, label: 'Октябрь' },
  { id: 11, label: 'Ноябрь' },
  { id: 12, label: 'Декабрь' },
];

const onOwnerMetersChanged = () => {
  electricityRefresh.value += 1;
  contributionsRefresh.value += 1;
};

const showBasePanel = computed(() => settingsMode.value && selectedYear.value === null);
const showYearPanel = computed(() => settingsMode.value && selectedYear.value !== null);
const showOwnerPanel = computed(() => !settingsMode.value && selectedId.value !== null);
const showAllPanel = computed(() => (
  !settingsMode.value
  && selectedId.value === null
  && selectedYear.value !== null
));
const showPaymentTypesStrip = computed(() => showAllPanel.value);
const selectedPaymentType = computed(() => (
  yearPaymentTypes.value.find((item) => item.id === selectedPaymentTypeId.value) || null
));
const showMonthsStrip = computed(() => (
  showAllPanel.value
  && selectedPaymentTypeId.value !== null
  && Boolean(selectedPaymentType.value?.is_electricity)
));
const showDebtsList = computed(() => showMonthsStrip.value && selectedDebts.value);

const selectMonth = (monthId: number) => {
  selectedDebts.value = false;
  selectedMonth.value = monthId;
};

watch(settingsMode, (isSettings) => {
  if (isSettings) {
    selectedYear.value = null;
    selectedPaymentTypeId.value = null;
    selectedDebts.value = false;
    return;
  }
  if (selectedYear.value === null) {
    selectedYear.value = currentYear;
  }
});

watch(selectedId, () => {
  selectedPaymentTypeId.value = null;
  selectedDebts.value = false;
});

watch(selectedPaymentTypeId, () => {
  selectedDebts.value = false;
});

const loadYearPaymentTypes = async () => {
  if (!showPaymentTypesStrip.value || selectedYear.value === null) {
    yearPaymentTypes.value = [];
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    const { ok, message, result } = await api('gardening/get-year-payment-types', {
      year: selectedYear.value,
    });
    if (ok === false) {
      root.$emit('msg', 'error', message || 'Не удалось загрузить виды платежей');
      yearPaymentTypes.value = [];
      return;
    }
    yearPaymentTypes.value = Array.isArray(result) ? result : [];
    if (
      selectedPaymentTypeId.value !== null
      && !yearPaymentTypes.value.some((item) => item.id === selectedPaymentTypeId.value)
    ) {
      selectedPaymentTypeId.value = null;
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

watch(
  () => [showPaymentTypesStrip.value, selectedYear.value],
  () => {
    loadYearPaymentTypes();
  },
  { immediate: true },
);

const years = computed(() => {
  const maxYear = currentYear + yearMaxOffset.value;
  const list: number[] = [];
  for (let year = yearMin.value; year <= maxYear; year += 1) {
    list.push(year);
  }
  return list;
});

const filteredRealEstates = computed(() => {
  const query = searchQuery.value.trim();
  if (!query) {
    return realEstates.value;
  }
  return realEstates.value.filter((item) => String(item.num_object ?? '').includes(query));
});

const scrollToSelectedYear = async () => {
  await nextTick();
  const active = document.querySelector('.years-strip .active-button') as HTMLElement | null;
  if (active) {
    active.scrollIntoView({ inline: 'center', block: 'nearest', behavior: 'auto' });
  }
};

const loadRealEstates = async () => {
  await store.dispatch(actions.INC_LOADING);
  try {
    const { result, year_min: yearMinValue, year_max_offset: yearMaxOffsetValue } = await api('gardening/get-real-estates');
    realEstates.value = result || [];
    if (typeof yearMinValue === 'number') {
      yearMin.value = yearMinValue;
    }
    if (typeof yearMaxOffsetValue === 'number') {
      yearMaxOffset.value = yearMaxOffsetValue;
    }
    await scrollToSelectedYear();
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const applyRouteQuery = () => {
  const { id, year } = parseGardeningPlotQuery(vm.$route?.query || {});
  settingsMode.value = false;
  if (year !== null) {
    selectedYear.value = year;
  }
  if (id !== null && realEstates.value.some((item) => item.id === id)) {
    selectedId.value = id;
  }
};

onMounted(async () => {
  await loadRealEstates();
  applyRouteQuery();
  await scrollToSelectedYear();
});

const openAddModal = () => {
  editingId.value = null;
  newNumObject.value = '';
  showAddModal.value = true;
};

const downloadSqlBackup = async () => {
  if (backingUp.value) {
    return;
  }
  backingUp.value = true;
  await store.dispatch(actions.INC_LOADING);
  try {
    const response = await fetch('/api/gardening/backup-sql', {
      credentials: 'same-origin',
    });
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      const data = await response.json();
      root.$emit('msg', 'error', data.message || 'Не удалось создать дамп');
      return;
    }
    if (!response.ok || contentType.includes('text/html')) {
      root.$emit('msg', 'error', 'Не удалось создать дамп');
      return;
    }
    const blob = await response.blob();
    const disposition = response.headers.get('content-disposition') || '';
    const match = disposition.match(/filename\*?=(?:UTF-8'')?["']?([^";]+)/i);
    const filename = match ? decodeURIComponent(match[1].replace(/["']/g, '')) : 'l2.sql.gz';
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (_) {
    root.$emit('msg', 'error', 'Не удалось создать дамп');
  } finally {
    backingUp.value = false;
    await store.dispatch(actions.DEC_LOADING);
  }
};

const openEditModal = (item: RealEstateItem) => {
  editingId.value = item.id;
  newNumObject.value = item.num_object != null ? String(item.num_object) : '';
  showAddModal.value = true;
};

const closeAddModal = () => {
  showAddModal.value = false;
  editingId.value = null;
  newNumObject.value = '';
};

const saveRealEstate = async () => {
  if (saving.value) {
    return;
  }
  saving.value = true;
  await store.dispatch(actions.INC_LOADING);
  try {
    const isEdit = editingId.value != null;
    const { ok, message, result } = await api(
      isEdit ? 'gardening/update-real-estate' : 'gardening/create-real-estate',
      isEdit
        ? { id: editingId.value, num_object: newNumObject.value }
        : { num_object: newNumObject.value },
    );
    if (!ok) {
      root.$emit('msg', 'error', message || (isEdit ? 'Не удалось сохранить объект' : 'Не удалось создать объект'));
      return;
    }
    root.$emit('msg', 'ok', isEdit ? 'Объект сохранён' : 'Объект добавлен');
    closeAddModal();
    await loadRealEstates();
    if (result?.id) {
      selectedId.value = result.id;
    }
  } finally {
    saving.value = false;
    await store.dispatch(actions.DEC_LOADING);
  }
};

const importPeriodLabel = computed(() => {
  if (!importResult.value?.year || !importResult.value?.month) {
    return '—';
  }
  const month = months.find((item) => item.id === importResult.value.month);
  return `${month ? month.label : importResult.value.month} ${importResult.value.year}`;
});

const onXlsxSelected = async (file: File) => {
  if (!file || importing.value) {
    return;
  }
  importing.value = true;
  await store.dispatch(actions.INC_LOADING);
  try {
    const formData = new FormData();
    formData.append('file', file);
    const { ok, message, result } = await api(
      'gardening/import-electricity-xlsx',
      null,
      null,
      {},
      formData,
    );
    if (!ok || !result) {
      root.$emit('msg', 'error', message || 'Не удалось загрузить файл');
      return;
    }
    importResult.value = result;
    if (result.year) {
      selectedYear.value = result.year;
    }
    if (result.month) {
      selectedMonth.value = result.month;
      selectedDebts.value = false;
    }
    electricityRefresh.value += 1;
    contributionsRefresh.value += 1;
    await loadRealEstates();
    root.$emit('msg', 'ok', 'Файл загружен');
  } finally {
    importing.value = false;
    await store.dispatch(actions.DEC_LOADING);
  }
};
</script>

<style scoped lang="scss">
.gardening-layout {
  display: flex;
  flex-direction: column;
  height: 100%;
  margin-bottom: 5px;
  background-color: #f8f7f7;
}

.gardening-layout--page-scroll {
  overflow-x: hidden;
  overflow-y: auto;

  .side-col {
    min-height: 0;
  }

  .side-col--nav,
  .side-col--main {
    overflow: visible;
  }

  .main-body {
    flex: 0 0 auto;
    overflow: visible;
  }

  .object-list {
    flex: 0 0 auto;
    overflow: visible;
  }
}

.header-row {
  display: grid;
  grid-template-columns: 1fr 6.56fr;
  flex-shrink: 0;
  min-height: 34px;
  border-bottom: 1px solid #b1b1b1;
}

.header-row__nav {
  display: flex;
  min-width: 0;
  border-right: 1px solid #b1b1b1;
  align-self: stretch;
  align-items: flex-start;
}

.header-row__years {
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: stretch;
}

.header-row__years-top,
.header-row__years-bottom {
  display: flex;
  align-items: stretch;
  min-width: 0;
  height: 34px;
  min-height: 34px;
}

.header-row__years-bottom {
  border-top: 1px solid #b1b1b1;
}

.mode-checkbox {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  height: 100%;
  padding: 0 12px;
  border-right: 1px solid #b1b1b1;
  margin: 0;
  cursor: pointer;
  color: #434A54;
  font-weight: normal;
  white-space: nowrap;

  input {
    margin: 0;
    cursor: pointer;
  }
}

.mode-checkbox__label {
  position: relative;
  display: inline-block;
}

.mode-checkbox__measure {
  visibility: hidden;
  display: block;
}

.mode-checkbox__text {
  position: absolute;
  left: 0;
  top: 0;
}

.body-row {
  display: grid;
  grid-template-columns: 1fr 6.56fr;
  flex: 1;
  min-height: 0;
}

.body-row--page-scroll {
  flex: 1 0 auto;
  min-height: min-content;
  align-items: start;
}

.side-col {
  display: flex;
  flex-direction: column;
  background-color: #f8f7f7;
  min-height: 0;
  border-radius: 0;
  margin: 0;
  box-shadow: none;
  border: none;
}

.side-col--nav {
  border-right: 1px solid #b1b1b1;
}

.side-col--main {
  overflow: hidden;
}

.main-body {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.accounting-main {
  display: flex;
  flex-direction: column;
  width: 100%;
  min-height: 0;
}

.accounting-main__owner {
  flex: 0 0 auto;
  min-height: 0;
  overflow: visible;
}

.accounting-main__rest {
  flex: 0 0 auto;
  min-height: 0;
  overflow: visible;
  display: flex;
  flex-direction: column;
  margin-top: 10px;
}

.accounting-main__receipts {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  gap: 10px;
  padding-right: 10px;
  box-sizing: border-box;
  flex: 0 0 auto;
  min-height: 0;
  overflow: visible;
}

.search {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  flex-wrap: nowrap;
  flex: 1;
  min-width: 0;
  height: 34px;
  min-height: 34px;
  max-height: 34px;

  :deep(input.form-control),
  :deep(.btn) {
    align-self: stretch;
    border-radius: 0 !important;
    -webkit-border-radius: 0 !important;
    -moz-border-radius: 0 !important;
  }

  :deep(input.form-control) {
    border: none;
    border-bottom: none;
    box-shadow: none;
    width: auto !important;
    flex: 2 166px;
    min-width: 0;
  }

  :deep(.btn) {
    flex: 3 94px;
    width: 94px;
    border-top: none !important;
    border-bottom: none !important;
    border-right: none !important;
    margin: 0;
  }
}

.import-summary {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.import-errors {
  margin-top: 10px;
  max-height: 180px;
  overflow-y: auto;
  color: #da4453;
}

.years-strip {
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  flex: 1;
  min-width: 0;
  overflow-x: auto;
  height: 100%;
}

.payment-types-strip,
.months-strip {
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  flex: 1;
  min-width: 0;
  overflow-x: auto;
  height: 100%;
}

.year-button {
  flex: 0 0 auto;
  min-width: 64px;
  height: 100%;
  border: none;
  border-right: 1px solid #b1b1b1;
  border-radius: 0 !important;
  -webkit-border-radius: 0 !important;
  -moz-border-radius: 0 !important;
  background-color: transparent;
  color: #434A54;
  padding: 0 10px;
  cursor: pointer;
  margin: 0;
}

.year-button:hover {
  background-color: #434a54;
  color: #FFFFFF;
}

.year-button:active {
  background-color: #37BC9B;
  color: #FFFFFF;
}

.active-button {
  background-color: #049372;
  color: #FFFFFF;
  border-radius: 0 !important;
  -webkit-border-radius: 0 !important;
  -moz-border-radius: 0 !important;
}

.object-list {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  padding: 0;
  margin: 0;
}

.object-row {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  box-sizing: border-box;
  height: 34px;
  min-height: 34px;
  line-height: 22px;
  border: none;
  border-bottom: 1px solid #b1b1b1;
  border-radius: 0;
  background-color: transparent;
  color: #434A54;
  padding: 0 6px 0 10px;
  text-align: left;
  cursor: pointer;
  outline: none;
  box-shadow: none;
}

.object-row__label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.object-row__edit {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  padding: 0;
  margin: 0;
  border: none;
  border-radius: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  opacity: 0.85;
  box-shadow: none;
  outline: none;
}

.object-row__edit:hover {
  opacity: 1;
}

.object-row:hover {
  background-color: #434a54;
  color: #FFFFFF;
}

.object-row--active,
.object-row--active:hover {
  background-color: #049372;
  color: #FFFFFF;
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
</style>

<style lang="scss">
.gardening-layout .search .btn.btn-blue-nb {
  border-radius: 0 !important;
  -webkit-border-radius: 0 !important;
  -moz-border-radius: 0 !important;
}

.gardening-layout .years-strip .year-button,
.gardening-layout .years-strip .year-button.active-button,
.gardening-layout .payment-types-strip .year-button,
.gardening-layout .payment-types-strip .year-button.active-button,
.gardening-layout .months-strip .year-button,
.gardening-layout .months-strip .year-button.active-button {
  border-radius: 0 !important;
  -webkit-border-radius: 0 !important;
  -moz-border-radius: 0 !important;
}

.gardening-layout .object-row,
.gardening-layout .object-row--active {
  border-radius: 0 !important;
  -webkit-border-radius: 0 !important;
  -moz-border-radius: 0 !important;
}
</style>
