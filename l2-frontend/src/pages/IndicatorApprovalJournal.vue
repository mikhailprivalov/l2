<template>
  <div>
    <form
      class="panel panel-default panel-flt"
      style="margin: 20px;"
      @submit.prevent="load"
    >
      <div
        class="panel-body"
        style="overflow: visible;"
      >
        <div
          class="row"
          style="margin-top:5px;"
        >
          <div class="col-xs-6">
            <div class="date-filter">
              <label class="date-filter__addon">
                <input
                  v-model="filterByDate"
                  type="checkbox"
                >
              </label>
              <span class="date-filter__addon">Дата</span>
              <input
                ref="dateFrom"
                class="date-filter__input"
                type="text"
                maxlength="10"
                :value="dateRange[0]"
                @change="onPeriodDateChange(0, $event)"
              >
              <button
                type="button"
                class="date-filter__clear"
                title="Очистить дату начала"
                @click="clearPeriodDate(0)"
              >
                ×
              </button>
              <input
                ref="dateTo"
                class="date-filter__input"
                type="text"
                maxlength="10"
                :value="dateRange[1]"
                @change="onPeriodDateChange(1, $event)"
              >
              <button
                type="button"
                class="date-filter__clear"
                title="Очистить дату окончания"
                @click="clearPeriodDate(1)"
              >
                ×
              </button>
            </div>
          </div>
        </div>
      </div>
    </form>
    <div
      v-if="!loaded"
      class="not-loaded"
    >
      Данные не загружены<br>
      <a
        class="a-under"
        href="#"
        @click.prevent="load"
      >загрузить</a>
    </div>
    <div
      v-else
      class="data"
    >
      <div class="sort-bar">
        <span class="sort-bar__label">Сортировка</span>
        <select
          class="form-control input-sm"
          :value="sortPrimaryKey"
          @change="setSortKey(0, $event)"
        >
          <option value="">
            нет
          </option>
          <option
            v-for="col in SORT_COLUMNS"
            :key="col.key"
            :value="col.key"
          >
            {{ col.label }}
          </option>
        </select>
        <button
          type="button"
          class="btn btn-default btn-sm"
          :disabled="!sortPrimaryKey"
          @click.prevent="toggleLevelDir(0)"
        >
          {{ sortPrimaryDir === 'desc' ? '▼' : '▲' }}
        </button>
        <span class="sort-bar__label">затем</span>
        <select
          class="form-control input-sm"
          :value="sortSecondaryKey"
          :disabled="!sortPrimaryKey"
          @change="setSortKey(1, $event)"
        >
          <option value="">
            нет
          </option>
          <option
            v-for="col in secondarySortColumns"
            :key="col.key"
            :value="col.key"
          >
            {{ col.label }}
          </option>
        </select>
        <button
          type="button"
          class="btn btn-default btn-sm"
          :disabled="!sortSecondaryKey"
          @click.prevent="toggleLevelDir(1)"
        >
          {{ sortSecondaryDir === 'desc' ? '▼' : '▲' }}
        </button>
        <button
          v-if="sortLevels.length"
          type="button"
          class="btn btn-link btn-sm sort-bar__reset"
          @click="clearSort"
        >
          сбросить
        </button>
      </div>
      <table class="table table-bordered table-condensed table-hover table-list">
        <colgroup>
          <col style="width: calc(170px + (100% - 880px) * 105 / 132)">
          <col style="width: calc((2 / 3) * (140px + (100% - 880px) * 140 / 1320))">
          <col style="width: calc((2 / 3) * (160px + (100% - 880px) * 160 / 1320))">
          <col style="width: calc((1 / 2) * (140px + (100% - 880px) * 140 / 1320))">
          <col style="width: 220px">
          <col style="width: 220px">
        </colgroup>
        <thead>
          <tr>
            <th
              class="sortable"
              @click="toggleSort('hospital')"
            >
              Больница
              <span
                v-if="sortMark('hospital')"
                class="sort-mark"
              >{{ sortMark('hospital') }}</span>
            </th>
            <th
              class="sortable"
              @click="toggleSort('documentId')"
            >
              Номер документа
              <span
                v-if="sortMark('documentId')"
                class="sort-mark"
              >{{ sortMark('documentId') }}</span>
            </th>
            <th
              class="sortable"
              @click="toggleSort('confirmDate')"
            >
              Дата подтверждения
              <span
                v-if="sortMark('confirmDate')"
                class="sort-mark"
              >{{ sortMark('confirmDate') }}</span>
            </th>
            <th
              class="sortable"
              @click="toggleSort('status')"
            >
              Статус
              <span
                v-if="sortMark('status')"
                class="sort-mark"
              >{{ sortMark('status') }}</span>
            </th>
            <th
              class="sortable"
              @click="toggleSort('linked')"
            >
              Связный документ
              <span
                v-if="sortMark('linked')"
                class="sort-mark"
              >{{ sortMark('linked') }}</span>
            </th>
            <th
              class="sortable"
              @click="toggleSort('sign')"
            >
              Подпись
              <span
                v-if="sortMark('sign')"
                class="sort-mark"
              >{{ sortMark('sign') }}</span>
            </th>
          </tr>
          <tr>
            <th>
              <Treeselect
                v-model="columnFilters.hospital"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="hospitalFilterOptions"
                placeholder="Все"
                :clearable="true"
                class="treeselect-wide"
              />
            </th>
            <th>
              <Treeselect
                v-model="columnFilters.documentId"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="documentIdFilterOptions"
                placeholder="Все"
                :clearable="true"
                class="treeselect-wide"
              />
            </th>
            <th>
              <Treeselect
                v-model="columnFilters.confirmDate"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="confirmDateFilterOptions"
                placeholder="Все"
                :clearable="true"
                class="treeselect-wide"
              />
            </th>
            <th>
              <Treeselect
                v-model="columnFilters.status"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="statusFilterOptions"
                placeholder="Все"
                :clearable="true"
                class="treeselect-wide"
              />
            </th>
            <th>
              <Treeselect
                v-model="columnFilters.linked"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="linkedFilterOptions"
                placeholder="Все"
                :clearable="true"
                class="treeselect-wide"
              />
            </th>
            <th>
              <Treeselect
                v-model="columnFilters.sign"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="signFilterOptions"
                placeholder="Все"
                :clearable="true"
                class="treeselect-wide"
              />
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in filteredRows"
            :key="row.documentId"
          >
            <td>{{ row.hospital }}</td>
            <td>
              <a
                class="a-under"
                :href="documentHref(row.documentId)"
                target="_blank"
              >{{ row.documentId }}</a>
            </td>
            <td>{{ row.confirmDate || '–' }}</td>
            <td class="status-cell">
              <span
                v-if="row.approved"
                class="status-cell__approved"
              >Утвержден</span>
              <span v-else>–</span>
            </td>
            <td>
              <div
                v-for="document in row.linkedDocuments"
                :key="document.id"
              >
                <a
                  class="a-under"
                  href="#"
                  @click.prevent="openLinked(row, document)"
                >{{ document.title }}</a>
              </div>
              <button
                v-if="!row.linkedDocuments.length"
                type="button"
                class="btn btn-blue-nb btn-sm"
                :disabled="linkingId === row.documentId || signingId === row.documentId"
                @click="createLinked(row)"
              >
                Связный документ
              </button>
            </td>
            <td>
              <template v-if="row.sign">
                <div>Подписан {{ row.sign.signedAt }} {{ row.sign.fio }}</div>
                <button
                  type="button"
                  class="btn btn-blue-nb btn-sm"
                  :disabled="resettingId === row.documentId"
                  @click="resetSign(row)"
                >
                  Сбросить
                </button>
              </template>
              <button
                v-else-if="row.approved"
                type="button"
                class="btn btn-blue-nb btn-sm"
                :disabled="signingId === row.documentId || linkingId === row.documentId"
                @click="sign(row)"
              >
                Подписать
              </button>
              <span v-else>–</span>
            </td>
          </tr>
          <tr v-if="filteredRows.length === 0">
            <td
              colspan="6"
              class="text-center"
            >
              не найдено
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <Modal
      v-if="signOpen"
      show-footer="true"
      white-bg="true"
      min-width="640px"
      @close="closeSign"
    >
      <span slot="header">Подписать</span>
      <div
        slot="body"
        class="sign-body"
      >
        <div v-if="!signChecked">
          загрузка
        </div>
        <div
          v-else-if="!signHasPlugin"
          class="status-error"
        >
          Плагин CSP не настроен
        </div>
        <template v-else>
          <select
            v-if="signCertificates.length"
            v-model="selectedThumbprint"
            class="form-control"
          >
            <option
              v-for="certificate in signCertificates"
              :key="certificate.thumbprint"
              :value="certificate.thumbprint"
            >
              {{ certificate.name }}
            </option>
          </select>
          <div
            v-else
            class="status-error"
          >
            Нет сертификатов
          </div>
          <div
            v-if="selectedCertificate"
            class="sign-body__cert"
          >
            <div>{{ selectedCertificate.thumbprint }}</div>
            <div>{{ selectedCertificate.validFrom }} — {{ selectedCertificate.validTo }}</div>
          </div>
        </template>
      </div>
      <div
        slot="footer"
        class="sign-footer"
      >
        <button
          type="button"
          class="btn btn-blue-nb"
          @click="closeSign"
        >
          Закрыть
        </button>
        <button
          type="button"
          class="btn btn-blue-nb"
          :disabled="signBusy || !selectedThumbprint"
          @click="confirmSign"
        >
          Подписать
        </button>
      </div>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  getCurrentInstance,
  onBeforeUnmount,
  onMounted,
  reactive,
  ref,
  watch,
} from 'vue';
import moment from 'moment';
import {
  createDetachedSignature,
  createHash,
  getCertificate,
  getSystemInfo,
  getUserCertificates,
} from 'crypto-pro';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import api from '@/api';
import useNotify from '@/hooks/useNotify';
import { convertSubjectNameToTitle } from '@/utils';
import Modal from '@/ui-cards/Modal.vue';

