<template>
  <PageInnerLayout>
    <TwoSidedLayout :left-width-px="301">
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
              :top-height-px="36"
              no-border
            >
              <template #top>
                <DateFieldNav
                  :def="date"
                  :val.sync="date"
                  w="100%"
                />
              </template>
              <template #bottom>
                <TopBottomLayout :top-height-percent="70">
                  <template #top>
                    <div class="requests-list">
                      <div class="requests-list__header">
                        <div class="requests-list__header-content">
                          <span>Ожидают</span>
                          <div class="requests-list__filter">
                            <button
                              class="filter-btn"
                              :class="{ 'filter-btn--active': !showAccepted }"
                              @click="showAccepted = false"
                            >
                              {{ `Все (${requestsWait.length})` }}
                            </button>
                            <button
                              class="filter-btn"
                              :class="{ 'filter-btn--active': showAccepted }"
                              @click="showAccepted = true"
                            >
                              {{ `Принятые (${requestsWait.filter(request => request.accepted).length})` }}
                            </button>
                            <button
                              class="filter-btn"
                              :class="{ 'filter-btn--active': isSearchMode }"
                              title="поиск по пациенту"
                              @click="isSearchMode = !isSearchMode"
                            >
                              <i class="fa fa-search" />
                            </button>
                          </div>
                        </div>
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
                        <div
                          v-if="isSearchMode"
                          class="requests-list__search"
                        >
                          <input
                            v-model.trim="patientQuery"
                            type="text"
                            class="form-control"
                            placeholder="поиск по пациенту"
                          >
                        </div>
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
                          v-for="request in requestsDone"
                          :key="request.id"
                          :request="request"
                          :hospital-id="selectedHospitalId"
                          @card-clicked="handleCardClick"
                        />
                        <div
                          v-if="requestsDone.length === 0"
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
        />
      </template>
    </TwoSidedLayout>
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

import ResultsParaclinic from '@/pages/ResultsParaclinic.vue';
import PageInnerLayout from '@/layouts/PageInnerLayout.vue';
import TwoSidedLayout from '@/layouts/TwoSidedLayout.vue';
import TopBottomLayout from '@/layouts/TopBottomLayout.vue';
import DateFieldNav from '@/fields/DateFieldNav.vue';
import api from '@/api';
import directionsPoint from '@/api/directions-point';
import useLoader from '@/hooks/useLoader';
import useOn from '@/hooks/useOn';

import RequestCard, { type Request } from './RequestCard.vue';

interface Hospital {
  id: number;
  label: string;
}

const date = ref(moment().format('DD.MM.YYYY'));
const hospitals = ref<Hospital[]>([]);
const selectedHospitalId = ref<number>(-1);
const hospitalsLoading = ref(false);
const requestsDone = ref<Request[]>([]);
const requestsWait = ref<Request[]>([]);
const initialLoading = ref(false);
const showAccepted = ref(false);
const selectedRequest = ref<Request | null>(null);
const formData = ref<any>(null);
const formLoading = ref(false);
const requestParams = ref<any>(null);
const numberToSearch = ref<string>('');
const isSearchMode = ref(false);
const patientQuery = ref<string>('');
let refreshInterval: any = null;

const loader = useLoader();

const filteredWaitRequests = computed(() => {
  const base = showAccepted.value
    ? requestsWait.value.filter(request => request.accepted)
    : requestsWait.value;

  const query = patientQuery.value.trim().toLowerCase();
  if (!query) return base;
  return base.filter(request => request.patient.toLowerCase().includes(query));
});

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
    console.error('Ошибка загрузки организаций:', error);
  } finally {
    loader.global.dec();
    hospitalsLoading.value = false;
  }
};

const loadRequestsByStatus = async (isDone: boolean) => {
  try {
    const response = await api('requests/by-status', {
      date: date.value,
      isDone,
      hospitalId: selectedHospitalId.value,
    });

    if (response.rows) {
      return response.rows;
    }
    return [];
  } catch (error) {
    return [];
  }
};

const loadAllRequests = async () => {
  const [waitRequests, doneRequests] = await Promise.all([
    loadRequestsByStatus(false),
    loadRequestsByStatus(true),
  ]);

  requestsWait.value = waitRequests;
  requestsDone.value = doneRequests;
};

useOn('change-document-state', loadAllRequests);
useOn('close-results-paraclinic', () => {
  selectedRequest.value = null;
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

watch(date, () => {
  loadAllRequests();
});

watch(selectedHospitalId, () => {
  selectedRequest.value = null;
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

.requests-list__header-content {
  display: flex;
  align-items: center;
  gap: 5px;
}

.requests-list__filter {
  display: flex;
  gap: 5px;
}

.filter-btn {
  padding: 4px 8px;
  border: 1px solid #ccc;
  border-radius: 6px;
  background-color: #fff;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s ease;
  color: #666;

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
}

.requests-list__items {
  padding: 5px;
}

.requests-list__search {
  position: sticky;
  top: 0;
  z-index: 2;
  background: #ffffff;
  padding-bottom: 5px;
}

.requests-list__search input {
  width: 100%;
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
  max-width: calc(100vw - 300px);
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
</style>
