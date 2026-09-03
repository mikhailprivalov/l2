<template>
  <PageInnerLayout>
    <TwoSidedLayout :left-width-px="588">
      <template #left>
        <TopBottomLayout
          :top-height-px="69"
          no-border
        >
          <template #top>
            <TopBottomLayout :top-height-px="35">
              <template #top>
                <Treeselect
                  v-model="selectedHospitalId"
                  :options="hospitals"
                  :clearable="false"
                  :disabled="hospitalsLoading"
                  :multiple="false"
                  :disable-branch-nodes="true"
                  :append-to-body="true"
                  placeholder="Выберите организацию"
                  class="treeselect-noborder treeselect-34px"
                />
              </template>
              <template #bottom>
                <div class="search">
                  <input
                    v-model.trim="numberToSearch"
                    type="text"
                    class="form-control "
                    placeholder="номер заявки"
                    @keyup.enter="searchByNumber()"
                  >
                  <button
                    class="btn btn-blue-nb"
                    :disabled="numberToSearch === ''"
                    @click="searchByNumber"
                  >
                    поиск
                  </button>
                </div>
              </template>
            </TopBottomLayout>
          </template>
          <template #bottom>
            <TopBottomLayout
              :top-height-px="toolbarHeightPx"
              no-border
            >
              <template #top>
                <div class="requests-toolbar">
                  <div class="requests-toolbar__row">
                    <DateRange
                      :key="dateRangeResetKey"
                      v-model="dateRange"
                    />
                    <button
                      class="date-range-reset"
                      type="button"
                      title="Сбросить настройки"
                      @click="resetSettings"
                    >
                      <i class="fa fa-refresh" />
                    </button>
                    <div class="requests-toolbar__filter">
                      <button
                        class="filter-btn filter-btn--compact"
                        :class="{ 'filter-btn--active': !showAccepted }"
                        @click="showAccepted = false"
                      >
                        {{ `Все (${departmentFilteredWaitRequests.length})` }}
                      </button>
                      <button
                        class="filter-btn filter-btn--compact"
                        :class="{ 'filter-btn--active': showAccepted }"
                        @click="showAccepted = true"
                      >
                        {{ `Принято (${departmentFilteredWaitRequests.filter(request => request.accepted).length})` }}
                      </button>
                      <button
                        class="filter-btn filter-btn--compact filter-btn--icon"
                        :class="{ 'filter-btn--active': isSearchMode }"
                        title="Поиск по пациенту"
                        @click="isSearchMode = !isSearchMode"
                      >
                        <i class="fa fa-search" />
                      </button>
                    </div>
                  </div>
                  <div
                    v-if="filterDepartments.length"
                    class="requests-toolbar__row requests-toolbar__row--departments"
                  >
                    <label
                      v-for="department in filterDepartments"
                      :key="department"
                      class="department-filter"
                    >
                      <input
                        type="checkbox"
                        :checked="isDepartmentSelected(department)"
                        @change="toggleDepartment(department)"
                      >
                      <span :title="department">{{ formatDepartmentLabel(department) }}</span>
                    </label>
                  </div>
                  <div
                    v-if="isSearchMode"
                    class="requests-toolbar__row requests-toolbar__row--search"
                  >
                    <input
                      v-model.trim="patientQuery"
                      type="text"
                      class="form-control requests-toolbar__search-input"
                      placeholder="поиск по пациенту"
                    >
                  </div>
                </div>
              </template>
              <template #bottom>
                <TopBottomLayout :top-height-percent="70">
                  <template #top>
                    <div class="requests-list">
                      <div
                        v-if="initialLoading"
                        class="requests-list__loading"
                      >
                        Загрузка...
                      </div>
                      <div
                        v-else
                        class="requests-list__items"
                      >
                        <RequestCard
                          v-for="request in filteredWaitRequests"
                          :key="request.id"
                          :request="request"
                          :hospital-id="selectedHospitalId"
                          @request-accepted="handleRequestAccepted"
                          @card-clicked="handleCardClick"
                        />
                        <div
                          v-if="filteredWaitRequests.length === 0"
                          class="requests-list__empty"
                        >
                          {{ showAccepted ? 'Нет принятых заявок' : 'Нет ожидающих заявок' }}
                        </div>
                      </div>
                    </div>
                  </template>
                  <template #bottom>
                    <div class="requests-list">
                      <div class="requests-list__header">
                        Исполненные
                      </div>
                      <div
                        v-if="initialLoading"
                        class="requests-list__loading"
                      >
                        Загрузка...
                      </div>
                      <div
                        v-else
                        class="requests-list__items"
                      >
                        <RequestCard
                          v-for="request in filteredDoneRequests"
                          :key="request.id"
                          :request="request"
                          :hospital-id="selectedHospitalId"
                          @card-clicked="handleCardClick"
                        />
                        <div
                          v-if="filteredDoneRequests.length === 0"
                          class="requests-list__empty"
                        >
                          Нет исполненных заявок
                        </div>
                      </div>
                    </div>
                  </template>
                </TopBottomLayout>
              </template>
            </TopBottomLayout>
          </template>
        </TopBottomLayout>
      </template>
      <template #right>
        <ResultsParaclinic
          v-if="selectedRequest"
          :key="selectedRequest.id"
          :direction-id-to-open="selectedRequest.id"
          forced-results-top
        >
          <template #before-researches>
            <div class="request-info-block">
              <div class="request-info-title">
                <span>Информация о заявке</span>
              </div>
              <div
                v-if="requestParams"
                class="request-info-content"
              >
                <div class="info-grid">
                  <div
                    v-if="requestParams.creator"
                    class="info-row"
                  >
                    <span class="info-label">Создал</span>
                    <span class="info-value">{{ requestParams.creator }}</span>
                  </div>
                  <div
                    v-if="requestParams.createdAt"
                    class="info-row"
                  >
                    <span class="info-label">Создана</span>
                    <span class="info-value">{{ requestParams.createdAt }}</span>
                  </div>
                  <div
                    v-if="requestParams.researchDate"
                    class="info-row"
                  >
                    <span class="info-label">Дата и время исследования</span>
                    <span class="info-value">{{ requestParams.researchDate }} {{ requestParams.researchTime }}</span>
                  </div>
                  <div
                    v-if="requestParams.dose"
                    class="info-row"
                  >
                    <span class="info-label">Доза</span>
                    <span class="info-value">{{ requestParams.dose }} мЗв</span>
                  </div>
                  <div
                    v-if="requestParams.contrastAmount"
                    class="info-row"
                  >
                    <span class="info-label">Контраст, объём </span>
                    <span class="info-value">{{ requestParams.textContrast }}, {{ requestParams.contrastAmount }} мл </span>
                  </div>
                  <div class="info-row">
                    <span class="info-label">Срочность</span>
                    <span class="info-value">
                      <span
                        v-if="requestParams.isCito"
                        class="cito-badge"
                      >CITO</span>
                      <template v-else>Обычная</template>
                    </span>
                  </div>
                  <div
                    v-if="requestParams.isDynamic"
                    class="info-row"
                  >
                    <span class="info-label dynamic-red">Динамика</span>
                    <span class="info-value">
                      <span
                        class="cito-badge"
                      >Сравнить</span>
                    </span>
                  </div>
                  <div class="info-row">
                    <span class="info-label">Изображение</span>
                    <span class="info-value">
                      <template v-if="requestParams.hasImage">
                        Привязано
                        <a
                          class="a-under"
                          href="#"
                          @click.prevent="showImageModal = true"
                        ><i class="fa fa-info-circle" /></a>
                      </template>
                      <template v-else>
                        Нет
                      </template>
                    </span>
                  </div>
                  <div
                    v-if="requestParams.files && requestParams.files.length > 0"
                    class="info-row"
                  >
                    <span class="info-label">Файлы</span>
                    <span class="info-value">
                      <a
                        v-for="file in requestParams.files"
                        :key="file.url"
                        :href="file.url"
                        target="_blank"
                        class="a-under"
                      >{{ file.name }}</a>
                    </span>
                  </div>
                </div>
                <div
                  v-if="requestParams.anamnesis"
                  class="info-block"
                >
                  <div class="info-block-label">
                    Анамнез
                  </div>
                  <Collapse
                    max-height="60px"
                    bg-color="#f9f9f9"
                  >
                    <div
                      class="info-block-text"
                      v-text="requestParams.anamnesis"
                    />
                  </Collapse>
                </div>
                <div
                  v-if="requestParams.comment"
                  class="info-block"
                >
                  <div class="info-block-label">
                    Комментарий
                  </div>
                  <Collapse
                    max-height="60px"
                    bg-color="#f9f9f9"
                  >
                    <div
                      class="info-block-text"
                      v-text="requestParams.comment"
                    />
                  </Collapse>
                </div>
              </div>
            </div>
          </template>
        </ResultsParaclinic>
      </template>
    </TwoSidedLayout>
    <Modal
      v-if="showImageModal && requestParams?.imageData"
      show-footer="true"
      white-bg="true"
      max-width="700px"
      margin-left-right="auto"
      @close="showImageModal = false"
    >
      <span slot="header">Детали изображения #{{ requestParams.imageData.id }}</span>
      <div
        slot="body"
        class="image-modal-body"
      >
        <div class="details-section">
          <div class="section-title">
            Данные пациента
          </div>
          <div class="detail-row">
            <span class="detail-label">Фамилия:</span>
            <span
              class="detail-value"
              :class="{ 'empty-value': !requestParams.imageData.family }"
            >{{ requestParams.imageData.family || '(не указана)' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Имя:</span>
            <span
              class="detail-value"
              :class="{ 'empty-value': !requestParams.imageData.name }"
            >{{ requestParams.imageData.name || '(не указано)' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Отчество:</span>
            <span
              class="detail-value"
              :class="{ 'empty-value': !requestParams.imageData.patronymic }"
            >{{ requestParams.imageData.patronymic || '(не указано)' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Дата рождения:</span>
            <span
              class="detail-value"
              :class="{ 'empty-value': !requestParams.imageData.birthday }"
            >{{ requestParams.imageData.birthday || '(не указана)' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Пол:</span>
            <span
              class="detail-value"
              :class="{ 'empty-value': !requestParams.imageData.sex }"
            >{{ requestParams.imageData.sex || '(не указан)' }}</span>
          </div>
        </div>

        <div class="details-section">
          <div class="section-title">
            Идентификаторы
          </div>
          <div class="detail-row">
            <span class="detail-label">ID пациента:</span>
            <span
              class="detail-value"
              :class="{ 'empty-value': !requestParams.imageData.patientId }"
            >{{ requestParams.imageData.patientId || '(отсутствует)' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">ID заказа:</span>
            <span
              class="detail-value"
              :class="{ 'empty-value': !requestParams.imageData.orderId }"
            >{{ requestParams.imageData.orderId || '(отсутствует)' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Study Instance UID:</span>
            <span
              class="detail-value small-text"
              :class="{ 'empty-value': !requestParams.imageData.studyInstanceUidTag }"
            >{{ requestParams.imageData.studyInstanceUidTag || '(отсутствует)' }}</span>
          </div>
        </div>

        <div class="details-section">
          <div class="section-title">
            Оборудование
          </div>
          <div class="detail-row">
            <span class="detail-label">Название:</span>
            <span
              class="detail-value"
              :class="{ 'empty-value': !requestParams.imageData.equipmentTitle }"
            >{{ requestParams.imageData.equipmentTitle || '(не определено)' }}</span>
          </div>
        </div>

        <div class="details-section">
          <div class="section-title">
            Даты
          </div>
          <div class="detail-row">
            <span class="detail-label">Создано:</span>
            <span class="detail-value">{{ requestParams.imageData.createdAt }}</span>
          </div>
        </div>
      </div>
      <div slot="footer">
        <button
          class="btn btn-blue-nb"
          @click="showImageModal = false"
        >
          Закрыть
        </button>
      </div>
    </Modal>
  </PageInnerLayout>
</template>

<script setup lang="ts">
import {
  computed,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from 'vue';
import moment from 'moment';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import Modal from '@/ui-cards/Modal.vue';
import ResultsParaclinic from '@/pages/ResultsParaclinic.vue';
import PageInnerLayout from '@/layouts/PageInnerLayout.vue';
import TwoSidedLayout from '@/layouts/TwoSidedLayout.vue';
import TopBottomLayout from '@/layouts/TopBottomLayout.vue';
import DateRange from '@/ui-cards/DateRange.vue';
import api from '@/api';
import directionsPoint from '@/api/directions-point';
import useLoader from '@/hooks/useLoader';
import useOn from '@/hooks/useOn';
import useNotify from '@/hooks/useNotify';
import Collapse from '@/components/Collapse.vue';

import RequestCard, { type Request } from './RequestCard.vue';

interface Hospital {
  id: number;
  label: string;
}

const MAX_PERIOD_DAYS = 40;

const getDefaultDateRange = (): [string, string] => [
  moment().subtract(10, 'days').format('DD.MM.YYYY'),
  moment().format('DD.MM.YYYY'),
];

const dateRange = ref(getDefaultDateRange());
const dateRangeResetKey = ref(0);
const hospitals = ref<Hospital[]>([]);
const selectedHospitalId = ref<number>(-1);
const hospitalsLoading = ref(false);
const requestsDone = ref<Request[]>([]);
const requestsWait = ref<Request[]>([]);
const filterDepartments = ref<string[]>([]);
const selectedDepartments = ref<Set<string>>(new Set());
const initialLoading = ref(false);
const showAccepted = ref(false);
const selectedRequest = ref<Request | null>(null);
const formData = ref<any>(null);
const formLoading = ref(false);
const requestParams = ref<any>(null);
const numberToSearch = ref<string>('');
const isSearchMode = ref(false);
const patientQuery = ref<string>('');
const showImageModal = ref(false);
let refreshInterval: any = null;

const loader = useLoader();
const notify = useNotify();

const toolbarHeightPx = computed(() => {
  let height = 36;
  if (filterDepartments.value.length) {
    height += Math.max(22, Math.ceil(filterDepartments.value.length / 2) * 20);
  }
  if (isSearchMode.value) {
    height += 36;
  }
  return height;
});

const matchesDepartmentFilter = (request: Request) => {
  if (filterDepartments.value.length === 0) {
    return true;
  }
  if (selectedDepartments.value.size === 0) {
    return false;
  }
  return selectedDepartments.value.has(request.podrzdeleniye || '-');
};

const departmentFilteredWaitRequests = computed(() => (
  requestsWait.value.filter(matchesDepartmentFilter)
));

const departmentFilteredDoneRequests = computed(() => (
  requestsDone.value.filter(matchesDepartmentFilter)
));

const filteredWaitRequests = computed(() => {
  const base = showAccepted.value
    ? departmentFilteredWaitRequests.value.filter(request => request.accepted)
    : departmentFilteredWaitRequests.value;

  const query = patientQuery.value.trim().toLowerCase();
  if (!query) return base;
  return base.filter(request => request.patient.toLowerCase().includes(query));
});

const filteredDoneRequests = computed(() => departmentFilteredDoneRequests.value);

const isDepartmentSelected = (department: string) => selectedDepartments.value.has(department);

const formatDepartmentLabel = (department: string) => (
  department.length > 5 ? `${department.slice(0, 5)}...` : department
);

const mergeFilterDepartments = (incoming: string[]) => {
  const sorted = [...new Set(incoming)].sort((a, b) => a.localeCompare(b, 'ru'));
  const previousDepartments = filterDepartments.value;
  const wasEmpty = previousDepartments.length === 0;
  const previousSelected = selectedDepartments.value;

  selectedDepartments.value = new Set(
    sorted.filter(department => {
      if (wasEmpty) {
        return true;
      }
      if (!previousDepartments.includes(department)) {
        return true;
      }
      return previousSelected.has(department);
    }),
  );
  filterDepartments.value = sorted;
};

const toggleDepartment = (department: string) => {
  const next = new Set(selectedDepartments.value);
  if (next.has(department)) {
    next.delete(department);
  } else {
    next.add(department);
  }
  selectedDepartments.value = next;
};

const loadHospitals = async () => {
  try {
    loader.global.inc();
    hospitalsLoading.value = true;
    const response = await api('requests/permissions-doctor');

    if (response.hospitals && Array.isArray(response.hospitals)) {
      hospitals.value = response.hospitals.map(h => ({
        id: h.id,
        label: h.title,
      }));
      if (hospitals.value.length > 0) {
        selectedHospitalId.value = hospitals.value[0].id;
      }
    }
  } catch (error) {
    notify.error('Ошибка загрузки организаций');
    // eslint-disable-next-line no-console
    console.error('Ошибка загрузки организаций:', error);
  } finally {
    loader.global.dec();
    hospitalsLoading.value = false;
  }
};

const resetSettings = () => {
  dateRange.value = getDefaultDateRange();
  dateRangeResetKey.value += 1;
  selectedDepartments.value = new Set(filterDepartments.value);
};

const clampDateRange = (): boolean => {
  const from = moment(dateRange.value[0], 'DD.MM.YYYY', true);
  const to = moment(dateRange.value[1], 'DD.MM.YYYY', true);

  if (!from.isValid() || !to.isValid()) {
    return false;
  }

  const start = from.isAfter(to) ? to : from;
  const end = from.isAfter(to) ? from : to;

  if (end.diff(start, 'days') <= MAX_PERIOD_DAYS) {
    if (from.isAfter(to)) {
      dateRange.value = [start.format('DD.MM.YYYY'), end.format('DD.MM.YYYY')];
      return true;
    }
    return false;
  }

  notify.error(`Период не может превышать ${MAX_PERIOD_DAYS} дней`);
  dateRange.value = [
    end.clone().subtract(MAX_PERIOD_DAYS, 'days').format('DD.MM.YYYY'),
    end.format('DD.MM.YYYY'),
  ];
  return true;
};

const loadRequestsByStatus = async (isDone: boolean) => {
  try {
    const response = await api('requests/by-status', {
      dateFrom: dateRange.value[0],
      dateTo: dateRange.value[1],
      isDone,
      hospitalId: selectedHospitalId.value,
    });

    if (response.error) {
      notify.error(response.error);
      return { rows: [], filterDepartment: [] as string[] };
    }

    return {
      rows: response.rows || [],
      filterDepartment: response.filterDepartment || [],
    };
  } catch (error) {
    notify.error('Ошибка загрузки заявок');
    // eslint-disable-next-line no-console
    console.error('Ошибка загрузки заявок:', error);
    return { rows: [], filterDepartment: [] as string[] };
  }
};

const loadAllRequests = async () => {
  const [waitResult, doneResult] = await Promise.all([
    loadRequestsByStatus(false),
    loadRequestsByStatus(true),
  ]);

  requestsWait.value = waitResult.rows;
  requestsDone.value = doneResult.rows;
  mergeFilterDepartments([
    ...waitResult.filterDepartment,
    ...doneResult.filterDepartment,
  ]);
};

useOn('change-document-state', loadAllRequests);
useOn('close-results-paraclinic', () => {
  selectedRequest.value = null;
  requestParams.value = null;
});

const startAutoRefresh = () => {
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }
  refreshInterval = setInterval(() => {
    loadAllRequests();
  }, 10000);
};

const stopAutoRefresh = () => {
  if (refreshInterval) {
    clearInterval(refreshInterval);
    refreshInterval = null;
  }
};

const handleRequestAccepted = (data: { requestId: number; accepted: boolean; acceptedByCurrentUser: boolean }) => {
  const request = requestsWait.value.find(r => r.id === data.requestId);
  if (request) {
    request.accepted = data.accepted;
    request.acceptedByCurrentUser = data.acceptedByCurrentUser;
  }
};

const loadRequestParams = async (requestId: number) => {
  const response = await api('requests/params', {
    requestId,
    hospitalId: selectedHospitalId.value,
  });

  requestParams.value = response.params;
};

const loadFormData = async (requestId: number) => {
  try {
    loader.inc();
    formLoading.value = true;
    const { direction, researches, patient } = await directionsPoint.getParaclinicForm({
      pk: requestId,
      force: true,
    });

    if (researches && researches.length > 0) {
      formData.value = {
        researches,
        patient,
        direction,
      };
    } else {
      formData.value = null;
    }
  } catch (error) {
    formData.value = null;
  } finally {
    loader.dec();
    formLoading.value = false;
  }
};

const handleCardClick = (request: Request) => {
  selectedRequest.value = request;
  showImageModal.value = false;
  loadFormData(request.id);
  loadRequestParams(request.id);
};

const searchByNumber = async () => {
  if (numberToSearch.value) {
    const { request } = await api('requests/by-number', {
      number: numberToSearch.value,
      hospitalId: selectedHospitalId.value,
    });

    if (request) {
      handleCardClick(request);
    }

    numberToSearch.value = '';
  }
};

watch(dateRange, () => {
  if (clampDateRange()) {
    return;
  }
  loadAllRequests();
}, { deep: true });

watch(selectedHospitalId, () => {
  selectedRequest.value = null;
  requestParams.value = null;
  filterDepartments.value = [];
  selectedDepartments.value = new Set();
  loadAllRequests();
});

watch(isSearchMode, value => {
  if (!value) {
    patientQuery.value = '';
  }
});

onMounted(() => {
  loadHospitals();
  initialLoading.value = true;
  loadAllRequests().finally(() => {
    initialLoading.value = false;
  });
  startAutoRefresh();
});

onBeforeUnmount(() => {
  stopAutoRefresh();
});
</script>

<style lang="scss" scoped>
.requests-toolbar {
  --toolbar-control-height: 34px;
  --toolbar-btn-height: 26px;

  display: flex;
  flex-direction: column;
  gap: 2px;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;

  &__row {
    display: flex;
    align-items: center;
    gap: 3px;
    width: 100%;
    max-width: 100%;
    min-width: 0;

    &--search {
      min-height: var(--toolbar-control-height);
    }

    &--departments {
      flex-wrap: wrap;
      align-items: flex-start;
      gap: 2px 8px;
      line-height: 1.2;
    }
  }

  &__filter {
    display: flex;
    align-items: center;
    gap: 3px;
    flex: 0 1 auto;
    min-width: 0;
  }

  &__search-input {
    flex: 1;
    min-width: 0;
    height: var(--toolbar-control-height);
    padding: 6px 8px;
    font-size: 12px;
    border-radius: 0;
  }

  :deep(.input-daterange) {
    display: inline-flex;
    width: auto;
    flex-shrink: 0;

    .form-control {
      flex: 0 0 auto;
      width: 76px;
      height: var(--toolbar-control-height);
      padding: 5px;
    }

    .input-group-addon {
      flex: 0 0 auto;
      padding: 5px 4px;
      min-width: 0;
      height: var(--toolbar-control-height);
    }
  }

  .date-range-reset,
  .filter-btn {
    height: var(--toolbar-btn-height);
    min-height: var(--toolbar-btn-height);
    box-sizing: border-box;
  }

  .date-range-reset {
    flex: 0 0 auto;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: var(--toolbar-btn-height);
    padding: 0;
    border: none;
    background: transparent;
    color: #666;
    cursor: pointer;
    font-size: 13px;

    &:hover {
      color: #049372;
    }
  }

  .filter-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0 4px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background-color: #fff;
    cursor: pointer;
    font-size: 10px;
    line-height: 1;
    white-space: nowrap;
    transition: all 0.2s ease;
    color: #666;
    min-width: 0;

    &:hover {
      background-color: #f0f0f0;
      border-color: #bbb;
      color: #333;
    }

    &--active {
      background-color: #049372;
      border-color: #049372;
      color: white;
    }

    &--icon {
      flex: 0 0 auto;
      width: auto;
      min-width: 0;
      padding: 0 4px;
      font-size: 12px;
    }

    &--compact {
      flex: 0 0 auto;
    }
  }
}

.department-filter {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin: 0;
  font-size: 12px;
  font-weight: normal;
  color: #555;
  cursor: pointer;
  max-width: 100%;

  input {
    margin: 0;
    flex-shrink: 0;
    width: 14px;
    height: 14px;
  }

  span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.requests-list {
  height: 100%;
  width: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  background: #ffffff;
}

.requests-list__header {
  position: sticky;
  top: 0;
  z-index: 1;
  background: #f5f5f7;
  font-weight: 500;
  font-size: 14px;
  padding: 4px 6px;
  border-radius: 6px;
}

.requests-list__items {
  padding: 5px;
}

.requests-list__loading {
  text-align: center;
  padding: 10px;
  color: #888;
}

.requests-list__empty {
  text-align: center;
  padding: 10px;
  color: #888;
}

.results-editor {
  height: 100%;
  width: 100%;
  max-width: calc(100vw - 588px);
  overflow-y: auto;
  overflow-x: hidden;
  padding: 10px;
}

.empty-state,
.loading-state,
.error-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #666;
  text-align: center;
  font-size: 16px;
}

.error-state {
  color: #e74c3c;
}

.form-container {
  height: 100%;
}

.form-header {
  padding-bottom: 15px;
  border-bottom: 1px solid #e0e0e0;
  margin-bottom: 15px;

  h3 {
    margin: 0 0 5px 0;
    color: #333;
    font-size: 18px;
    font-weight: 600;
  }

  .patient-info {
    margin: 0;
    color: #666;
    font-size: 14px;
  }
}

.request-params {
  margin-top: 8px;
  padding: 6px 8px;
  background-color: #f9f9f9;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
}

.params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 4px;
}

.param-item {
  display: flex;
  font-size: 11px;
  line-height: 1.3;
}

.param-label {
  font-weight: 500;
  color: #333;
  min-width: 70px;
  margin-right: 6px;
  white-space: nowrap;
}

.param-value {
  color: #666;
  flex: 1;
  word-break: break-word;
}

.form-content {
  height: calc(100% - 80px);
  overflow-y: auto;
}

.research-title {
  position: sticky;
  top: 0;
  background-color: #ddd;
  text-align: center;
  padding: 5px;
  font-weight: bold;
  z-index: 4;
  display: flex;
}

.research-left {
  position: relative;
  text-align: left;
  width: calc(100% - 430px);
}

.research-right {
  text-align: right;
  width: 430px;
  margin-top: -5px;
  margin-right: -5px;
  margin-bottom: -5px;
  white-space: nowrap;

  .btn {
    border-radius: 0;
    padding: 5px 4px;
  }
}

.comment {
  font-weight: normal;
  color: #666;
}

.control-row {
  height: 34px;
  background-color: #f3f3f3;
  display: flex;
  flex-direction: row;
  margin-bottom: 10px;

  button {
    align-self: stretch;
    border-radius: 0;
  }

  div {
    align-self: stretch;
  }
}

.res-title {
  padding: 5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status {
  display: inline-block;
  padding: 5px;
  font-weight: bold;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-none {
  color: #CF3A24
}

.status-saved {
  color: #F4D03F
}

.status-confirmed {
  color: #049372
}

.search {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  flex-wrap: nowrap;
  justify-content: stretch;
  height: 100%;

  input,
  button {
    align-self: stretch;
    border: none;
    border-radius: 0;
  }

  input {
    border-bottom: 1px solid #b1b1b1;
    width: 166px !important;
    flex: 2 166px;
    min-width: 0;
  }

  button {
    flex: 3 94px;
    width: 94px;
  }
}

.request-info-block {
  margin-bottom: 10px;
}

.request-info-title {
  position: sticky;
  top: 0;
  background-color: #ddd;
  padding: 5px;
  font-weight: bold;
  z-index: 4;
}

.request-info-content {
  padding: 10px;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-top: none;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 20px;
}

.info-row {
  display: flex;
  align-items: baseline;
  padding: 3px 0;
  font-size: 13px;
}

.info-label {
  color: #888;
  width: 186px;
  flex-shrink: 0;
}

.info-value {
  color: #333;
  flex: 1;
}

.cito-badge {
  display: inline-block;
  background: #ff6b6b;
  color: #fff;
  font-size: 10px;
  font-weight: bold;
  border-radius: 3px;
  padding: 2px 6px;
  letter-spacing: 0.5px;
  vertical-align: middle;
}

.info-block {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
  max-width: 800px;
}

.info-block-label {
  font-weight: 500;
  color: #666;
  font-size: 12px;
  margin-bottom: 4px;
}

.info-block-text {
  background: #f9f9f9;
  padding: 8px 10px;
  border-radius: 4px;
  font-size: 13px;
  color: #333;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.4;
}

.info-value .a-under + .a-under {
  margin-left: 10px;
}

.image-modal-body {
  padding: 15px;
  max-height: 500px;
  overflow-y: auto;
}

.details-section {
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;

  &:last-child {
    border-bottom: none;
    margin-bottom: 0;
  }
}

.section-title {
  font-weight: 600;
  color: #049372;
  font-size: 13px;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-row {
  display: flex;
  margin-bottom: 4px;
}

.detail-label {
  font-weight: 600;
  color: #333;
  min-width: 140px;
  flex-shrink: 0;
  font-size: 13px;
}

.dynamic-red {
  color: #ff6b6b;
  font-weight: bold;
}

.detail-value {
  color: #666;
  margin-left: 8px;
  flex: 1;
  font-size: 13px;
  word-break: break-word;

  &.small-text {
    font-size: 11px;
    font-family: 'Courier New', monospace;
  }

  &.empty-value {
    color: #999;
    font-style: italic;
  }
}
</style>