interface LinkedDocument {
  id: number;
  title: string;
}

interface JournalSign {
  signedAt: string;
  fio: string;
}

interface JournalRow {
  documentId: number;
  hospital: string;
  confirmDate: string;
  approved: boolean;
  linkedDocuments: LinkedDocument[];
  sign: JournalSign | null;
}

interface SortLevel {
  key: string;
  dir: 'asc' | 'desc';
}

const SORT_COLUMNS = [
  { key: 'hospital', label: 'Больница' },
  { key: 'documentId', label: 'Номер документа' },
  { key: 'confirmDate', label: 'Дата подтверждения' },
  { key: 'status', label: 'Статус' },
  { key: 'linked', label: 'Связный документ' },
  { key: 'sign', label: 'Подпись' },
];

const NUMERIC_SORT_KEYS = new Set(['documentId']);

const makeOptions = (values: unknown[], numeric = false) => {
  const normalized = Array.from(new Set(
    values
      .map(value => String(value ?? '').trim())
      .filter(value => value !== ''),
  ));
  if (numeric) {
    normalized.sort((left, right) => Number(left) - Number(right));
  } else {
    normalized.sort((left, right) => left.localeCompare(right, 'ru'));
  }
  return normalized.map(value => ({ id: value, label: value }));
};

const normalizeFilterValue = (value: unknown) => {
  if (value === null || value === undefined) {
    return null;
  }
  const normalized = String(value).trim();
  if (normalized === '' || normalized.toLowerCase() === 'null' || normalized.toLowerCase() === 'undefined') {
    return null;
  }
  return normalized;
};

