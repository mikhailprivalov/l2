<template>
  <PageInnerLayout>
    <TwoSidedLayout :left-width-px="300">
      <template #left>
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
            <TopBottomLayout split-half>
              <template #top>
                <div class="requests-list">
                  <div class="requests-list__header">
                    <div class="requests-list__header-content">
                      <span>Ожидающие</span>
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
                    <RequestCard
                      v-for="request in filteredWaitRequests"
                      :key="request.id"
                      :request="request"
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
      <template #right>
        <div class="results-editor">
          <div
            v-if="formData && formData.researches && formData.researches.length > 0"
            class="form-container"
          >
            <div class="form-header">
              <p class="patient-info">
                {{ formData.direction.pk }} {{ formData.patient.fio_age }}
              </p>
              <!-- <div
                v-if="requestParams"
                class="request-params"
              >
                <div class="params-grid">
                  <div
                    v-for="(value, key) in requestParams"
                    :key="key"
                    class="param-item"
                  >
                    <span class="param-label">{{ key }}:</span>
                    <span class="param-value">{{ value }}</span>
                  </div>
                </div>
              </div> -->
            </div>
            <div class="form-content">
              <div
                v-for="research in formData.researches"
                :key="research.pk"
              >
                <div class="research-title">
                  <div class="research-left">
                    {{ research.research.title }}
                    <span
                      v-if="research.research.comment"
                      class="comment"
                    > [{{ research.research.comment }}]</span>
                  </div>
                  <div class="research-right">
                    <template v-if="research.confirmed">
                      <button
                        class="btn btn-blue-nb"
                        @click="printResults(selectedRequest.id)"
                      >
                        Печать
                      </button>
                    </template>
                  </div>
                </div>
                <DescriptiveForm
                  :research="research.research"
                  :pk="research.pk"
                  :confirmed="Boolean(!!research.confirmed || !!research.forbidden_edit)"
                  :patient="formData.patient"
                  :change_mkb="() => {}"
                  :hospital_r_type="'desc'"
                />
                <div class="control-row">
                  <div class="res-title">
                    {{ research.research.title }}:
                  </div>
                  <div v-if="research.confirmed">
                    <span class="status status-confirmed">Подтверждено</span>
                  </div>
                  <div v-else>
                    <span class="status status-none">Не подтверждено</span>
                  </div>
                  <template v-if="!research.confirmed">
                    <button
                      class="btn btn-blue-nb"
                      @click="saveResearch(research)"
                    >
                      Сохранить
                    </button>
                    <button
                      class="btn btn-blue-nb"
                      @click="saveAndConfirmResearch(research)"
                    >
                      Сохранить и подтвердить
                    </button>
                  </template>
                  <template v-else>
                    <button
                      v-if="research.allow_reset_confirm"
                      class="btn btn-blue-nb"
                      @click="resetConfirmResearch(research)"
                    >
                      Сброс подтверждения
                    </button>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </TwoSidedLayout>
  </PageInnerLayout>
</template>

<script setup lang="ts">
import {
  computed,
  getCurrentInstance,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from 'vue';
import moment from 'moment';

import PageInnerLayout from '@/layouts/PageInnerLayout.vue';
import TwoSidedLayout from '@/layouts/TwoSidedLayout.vue';
import TopBottomLayout from '@/layouts/TopBottomLayout.vue';
import DateFieldNav from '@/fields/DateFieldNav.vue';
import DescriptiveForm from '@/forms/DescriptiveForm.vue';
import api from '@/api';
import directionsPoint from '@/api/directions-point';
import usePrint from '@/hooks/usePrint';
import useNotify from '@/hooks/useNotify';
import useLoader from '@/hooks/useLoader';
import { vField, vGroup } from '@/components/visibility-triggers';

import RequestCard, { type Request } from './RequestCard.vue';

const root = getCurrentInstance().proxy.$root;
const date = ref(moment().format('DD.MM.YYYY'));
const requestsDone = ref<Request[]>([]);
const requestsWait = ref<Request[]>([]);
const initialLoading = ref(false);
const showAccepted = ref(false);
const selectedRequest = ref<Request | null>(null);
const formData = ref<any>(null);
const formLoading = ref(false);
const requestParams = ref<any>(null);
let refreshInterval: any = null;

const loader = useLoader();

const { printResults: doPrintResults } = usePrint();
const notify = useNotify();

const filteredWaitRequests = computed(() => {
  if (showAccepted.value) {
    return requestsWait.value.filter(request => request.accepted);
  }
  return requestsWait.value;
});

const loadRequestsByStatus = async (isDone: boolean) => {
  try {
    const response = await api('requests/by-status', {
      date: date.value,
      isDone,
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

const startAutoRefresh = () => {
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }
  refreshInterval = setInterval(() => {
    loadAllRequests();
  }, 30000);
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

const printResults = (requestId: number) => {
  doPrintResults([requestId]);
};

const visibilityState = (research: any) => {
  const groups = {};
  const fields = {};
  const { groups: igroups } = research.research;

  for (const group of research.research.groups) {
    if (!vGroup(group, igroups, formData.value.patient)) {
      groups[group.pk] = false;
    } else {
      groups[group.pk] = true;
      for (const field of group.fields) {
        fields[field.pk] = vField(group, igroups, field.visibility, formData.value.patient);
      }
    }
  }

  return {
    groups,
    fields,
  };
};

const saveResearch = async (research: any) => {
  if (!formData.value) return;

  try {
    const response = await directionsPoint.paraclinicResultSave({
      data: {
        ...research,
        direction: {
          pk: selectedRequest.value.id,
          all_confirmed: false,
        },
      },
      with_confirm: false,
      visibility_state: visibilityState(research),
    });

    if (response.ok) {
      notify.ok('Сохранено');
      loadFormData(selectedRequest.value.id);
      loadAllRequests();
    } else {
      notify.error(response.message);
    }
  } catch (error) {
    notify.error('Ошибка сохранения');
  }
};

const saveAndConfirmResearch = async (research: any) => {
  if (!formData.value) return;

  try {
    const response = await directionsPoint.paraclinicResultSave({
      data: {
        ...research,
        direction: {
          pk: selectedRequest.value.id,
          all_confirmed: false,
        },
      },
      with_confirm: true,
      visibility_state: visibilityState(research),
    });

    if (response.ok) {
      notify.ok('Сохранено');
      notify.ok('Подтверждено');
      loadFormData(selectedRequest.value.id);
      loadAllRequests();
    } else {
      notify.error(response.message);
    }
  } catch (error) {
    notify.error('Ошибка сохранения и подтверждения');
  }
};

const resetConfirmResearch = async (research: any) => {
  if (!formData.value) return;

  try {
    try {
      await root.$dialog.confirm(`Подтвердите сброс подтверждения услуги «${research.research.title}»`);
    } catch (_) {
      return;
    }

    loader.inc();
    const response = await directionsPoint.paraclinicResultConfirmReset({
      iss_pk: research.pk,
    });

    if (response.ok) {
      notify.ok('Подтверждение сброшено');
      loadFormData(selectedRequest.value.id);
      loadAllRequests();
    } else {
      notify.error(response.message);
    }
  } catch (error) {
    notify.error('Ошибка сброса подтверждения');
  } finally {
    loader.dec();
  }
};

watch(date, () => {
  loadAllRequests();
});

onMounted(() => {
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
</style>
