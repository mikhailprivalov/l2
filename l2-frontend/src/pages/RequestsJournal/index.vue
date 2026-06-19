<template>
  <div class="requests-journal">
    <div class="filters-sticky">
      <div class="panel panel-default panel-flt filters-panel">
        <div
          class="panel-body"
          style="overflow: visible;"
        >
          <div class="row filter-row filter-row--first">
            <div class="col-xs-6">
              <div class="input-group treeselect-noborder-left">
                <span class="input-group-addon">Больница</span>
                <Treeselect
                  v-model="filters.hospitalId"
                  :multiple="false"
                  :disable-branch-nodes="true"
                  :options="hospitals"
                  placeholder="Все"
                  :clearable="false"
                  class="treeselect-wide"
                  :append-to-body="true"
                />
              </div>
            </div>
            <div class="col-xs-6">
              <div class="input-group treeselect-noborder-left">
                <span class="input-group-addon">Врач</span>
                <Treeselect
                  v-model="filters.doctorId"
                  :multiple="false"
                  :disable-branch-nodes="true"
                  :options="doctors"
                  placeholder="Все"
                  :clearable="false"
                  class="treeselect-wide"
                  :append-to-body="true"
                />
              </div>
            </div>
          </div>
          <div class="row filter-row filter-row--second">
            <div class="col-xs-6">
              <div class="status-filters">
                <span class="status-filters__label">Статус:</span>
                <label
                  v-for="status in statusOptions"
                  :key="status.id"
                  class="status-filter"
                >
                  <input
                    v-model="selectedStatuses"
                    type="checkbox"
                    :value="status.id"
                  >
                  {{ status.label }}
                </label>
                <a
                  class="a-under status-filters__reset"
                  href="#"
                  @click.prevent="resetFilters"
                >Сбросить</a>
              </div>
            </div>
            <div class="col-xs-6">
              <div class="filter-row__right">
                <div class="input-group treeselect-noborder-left journal-date-filter">
                  <span class="input-group-addon">Дата</span>
                  <div class="journal-date-filter__body">
                    <DateRange v-model="dateRange" />
                  </div>
                </div>
                <div class="filters-pagination">
                  <select
                    v-model.number="pageSize"
                    class="form-control page-size-select"
                  >
                    <option
                      v-for="size in pageSizeOptions"
                      :key="size"
                      :value="size"
                    >
                      {{ size }}
                    </option>
                  </select>
                  <Paginate
                    v-model="page"
                    :page-count="pages"
                    :page-range="3"
                    :margin-pages="1"
                    :click-handler="load"
                    prev-text="Назад"
                    next-text="Вперёд"
                    container-class="pagination"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="loading && !loaded"
      class="not-loaded"
    >
      Загрузка...
    </div>
    <div
      v-else
      class="data"
    >
      <table class="table table-bordered table-condensed table-hover table-list">
        <colgroup>
          <col>
          <col>
          <col width="72">
          <col width="24%">
          <col>
          <col>
          <col>
          <col>
          <col>
        </colgroup>
        <thead>
          <tr>
            <th>Больница</th>
            <th class="table-list__patient">
              <div class="table-list__patient-label">
                ФИО пациента
              </div>
              <input
                v-model.trim="patientQuery"
                type="text"
                class="form-control input-sm table-list__patient-input"
                placeholder="поиск"
                @click.stop
              >
            </th>
            <th>№ заявки</th>
            <th>Услуга</th>
            <th>ФИО врача</th>
            <th
              class="table-list__sortable"
              @click="toggleSort('created')"
            >
              Создана
              <i :class="sortIcon('created')" />
            </th>
            <th
              class="table-list__sortable"
              @click="toggleSort('accepted')"
            >
              Принята
              <i :class="sortIcon('accepted')" />
            </th>
            <th
              class="table-list__sortable"
              @click="toggleSort('confirmed')"
            >
              Исполнена
              <i :class="sortIcon('confirmed')" />
            </th>
            <th
              class="table-list__sortable"
              @click="toggleSort('status')"
            >
              Статус
              <i :class="sortIcon('status')" />
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in rows"
            :key="row.id"
            :class="{ 'row-cito': row.cito }"
          >
            <td>{{ row.hospital }}</td>
            <td>{{ row.patient }}</td>
            <td>
              <a
                class="a-under"
                :href="getDescriptiveHref(row.id)"
              >{{ row.id }}</a>
            </td>
            <td>{{ row.research || '—' }}</td>
            <td>{{ row.doctorFio }}</td>
            <td>{{ row.createdAt }}</td>
            <td>{{ row.acceptedAt || '—' }}</td>
            <td>{{ row.confirmedAt || '—' }}</td>
            <td :class="statusCellClass(row.status)">
              <span
                v-if="row.cito"
                class="cito-badge"
              >CITO</span>
              {{ row.status }}
            </td>
          </tr>
          <tr v-if="rows.length === 0">
            <td
              colspan="9"
              class="text-center"
            >
              нет данных
            </td>
          </tr>
        </tbody>
      </table>
      <div class="pagination-row">
        <div class="pagination-controls">
          <select
            v-model.number="pageSize"
            class="form-control page-size-select"
          >
            <option
              v-for="size in pageSizeOptions"
              :key="size"
              :value="size"
            >
              {{ size }}
            </option>
          </select>
          <Paginate
          v-model="page"
          :page-count="pages"
          :page-range="4"
          :margin-pages="2"
          :click-handler="load"
          prev-text="Назад"
          next-text="Вперёд"
          container-class="pagination"
        />
        </div>
      </div>
      <div class="founded">
        Найдено записей: <strong>{{ total }}</strong>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  onMounted,
  ref,
  watch,
} from 'vue';
import moment from 'moment';
import _ from 'lodash';
import Treeselect from '@riophae/vue-treeselect';
import Paginate from 'vuejs-paginate';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import DateRange from '@/ui-cards/DateRange.vue';
import api from '@/api';
import useNotify from '@/hooks/useNotify';