const isBlankSortValue = (value: unknown) => {
  const normalized = String(value ?? '').trim();
  return normalized === '' || normalized === '–' || normalized === '-' || normalized === '—';
};

const statusLabel = (row: JournalRow) => (row.approved ? 'Утвержден' : '–');

const linkedLabel = (row: JournalRow) => {
  const titles = (row.linkedDocuments || []).map(document => document.title).filter(title => title);
  return titles.length ? titles.join(', ') : '–';
};

const signLabel = (row: JournalRow) => (
  row.sign ? `Подписан ${row.sign.signedAt} ${row.sign.fio}`.trim() : '–'
);

const rowSortValue = (row: JournalRow, key: string) => {
  if (key === 'status') {
    return statusLabel(row);
  }
  if (key === 'linked') {
    return linkedLabel(row);
  }
  if (key === 'sign') {
    return signLabel(row);
  }
  return row[key as keyof JournalRow];
};

const parseRuDate = (value: unknown) => {
  const match = String(value ?? '').trim().match(/^(\d{2})\.(\d{2})\.(\d{4})$/);
  if (!match) {
    return null;
  }
  return Date.UTC(Number(match[3]), Number(match[2]) - 1, Number(match[1]));
};

const compareSortValues = (left: unknown, right: unknown, key: string) => {
  if (key === 'confirmDate') {
    const leftTime = parseRuDate(left);
    const rightTime = parseRuDate(right);
    if (leftTime !== null && rightTime !== null) {
      return leftTime - rightTime;
    }
  }
  if (NUMERIC_SORT_KEYS.has(key)) {
    const leftNumber = Number(String(left).trim().replace(',', '.'));
    const rightNumber = Number(String(right).trim().replace(',', '.'));
    return leftNumber - rightNumber;
  }
  return String(left).localeCompare(String(right), 'ru', { numeric: true, sensitivity: 'base' });
};

