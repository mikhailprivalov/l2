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
          <GardeningAccountingSummary
            v-else-if="showAllPanel"
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
                type="number"
                min="1"
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

interface RealEstateItem {
  id: number;
  num_object: number | null;
}

interface YearPaymentTypeOption {
  id: number;
  label: string;
  not_control?: boolean;
}

const store = useStore();
const root = getCurrentInstance().proxy.$root;
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

watch(settingsMode, (isSettings) => {
  if (isSettings) {
    selectedYear.value = null;
    selectedPaymentTypeId.value = null;
    return;
  }
  if (selectedYear.value === null) {
    selectedYear.value = currentYear;
  }
});

watch(selectedId, () => {
  selectedPaymentTypeId.value = null;
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

const openAddModal = () => {
  editingId.value = null;
  newNumObject.value = '';
  showAddModal.value = true;
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

onMounted(() => {
  loadRealEstates();
});
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
  height: 100%;

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

.years-strip {
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  flex: 1;
  min-width: 0;
  overflow-x: auto;
  height: 100%;
}

.payment-types-strip {
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
.gardening-layout .payment-types-strip .year-button.active-button {
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