interface FilterOption {
  id: number;
  label: string;
}

interface JournalRow {
  id: number;
  hospital: string;
  patient: string;
  research: string;
  doctorFio: string;
  createdAt: string;
  acceptedAt: string | null;
  confirmedAt: string | null;
  status: string;
  cito: boolean;
}

const pageSizeOptions = [50, 100, 150];

type SortField = 'created' | 'accepted' | 'confirmed' | 'status';
type SortDir = 'asc' | 'desc';

const statusOptions = [
  { id: 'new', label: 'Новые' },
  { id: 'cito', label: 'CITO' },
  { id: 'accepted', label: 'В работе' },
  { id: 'confirmed', label: 'Исполнены' },
];

const getDefaultDateRange = (): [string, string] => [
  moment().subtract(10, 'days').format('DD.MM.YYYY'),
  moment().format('DD.MM.YYYY'),
];

const notify = useNotify();

const maxPeriodDays = ref(40);
const selectedStatuses = ref<string[]>([]);
const dateRange = ref<[string, string]>(getDefaultDateRange());
const filters = ref({
  hospitalId: -1,
  doctorId: -1,
});
const hospitals = ref<FilterOption[]>([{ id: -1, label: 'Все' }]);
const doctors = ref<FilterOption[]>([{ id: -1, label: 'Все' }]);
const rows = ref<JournalRow[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(50);
const patientQuery = ref('');
const sortBy = ref<SortField | ''>('');
const sortDir = ref<SortDir>('desc');
const loaded = ref(false);
const loading = ref(false);

const pages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)));

const getDescriptiveHref = (pk: number) => (
  `/ui/results/descriptive#${encodeURIComponent(JSON.stringify({ pk }))}`
);