const compareRowsByKey = (left: JournalRow, right: JournalRow, key: string, dir: 'asc' | 'desc') => {
  const leftValue = rowSortValue(left, key);
  const rightValue = rowSortValue(right, key);
  const leftBlank = key !== 'status' && isBlankSortValue(leftValue);
  const rightBlank = key !== 'status' && isBlankSortValue(rightValue);
  if (leftBlank || rightBlank) {
    if (leftBlank && rightBlank) {
      return 0;
    }
    return leftBlank ? 1 : -1;
  }
  const direction = dir === 'asc' ? 1 : -1;
  return compareSortValues(leftValue, rightValue, key) * direction;
};

const notify = useNotify();
const root = getCurrentInstance()?.proxy?.$root as {
  $on: (event: string, handler: () => void) => void;
  $off: (event: string, handler: () => void) => void;
  $emit: (event: string, ...args: unknown[]) => void;
} | undefined;
const loaded = ref(false);
const rows = ref<JournalRow[]>([]);
const filterByDate = ref(true);
const dateRange = ref<[string, string]>([
  moment().subtract(40, 'days').format('DD.MM.YYYY'),
  moment().format('DD.MM.YYYY'),
]);
const dateFrom = ref<HTMLInputElement | null>(null);
const dateTo = ref<HTMLInputElement | null>(null);
const columnFilters = reactive({
  hospital: null as string | null,
  documentId: null as string | null,
  confirmDate: null as string | null,
  status: null as string | null,
  linked: null as string | null,
  sign: null as string | null,
});
const sortLevels = ref<SortLevel[]>([]);
interface SignCertificate {
  thumbprint: string;
  name: string;
  validFrom: string;
  validTo: string;
}

const signingId = ref(0);
const signOpen = ref(false);
const signRowId = ref(0);
const signPdf = ref('');
const signChecked = ref(false);
const signHasPlugin = ref(false);
const signCertificates = ref<SignCertificate[]>([]);
const selectedThumbprint = ref('');
const signBusy = ref(false);
const resettingId = ref(0);
const linkingId = ref(0);
const openingId = ref(0);

const sortPrimaryKey = computed(() => (sortLevels.value[0] ? sortLevels.value[0].key : ''));
const sortPrimaryDir = computed(() => (sortLevels.value[0] ? sortLevels.value[0].dir : 'asc'));
const sortSecondaryKey = computed(() => (sortLevels.value[1] ? sortLevels.value[1].key : ''));
const sortSecondaryDir = computed(() => (sortLevels.value[1] ? sortLevels.value[1].dir : 'asc'));
const secondarySortColumns = computed(() => SORT_COLUMNS.filter(column => column.key !== sortPrimaryKey.value));

const filteredRows = computed(() => {
  const filters = {
    hospital: normalizeFilterValue(columnFilters.hospital),
    documentId: normalizeFilterValue(columnFilters.documentId),
    confirmDate: normalizeFilterValue(columnFilters.confirmDate),
    status: normalizeFilterValue(columnFilters.status),
    linked: normalizeFilterValue(columnFilters.linked),
    sign: normalizeFilterValue(columnFilters.sign),
  };
  const hasFilters = Object.values(filters).some(value => value !== null);
  const filtered = hasFilters
    ? rows.value.filter(row => (
      (filters.hospital === null || String(row.hospital ?? '') === filters.hospital)
      && (filters.documentId === null || String(row.documentId) === filters.documentId)
      && (filters.confirmDate === null || String(row.confirmDate ?? '') === filters.confirmDate)
      && (filters.status === null || statusLabel(row) === filters.status)
      && (filters.linked === null || linkedLabel(row) === filters.linked)
      && (filters.sign === null || signLabel(row) === filters.sign)
    ))
    : rows.value;
  if (!sortLevels.value.length) {
    return filtered;
  }
  const levels = sortLevels.value;
  return filtered.slice().sort((left, right) => {
    for (let index = 0; index < levels.length; index += 1) {
      const level = levels[index];
      const result = compareRowsByKey(left, right, level.key, level.dir);
      if (result !== 0) {
        return result;
      }
    }
    return 0;
  });
});

const hospitalFilterOptions = computed(() => makeOptions(rows.value.map(row => row.hospital)));
const documentIdFilterOptions = computed(() => makeOptions(rows.value.map(row => row.documentId), true));
const confirmDateFilterOptions = computed(() => makeOptions(rows.value.map(row => row.confirmDate))
  .sort((left, right) => (parseRuDate(left.id) || 0) - (parseRuDate(right.id) || 0)));
const statusFilterOptions = computed(() => makeOptions(rows.value.map(row => statusLabel(row))));
const linkedFilterOptions = computed(() => makeOptions(rows.value.map(row => linkedLabel(row))));
const signFilterOptions = computed(() => makeOptions(rows.value.map(row => signLabel(row))));

const documentHref = (documentId: number) => `/ui/document-manager-2?document=${documentId}`;

const selectedCertificate = computed(() => (
  signCertificates.value.find(certificate => certificate.thumbprint === selectedThumbprint.value) || null
));

const rememberLinked = (documentId: number, document: LinkedDocument | null) => {
  if (!document) {
    return;
  }
  rows.value = rows.value.map(item => (
    item.documentId === documentId && !item.linkedDocuments.length
      ? { ...item, linkedDocuments: [document] }
      : item
  ));
};

const periodInputs = () => [dateFrom.value, dateTo.value];

const initPeriodDates = () => {
  const options = {
    format: 'dd.mm.yyyy',
    todayBtn: 'linked',
    language: 'ru',
    autoclose: true,
    todayHighlight: true,
    orientation: 'top',
  };
  periodInputs().forEach((element) => {
    if (!element) {
      return;
    }
    const $input = (window as any).$(element);
    $input.datepicker(options).on('changeDate', () => {
      if (!$input.is(':focus')) {
        element.dispatchEvent(new Event('change'));
      }
    });
    const parsed = moment(element.value, 'DD.MM.YYYY', true);
    if (parsed.isValid()) {
      $input.datepicker('update', parsed.toDate());
    }
  });
};