const sortIcon = (field: SortField) => {
  if (sortBy.value !== field) {
    return 'fa fa-sort table-list__sort-icon table-list__sort-icon--inactive';
  }
  return sortDir.value === 'asc'
    ? 'fa fa-sort-asc table-list__sort-icon'
    : 'fa fa-sort-desc table-list__sort-icon';
};

const statusCellClass = (status: string) => {
  if (status === 'CITO') {
    return 'table-list__status--cito';
  }
  if (status === 'В работе') {
    return 'table-list__status--accepted';
  }
  if (status === 'Исполнена') {
    return 'table-list__status--confirmed';
  }
  return '';
};

const clampDateRange = (): boolean => {
  const from = moment(dateRange.value[0], 'DD.MM.YYYY', true);
  const to = moment(dateRange.value[1], 'DD.MM.YYYY', true);

  if (!from.isValid() || !to.isValid()) {
    return true;
  }

  const start = from.isAfter(to) ? to : from;
  const end = from.isAfter(to) ? from : to;

  if (end.diff(start, 'days') <= maxPeriodDays.value) {
    if (from.isAfter(to)) {
      dateRange.value = [start.format('DD.MM.YYYY'), end.format('DD.MM.YYYY')];
      return true;
    }
    return false;
  }

  notify.error(`Период не может превышать ${maxPeriodDays.value} дней`);
  dateRange.value = [
    end.clone().subtract(maxPeriodDays.value, 'days').format('DD.MM.YYYY'),
    end.format('DD.MM.YYYY'),
  ];
  return true;
};

const isDateRangeValid = () => {
  const from = moment(dateRange.value[0], 'DD.MM.YYYY', true);
  const to = moment(dateRange.value[1], 'DD.MM.YYYY', true);
  return from.isValid() && to.isValid();
};

const load = async (targetPage = 1) => {
  if (!isDateRangeValid()) {
    return;
  }

  const normalizedRange = [
    moment(dateRange.value[0], 'DD.MM.YYYY').format('DD.MM.YYYY'),
    moment(dateRange.value[1], 'DD.MM.YYYY').format('DD.MM.YYYY'),
  ];

  page.value = targetPage;
  loading.value = true;

  try {
    const response = await api('requests/all-list', {
      hospitalId: filters.value.hospitalId,
      doctorId: filters.value.doctorId,
      statuses: selectedStatuses.value,
      dateFrom: normalizedRange[0],
      dateTo: normalizedRange[1],
      patientQuery: patientQuery.value,
      sortBy: sortBy.value,
      sortDir: sortDir.value,
      offset: (targetPage - 1) * pageSize.value,
      limit: pageSize.value,
    });

    if (response.error) {
      notify.error(response.error);
      return;
    }

    if (response.maxPeriodDays) {
      maxPeriodDays.value = response.maxPeriodDays;
    }

    rows.value = response.rows || [];
    total.value = response.total || 0;
    hospitals.value = response.hospitals || [{ id: -1, label: 'Все' }];
    doctors.value = response.doctors || [{ id: -1, label: 'Все' }];
    loaded.value = true;
  } catch (error) {
    notify.error('Ошибка загрузки журнала заявок');
    // eslint-disable-next-line no-console
    console.error('Ошибка загрузки журнала заявок:', error);
  } finally {
    loading.value = false;
  }
};

const toggleSort = (field: SortField) => {
  if (sortBy.value === field) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortBy.value = field;
    sortDir.value = 'asc';
  }
  load(1);
};

const debouncedLoad = _.debounce(() => {
  load(1);
}, 300);

const onFiltersChange = () => {
  if (clampDateRange()) {
    return;
  }
  debouncedLoad();
};

const resetFilters = () => {
  selectedStatuses.value = [];
  dateRange.value = getDefaultDateRange();
  patientQuery.value = '';
  sortBy.value = '';
  sortDir.value = 'desc';
  filters.value = {
    hospitalId: -1,
    doctorId: -1,
  };
};