const validatePeriodDates = () => {
  const fields = periodInputs();
  for (let index = 0; index < fields.length; index += 1) {
    const element = fields[index];
    const value = String(element?.value || '').trim();
    if (!element || value === '' || moment(value, 'DD.MM.YYYY', true).isValid()) {
      continue;
    }
    const today = moment().format('DD.MM.YYYY');
    element.value = today;
    (window as any).$(element).datepicker('update', moment().toDate());
    root?.$emit('msg', 'error', 'Неверная дата');
    const next = dateRange.value.slice() as [string, string];
    next[index] = today;
    dateRange.value = next;
  }
};

const onPeriodDateChange = (index: number, event: Event) => {
  const input = event.target as HTMLInputElement;
  let value = String(input.value || '').trim();
  if (value !== '' && !moment(value, 'DD.MM.YYYY', true).isValid()) {
    notify.error('Неверная дата');
    value = moment().format('DD.MM.YYYY');
    input.value = value;
    (window as any).$(input).datepicker('update', moment().toDate());
  }
  const next = dateRange.value.slice() as [string, string];
  if (next[index] === value) {
    return;
  }
  next[index] = value;
  dateRange.value = next;
};

const clearPeriodDate = (index: number) => {
  const input = periodInputs()[index];
  if (!input) {
    return;
  }
  input.value = '';
  (window as any).$(input).datepicker('update', '');
  const next = dateRange.value.slice() as [string, string];
  if (next[index] === '') {
    return;
  }
  next[index] = '';
  dateRange.value = next;
};

const destroyPeriodDates = () => {
  periodInputs().forEach((element) => {
    if (element) {
      (window as any).$(element).datepicker('destroy');
    }
  });
};

const load = async () => {
  const response = await api('indicators/approval-journal', {
    filterByDate: filterByDate.value,
    datePeriod: filterByDate.value ? dateRange.value : ['', ''],
  });
  if (!response.ok) {
    notify.error(response.message || 'Не удалось загрузить журнал');
    return;
  }
  sortLevels.value = [];
  rows.value = response.rows || [];
  loaded.value = true;
};

const openLinked = async (row: JournalRow, document: LinkedDocument) => {
  if (openingId.value) {
    return;
  }
  openingId.value = document.id;
  try {
    const response = await api('indicators/approval-journal/link-open', {
      documentId: row.documentId,
      linkedDocumentId: document.id,
    });
    if (!response.ok) {
      notify.error(response.message || 'Не удалось обновить документ');
      return;
    }
    window.open(documentHref(document.id), '_blank');
  } finally {
    openingId.value = 0;
  }
};

const createLinked = async (row: JournalRow) => {
  if (row.linkedDocuments.length) {
    return;
  }
  linkingId.value = row.documentId;
  try {
    const response = await api('indicators/approval-journal/link', { documentId: row.documentId });
    if (!response.ok || !response.document) {
      notify.error(response.message || 'Документ не создан');
      return;
    }
    rows.value = rows.value.map(item => (
      item.documentId === row.documentId ? { ...item, linkedDocuments: [response.document] } : item
    ));
    window.open(documentHref(response.document.id), '_blank');
  } finally {
    linkingId.value = 0;
  }
};

const closeSign = () => {
  signOpen.value = false;
  signRowId.value = 0;
  signPdf.value = '';
  signChecked.value = false;
  signHasPlugin.value = false;
  signCertificates.value = [];
  selectedThumbprint.value = '';
  signBusy.value = false;
};

const loadCertificates = async () => {
  signChecked.value = false;
  signHasPlugin.value = false;
  signCertificates.value = [];
  selectedThumbprint.value = '';
  try {
    await getSystemInfo();
    signHasPlugin.value = true;
    const certificates = await getUserCertificates();
    signCertificates.value = certificates.map(certificate => ({
      thumbprint: certificate.thumbprint,
      name: convertSubjectNameToTitle(null, certificate.subjectName) || certificate.thumbprint,
      validFrom: moment(certificate.validFrom).format('DD.MM.YYYY HH:mm'),
      validTo: moment(certificate.validTo).format('DD.MM.YYYY HH:mm'),
    }));
    if (signCertificates.value.length) {
      selectedThumbprint.value = signCertificates.value[0].thumbprint;
    }
  } catch (error) {
    if (error) {
      signHasPlugin.value = false;
    }
  } finally {
    signChecked.value = true;
  }
};

const sign = async (row: JournalRow) => {
  signingId.value = row.documentId;
  try {
    const response = await api('indicators/approval-journal/sign-file', { documentId: row.documentId });
    rememberLinked(row.documentId, response.document || null);
    if (!response.ok || !response.pdf) {
      notify.error(response.message || 'Не удалось подготовить документ');
      return;
    }
    signRowId.value = row.documentId;
    signPdf.value = response.pdf;
    signOpen.value = true;
    await loadCertificates();
  } finally {
    signingId.value = 0;
  }
};

const confirmSign = async () => {
  if (!signRowId.value || !signPdf.value || !selectedThumbprint.value || signBusy.value) {
    return;
  }
  signBusy.value = true;
  try {
    const binary = Uint8Array.from(atob(signPdf.value), char => char.charCodeAt(0));
    const hashed = await createHash(binary);
    const signature = await createDetachedSignature(selectedThumbprint.value, hashed);
    let certificate = null;
    try {
      certificate = await getCertificate(selectedThumbprint.value);
    } catch (error) {
      if (error) {
        certificate = null;
      }
    }
    const response = await api('indicators/approval-journal/sign', {
      documentId: signRowId.value,
      sign: signature,
      certThumbprint: selectedThumbprint.value,
      certDetails: certificate ? {
        subjectName: certificate.subjectName,
        validFrom: certificate.validFrom,
        validTo: certificate.validTo,
      } : null,
    });
    if (!response.ok) {
      notify.error(response.message || 'Не удалось подписать');
      return;
    }
    const documentId = signRowId.value;
    rows.value = rows.value.map(item => (
      item.documentId === documentId ? { ...item, sign: response.sign } : item
    ));
    rememberLinked(documentId, response.document || null);
    closeSign();
  } catch (error) {
    if (error) {
      notify.error('Не удалось подписать');
    }
  } finally {
    signBusy.value = false;
  }
};

const resetSign = async (row: JournalRow) => {
  resettingId.value = row.documentId;
  try {
    const response = await api('indicators/approval-journal/sign-reset', { documentId: row.documentId });
    if (!response.ok) {
      notify.error(response.message || 'Не удалось сбросить подпись');
      return;
    }
    rows.value = rows.value.map(item => (
      item.documentId === row.documentId ? { ...item, sign: null } : item
    ));
  } finally {
    resettingId.value = 0;
  }
};

const toggleSort = (key: string) => {
  const primary = sortLevels.value[0];
  const secondary = sortLevels.value[1];
  if (primary && primary.key === key) {
    sortLevels.value = [
      { key, dir: primary.dir === 'asc' ? 'desc' : 'asc' },
      ...(secondary ? [secondary] : []),
    ];
    return;
  }
  if (primary && secondary && secondary.key === key) {
    sortLevels.value = [
      primary,
      { key, dir: secondary.dir === 'asc' ? 'desc' : 'asc' },
    ];
    return;
  }
  if (!primary) {
    sortLevels.value = [{ key, dir: 'asc' }];
    return;
  }
  sortLevels.value = [primary, { key, dir: 'asc' }];
};

const setSortKey = (index: number, event: Event) => {
  const key = (event.target as HTMLSelectElement).value;
  const primary = sortLevels.value[0];
  const secondary = sortLevels.value[1];
  if (index === 0) {
    if (!key) {
      sortLevels.value = [];
      return;
    }
    const dir = primary && primary.key === key ? primary.dir : 'asc';
    const keptSecondary = secondary && secondary.key !== key ? secondary : null;
    sortLevels.value = keptSecondary ? [{ key, dir }, keptSecondary] : [{ key, dir }];
    return;
  }
  if (!primary) {
    return;
  }
  if (!key || key === primary.key) {
    sortLevels.value = [primary];
    return;
  }
  const dir = secondary && secondary.key === key ? secondary.dir : 'asc';
  sortLevels.value = [primary, { key, dir }];
};