watch(selectedStatuses, onFiltersChange, { deep: true });
watch(() => filters.value.hospitalId, onFiltersChange);
watch(() => filters.value.doctorId, onFiltersChange);
watch(dateRange, onFiltersChange, { deep: true });
watch(patientQuery, onFiltersChange);
watch(pageSize, () => {
  load(1);
});

onMounted(() => {
  load(1);
});
</script>

<style lang="scss" scoped>
.requests-journal {
  padding: 0 6px 6px;
}

.filters-sticky {
  position: sticky;
  top: 0;
  z-index: 20;
  background: #f5f5f5;
  padding-bottom: 2px;
}

.filters-panel {
  margin: 0;

  .panel-body {
    padding: 4px 6px;
  }
}

.filter-row {
  &--first {
    margin-bottom: 4px;
  }

  &__right {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    flex-wrap: wrap;
    min-height: 34px;
    width: 100%;
  }
}

.filters-pagination {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex: 1 1 auto;
  margin-left: auto;

  :deep(.pagination) {
    margin: 0;
  }
}

.page-size-select {
  width: auto;
  min-width: 58px;
  height: 26px;
  padding: 2px 6px;
  flex: 0 0 auto;
}

.status-filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 12px;
  min-height: 34px;

  &__label {
    font-weight: 600;
  }

  &__reset {
    white-space: nowrap;
  }
}

.status-filter {
  margin: 0;
  font-weight: normal;
  cursor: pointer;
  white-space: nowrap;

  input {
    margin-right: 4px;
  }
}

.journal-date-filter {
  width: auto;
  max-width: 100%;

  &__body {
    flex: 0 0 auto;
    display: flex;

    :deep(.input-daterange) {
      display: inline-flex;
      width: auto;
      margin: 0;

      .form-control {
        width: 80px;
        height: 34px;
        padding: 5px;
        border-radius: 0;
      }

      .form-control:first-child {
        border-left: none;
      }

      .form-control:last-child {
        border-radius: 0 4px 4px 0;
      }

      > .input-group-addon {
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 24px;
        height: 34px;
        padding: 5px 6px;
        border-radius: 0;
      }
    }
  }
}

.not-loaded {
  text-align: center;
  color: grey;
  padding: 20px;
}

.data {
  margin-top: 4px;
}

.pagination-row {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  margin-top: 8px;
  margin-bottom: 4px;
}

.pagination-controls {
  display: inline-flex;
  align-items: center;
  gap: 8px;

  :deep(.pagination) {
    margin: 0;
  }
}

.founded {
  text-align: center;
  padding: 5px;
}

.table-list {
  table-layout: fixed;
  margin-bottom: 0;

  td:nth-child(3) {
    text-align: center;
    white-space: nowrap;
  }

  td:nth-child(4) {
    word-break: break-word;
  }

  &__patient {
    vertical-align: top;
  }

  &__patient-label {
    margin-bottom: 4px;
    white-space: nowrap;
  }

  &__patient-input {
    height: 24px;
    padding: 2px 6px;
    font-size: 12px;
  }

  &__sortable {
    cursor: pointer;
    user-select: none;
    white-space: nowrap;
  }

  &__sort-icon {
    margin-left: 4px;
    font-size: 11px;

    &--inactive {
      opacity: 0.45;
    }
  }

  &__status--cito {
    border-right: 3px solid #d9534f;
  }

  &__status--accepted {
    border-right: 3px solid #046d93;
  }

  &__status--confirmed {
    border-right: 3px solid #049372;
  }
}

.row-cito {
  background-color: #fff8f0;
}

.cito-badge {
  display: inline-block;
  margin-right: 4px;
  padding: 0 4px;
  border-radius: 2px;
  background: #d9534f;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  vertical-align: middle;
}
</style>