const toggleLevelDir = (index: number) => {
  const level = sortLevels.value[index];
  if (!level) {
    return;
  }
  const next = sortLevels.value.slice();
  next[index] = { key: level.key, dir: level.dir === 'asc' ? 'desc' : 'asc' };
  sortLevels.value = next;
};

const clearSort = () => {
  sortLevels.value = [];
};

const sortMark = (key: string) => {
  const index = sortLevels.value.findIndex(level => level.key === key);
  if (index === -1) {
    return '';
  }
  const arrow = sortLevels.value[index].dir === 'asc' ? '▲' : '▼';
  return `${index + 1}${arrow}`;
};

onMounted(() => {
  initPeriodDates();
  root?.$on('validate-datepickers', validatePeriodDates);
  load();
});

onBeforeUnmount(() => {
  root?.$off('validate-datepickers', validatePeriodDates);
  destroyPeriodDates();
});

watch([filterByDate, dateRange], () => {
  if (loaded.value) {
    load();
  }
}, { deep: true });
</script>

<style scoped lang="scss">
.not-loaded {
  text-align: center;
  padding: 20px;
  color: grey;
}

.data {
  padding: 0 20px 20px;
}

.sort-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 8px;

  > * {
    margin-right: 6px;
    margin-bottom: 4px;
  }

  select.form-control {
    width: auto;
    display: inline-block;
  }

  &__label {
    color: #555;
  }

  &__reset {
    padding-left: 4px;
  }
}

.date-filter {
  display: inline-flex;
  align-items: stretch;
  height: 34px;
  background: #aab2bd;

  &__addon {
    display: flex;
    align-items: center;
    flex: 0 0 auto;
    margin: 0;
    padding: 0 8px;
    background: #aab2bd;
    color: #fff;
    font-weight: normal;
    white-space: nowrap;

    input {
      margin: 0;
    }
  }

  &__clear {
    flex: 0 0 28px;
    width: 28px;
    margin: 0;
    padding: 0;
    border: 0;
    background: #aab2bd;
    color: #fff;
    font-size: 16px;
    line-height: 32px;

    &:hover {
      background: #434a54;
      color: #fff;
    }
  }

  &__input {
    width: 92px;
    flex: 0 0 92px;
    height: 34px;
    margin: 0;
    padding: 0 4px;
    border: 0;
    border-radius: 0;
    background: #fff;
    box-shadow: none;
    text-align: center;
  }
}

.table-list {
  table-layout: fixed;

  thead th {
    position: sticky;
    top: -1px;
    background: #fff;
  }

  thead th.sortable {
    cursor: pointer;
    user-select: none;
  }

  .sort-mark {
    margin-left: 4px;
  }

  thead .vue-treeselect {
    min-width: 90px;
    font-size: 12px;
  }

  thead tr:last-child th {
    padding: 0;
  }

  thead tr:last-child th ::v-deep .vue-treeselect__control {
    border: 0;
    border-radius: 0;
    box-shadow: none;
    min-height: 28px;
    height: 28px;
  }

  thead tr:last-child th ::v-deep .vue-treeselect__single-value {
    line-height: 28px;
  }

  thead tr:last-child th ::v-deep .vue-treeselect__input-container {
    padding-top: 0;
    padding-bottom: 0;
  }
}

.status-cell {
  text-align: center;

  &__approved {
    color: #049372;
  }
}

.sign-body {
  min-height: 120px;
  padding: 12px;

  &__cert {
    margin-top: 8px;
  }
}

.sign-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.status-error {
  color: #da4453;
}
</style>
