<template>
  <div>
    <form
      class="panel panel-default panel-flt"
      style="margin: 20px;"
      @submit.prevent="load()"
    >
      <div
        class="panel-body"
        style="overflow: visible;"
      >
        <div
          class="row"
          style="margin-top:5px;"
        >
          <div class="col-xs-12 indicator-filters">
            <div class="date-filter">
              <label class="date-filter__addon">
                <input
                  v-model="params.filterByDate"
                  type="checkbox"
                >
              </label>
              <span class="date-filter__addon">Дата</span>
              <input
                ref="dateFrom"
                class="date-filter__input"
                type="text"
                maxlength="10"
                :value="params.datePeriod[0]"
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
                :value="params.datePeriod[1]"
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
            <label
              v-if="canSeeAllIndicators"
              class="all-indicators"
            >
              <input
                v-model="params.allIndicators"
                type="checkbox"
              >
              <span>Все показатели</span>
            </label>
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
        @click.prevent="load()"
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
            v-for="col in sortColumns"
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
          <col style="width: 300px">
          <col style="width: 110px">
          <col style="width: 130px">
          <col style="width: 160px">
          <col>
          <col style="width: 120px">
          <col style="width: 90px">
          <col style="width: 160px">
          <col style="width: 120px">
          <col style="width: 100px">
          <col style="width: 100px">
          <col style="width: 200px">
        </colgroup>
        <thead>
          <tr>
            <th
              class="sortable"
              @click="toggleSort('hospital')"
            >
              Медицинская организация
              <span
                v-if="sortMark('hospital')"
                class="sort-mark"
              >{{ sortMark('hospital') }}</span>
            </th>
            <th
              class="sortable"
              @click="toggleSort('confirmDate')"
            >
              Дата
              <span
                v-if="sortMark('confirmDate')"
                class="sort-mark"
              >{{ sortMark('confirmDate') }}</span>
            </th>
            <th
              class="sortable"
              @click="toggleSort('direction')"
            >
              Номер
              <span
                v-if="sortMark('direction')"
                class="sort-mark"
              >{{ sortMark('direction') }}</span>
            </th>
            <th
              class="sortable"
              @click="toggleSort('curatorName')"
            >
              Куратор
              <span
                v-if="sortMark('curatorName')"
                class="sort-mark"
              >{{ sortMark('curatorName') }}</span>
            </th>
            <th
              class="sortable"
              @click="toggleSort('indicatorTitle')"
            >
              Показатель
              <span
                v-if="sortMark('indicatorTitle')"
                class="sort-mark"
              >{{ sortMark('indicatorTitle') }}</span>
            </th>
            <th
              class="sortable"
              @click="toggleSort('hospitalValue')"
            >
              Значение МО
              <span
                v-if="sortMark('hospitalValue')"
                class="sort-mark"
              >{{ sortMark('hospitalValue') }}</span>
            </th>
            <th
              class="sortable"
              @click="toggleSort('score')"
            >
              Балл, МО
              <span
                v-if="sortMark('score')"
                class="sort-mark"
              >{{ sortMark('score') }}</span>
            </th>
            <th
              class="sortable"
              @click="toggleSort('curatorValue')"
            >
              Значение, куратор
              <span
                v-if="sortMark('curatorValue')"
                class="sort-mark"
              >{{ sortMark('curatorValue') }}</span>
            </th>
            <th
              class="sortable"
              @click="toggleSort('curatorScore')"
            >
              Балл, куратор
              <span
                v-if="sortMark('curatorScore')"
                class="sort-mark"
              >{{ sortMark('curatorScore') }}</span>
            </th>
            <th />
            <th
              class="sortable"
              @click="toggleSort('curatorStatus')"
            >
              Статус
              <span
                v-if="sortMark('curatorStatus')"
                class="sort-mark"
              >{{ sortMark('curatorStatus') }}</span>
            </th>
            <th
              class="sortable"
              @click="toggleSort('curatorComment')"
            >
              Комментарий
              <span
                v-if="sortMark('curatorComment')"
                class="sort-mark"
              >{{ sortMark('curatorComment') }}</span>
            </th>
          </tr>
          <tr>
            <th>
              <treeselect
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
              <treeselect
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
              <treeselect
                v-model="columnFilters.direction"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="directionFilterOptions"
                placeholder="Все"
                :clearable="true"
                class="treeselect-wide"
              />
            </th>
            <th>
              <treeselect
                v-model="columnFilters.curatorName"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="curatorNameFilterOptions"
                placeholder="Все"
                :clearable="true"
                class="treeselect-wide"
              />
            </th>
            <th>
              <treeselect
                v-model="columnFilters.indicatorTitle"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="indicatorTitleFilterOptions"
                placeholder="Все"
                :clearable="true"
                class="treeselect-wide"
              />
            </th>
            <th>
              <treeselect
                v-model="columnFilters.hospitalValue"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="hospitalValueFilterOptions"
                placeholder="Все"
                :clearable="true"
                class="treeselect-wide"
              />
            </th>
            <th>
              <treeselect
                v-model="columnFilters.score"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="scoreFilterOptions"
                placeholder="Все"
                :clearable="true"
                class="treeselect-wide"
              />
            </th>
            <th>
              <treeselect
                v-model="columnFilters.curatorValue"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="curatorValueFilterOptions"
                placeholder="Все"
                :clearable="true"
                class="treeselect-wide"
              />
            </th>
            <th>
              <treeselect
                v-model="columnFilters.curatorScore"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="curatorScoreFilterOptions"
                placeholder="Все"
                :clearable="true"
                class="treeselect-wide"
              />
            </th>
            <th />
            <th>
              <treeselect
                v-model="columnFilters.curatorStatus"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="curatorStatusFilterOptions"
                placeholder="Все"
                :clearable="true"
                class="treeselect-wide"
              />
            </th>
            <th />
          </tr>
        </thead>
        <tbody>
          <IndicatorCuratorRow
            v-for="r in filteredRows"
            :key="`${r.issledovaniye}-${r.direction}-${r.indicatorTitle}`"
            :row="r"
            @row-updated="onRowUpdated"
          />
          <tr v-if="filteredRows.length === 0">
            <td
              colspan="11"
              class="text-center"
            >
              не найдено
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import moment from 'moment';
import _ from 'lodash';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import * as actions from '@/store/action-types';
import DocCallRow from '@/pages/DocCallRow.vue';
import IndicatorCuratorRow from '@/pages/IndicatorCuratorRow.vue';
import DateFieldNav2 from '@/fields/DateFieldNav2.vue';
import ExtraNotificationFastEditor from '@/ui-cards/ExtraNotificationFastEditor.vue';
import { ExtraNotificationData } from '@/types/extraNotification';

interface Params {
  datePeriod: any;
  hospital: number;
  filterByDate: boolean;
  allIndicators: boolean;
}

const EMPTY_ROWS: ExtraNotificationData[] = [];

const makeOptions = (values: any[], numeric = false) => {
  const normalized = Array.from(new Set(
    values
      .map(v => String(v ?? '').trim())
      .filter(v => v !== ''),
  ));
  if (numeric) {
    normalized.sort((a, b) => Number(a) - Number(b));
  } else {
    normalized.sort((a, b) => a.localeCompare(b, 'ru'));
  }
  return normalized.map(v => ({ id: v, label: v }));
};

const normalizeFilterValue = (value: any) => {
  if (value === null || value === undefined) {
    return null;
  }
  const normalized = String(value).trim();
  if (normalized === '' || normalized.toLowerCase() === 'null' || normalized.toLowerCase() === 'undefined') {
    return null;
  }
  return normalized;
};

const rowCuratorStatusLabel = (row: any) => (row.curatorApproved ? 'утверждено' : '–');

interface SortLevel {
  key: string;
  dir: 'asc' | 'desc';
}

const SORT_COLUMNS = [
  { key: 'hospital', label: 'Медицинская организация' },
  { key: 'confirmDate', label: 'Дата' },
  { key: 'direction', label: 'Номер' },
  { key: 'curatorName', label: 'Куратор' },
  { key: 'indicatorTitle', label: 'Показатель' },
  { key: 'hospitalValue', label: 'Значение МО' },
  { key: 'score', label: 'Балл, МО' },
  { key: 'curatorValue', label: 'Значение, куратор' },
  { key: 'curatorScore', label: 'Балл, куратор' },
  { key: 'curatorStatus', label: 'Статус' },
  { key: 'curatorComment', label: 'Комментарий' },
];

const NUMERIC_SORT_KEYS = new Set(['direction', 'score', 'curatorScore']);
const MIXED_SORT_KEYS = new Set(['hospitalValue', 'curatorValue']);

const isBlankSortValue = (value: unknown) => {
  const normalized = String(value ?? '').trim();
  return normalized === '' || normalized === '–' || normalized === '-' || normalized === '—';
};

const isNumericSortValue = (value: unknown) => {
  if (isBlankSortValue(value)) {
    return false;
  }
  return Number.isFinite(Number(String(value).trim().replace(',', '.')));
};

const rowSortValue = (row: any, key: string) => (
  key === 'curatorStatus' ? rowCuratorStatusLabel(row) : row[key]
);

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
  const numeric = NUMERIC_SORT_KEYS.has(key)
    || (MIXED_SORT_KEYS.has(key) && isNumericSortValue(left) && isNumericSortValue(right));
  if (numeric) {
    const leftNumber = Number(String(left).trim().replace(',', '.'));
    const rightNumber = Number(String(right).trim().replace(',', '.'));
    return leftNumber - rightNumber;
  }
  return String(left).localeCompare(String(right), 'ru', { numeric: true, sensitivity: 'base' });
};

const compareRowsByKey = (left: any, right: any, key: string, dir: 'asc' | 'desc') => {
  const leftValue = rowSortValue(left, key);
  const rightValue = rowSortValue(right, key);
  const leftBlank = key !== 'curatorStatus' && isBlankSortValue(leftValue);
  const rightBlank = key !== 'curatorStatus' && isBlankSortValue(rightValue);
  if (leftBlank || rightBlank) {
    if (leftBlank && rightBlank) {
      return 0;
    }
    return leftBlank ? 1 : -1;
  }
  const direction = dir === 'asc' ? 1 : -1;
  return compareSortValues(leftValue, rightValue, key) * direction;
};

@Component({
  components: {
    ExtraNotificationFastEditor,
    DateFieldNav2,
    DocCallRow,
    IndicatorCuratorRow,
    Treeselect,
  },
  data() {
    return {
      hospitals: [],
      rows: EMPTY_ROWS,
      loaded: false,
      params: {
        // date: moment().format('YYYY-MM-DD'),
        hospital: -1,
        filterByDate: true,
        allIndicators: false,
        datePeriod: [
          moment().subtract(40, 'days').format('DD.MM.YYYY'),
          moment().format('DD.MM.YYYY'),
        ],
      },
      columnFilters: {
        hospital: null,
        confirmDate: null,
        direction: null,
        curatorName: null,
        indicatorTitle: null,
        hospitalValue: null,
        score: null,
        curatorValue: null,
        curatorScore: null,
        curatorStatus: null,
      },
      sortLevels: [],
      sortColumns: SORT_COLUMNS,
    };
  },
  beforeMount() {
    this.$store.watch(
      state => state.user.data,
      (oldValue, newValue) => {
        if (this.params.hospital === -1 && newValue) {
          this.params.hospital = newValue.hospital || -1;
        }
      },
      { immediate: true },
    );
    this.$store.dispatch(actions.GET_USER_DATA);
  },
  watch: {
    watchParams: {
      deep: true,
      handler() {
        this.load();
      },
    },
    watchParamsDebounce: {
      deep: true,
      handler: _.debounce(function () {
        this.load();
      }, 200),
    },
  },
  async mounted() {
    this.initPeriodDates();
    await this.$store.dispatch(actions.INC_LOADING);
    const { hospitals } = await this.$api('hospitals', { filterByUserHospital: true });
    this.hospitals = hospitals;
    await this.$store.dispatch(actions.DEC_LOADING);
  },
})
export default class ExtraNotification extends Vue {
  params: Params;

  rows: ExtraNotificationData[];

  columnFilters: Record<string, string | null>;

  sortLevels: SortLevel[];

  loaded: boolean;

  hospitals: any[];

  get canEdit() {
    for (const g of this.$store.getters.user_data.groups || []) {
      if (g === 'Заполнение экстренных извещений' || g === 'Показатели куратора') {
        return true;
      }
    }
    return false;
  }

  get canSeeAllIndicators() {
    return (this.$store.getters.user_data.groups || []).includes('Все показатели');
  }

  get watchParams() {
    return {
      hospital: this.params.hospital,
      filterByDate: this.params.filterByDate,
      datePeriod: this.params.filterByDate ? this.params.datePeriod : null,
      allIndicators: this.canSeeAllIndicators && this.params.allIndicators,
    };
  }

  get visibleHospitals() {
    return this.canEdit ? this.hospitals : this.hospitals.filter(h => h.id === this.$store.getters.user_data.hospital);
  }

  get filteredRows() {
    const toValue = (value: any) => String(value ?? '');
    const filters = {
      hospital: normalizeFilterValue(this.columnFilters.hospital),
      confirmDate: normalizeFilterValue(this.columnFilters.confirmDate),
      direction: normalizeFilterValue(this.columnFilters.direction),
      curatorName: normalizeFilterValue(this.columnFilters.curatorName),
      indicatorTitle: normalizeFilterValue(this.columnFilters.indicatorTitle),
      hospitalValue: normalizeFilterValue(this.columnFilters.hospitalValue),
      score: normalizeFilterValue(this.columnFilters.score),
      curatorValue: normalizeFilterValue(this.columnFilters.curatorValue),
      curatorScore: normalizeFilterValue(this.columnFilters.curatorScore),
      curatorStatus: normalizeFilterValue(this.columnFilters.curatorStatus),
    };
    const hasFilters = Object.values(filters).some(v => v !== null);
    const filtered = hasFilters
      ? this.rows.filter((row: any) => (
        (filters.hospital === null || toValue(row.hospital) === filters.hospital)
        && (filters.confirmDate === null || toValue(row.confirmDate) === filters.confirmDate)
        && (filters.direction === null || toValue(row.direction) === filters.direction)
        && (filters.curatorName === null || toValue(row.curatorName) === filters.curatorName)
        && (filters.indicatorTitle === null || toValue(row.indicatorTitle) === filters.indicatorTitle)
        && (filters.hospitalValue === null || toValue(row.hospitalValue) === filters.hospitalValue)
        && (filters.score === null || toValue(row.score) === filters.score)
        && (filters.curatorValue === null || toValue(row.curatorValue) === filters.curatorValue)
        && (filters.curatorScore === null || toValue(row.curatorScore) === filters.curatorScore)
        && (filters.curatorStatus === null || rowCuratorStatusLabel(row) === filters.curatorStatus)
      ))
      : this.rows;
    if (!this.sortLevels.length) {
      return filtered;
    }
    const levels = this.sortLevels;
    return filtered.slice().sort((left: any, right: any) => {
      for (let index = 0; index < levels.length; index += 1) {
        const level = levels[index];
        const result = compareRowsByKey(left, right, level.key, level.dir);
        if (result !== 0) {
          return result;
        }
      }
      return 0;
    });
  }

  get secondarySortColumns() {
    return SORT_COLUMNS.filter(column => column.key !== this.sortPrimaryKey);
  }

  get sortPrimaryKey() {
    return this.sortLevels[0] ? this.sortLevels[0].key : '';
  }

  get sortPrimaryDir(): 'asc' | 'desc' {
    return this.sortLevels[0] ? this.sortLevels[0].dir : 'asc';
  }

  get sortSecondaryKey() {
    return this.sortLevels[1] ? this.sortLevels[1].key : '';
  }

  get sortSecondaryDir(): 'asc' | 'desc' {
    return this.sortLevels[1] ? this.sortLevels[1].dir : 'asc';
  }

  initPeriodDates() {
    const options = {
      format: 'dd.mm.yyyy',
      todayBtn: 'linked',
      language: 'ru',
      autoclose: true,
      todayHighlight: true,
      orientation: 'top',
    };
    [this.$refs.dateFrom, this.$refs.dateTo].forEach((input) => {
      const element = input as HTMLInputElement;
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
    this.$root.$on('validate-datepickers', this.validatePeriodDates);
  }

  validatePeriodDates() {
    [this.$refs.dateFrom, this.$refs.dateTo].forEach((input, index) => {
      const element = input as HTMLInputElement;
      const value = String(element?.value || '').trim();
      if (!element || value === '' || moment(value, 'DD.MM.YYYY', true).isValid()) {
        return;
      }
      const today = moment().format('DD.MM.YYYY');
      element.value = today;
      (window as any).$(element).datepicker('update', moment().toDate());
      this.$root.$emit('msg', 'error', 'Неверная дата');
      const next = this.params.datePeriod.slice();
      next[index] = today;
      this.params.datePeriod = next;
    });
  }

  onPeriodDateChange(index: number, event: Event) {
    const input = event.target as HTMLInputElement;
    let value = String(input.value || '').trim();
    if (value !== '' && !moment(value, 'DD.MM.YYYY', true).isValid()) {
      this.$root.$emit('msg', 'error', 'Неверная дата');
      value = moment().format('DD.MM.YYYY');
      input.value = value;
      (window as any).$(input).datepicker('update', moment().toDate());
    }
    const next = this.params.datePeriod.slice();
    if (next[index] === value) {
      return;
    }
    next[index] = value;
    this.params.datePeriod = next;
  }

  clearPeriodDate(index: number) {
    const input = (index === 0 ? this.$refs.dateFrom : this.$refs.dateTo) as HTMLInputElement;
    if (!input) {
      return;
    }
    input.value = '';
    (window as any).$(input).datepicker('update', '');
    const next = this.params.datePeriod.slice();
    if (next[index] === '') {
      return;
    }
    next[index] = '';
    this.params.datePeriod = next;
  }

  beforeDestroy() {
    this.$root.$off('validate-datepickers', this.validatePeriodDates);
    [this.$refs.dateFrom, this.$refs.dateTo].forEach((input) => {
      if (input) {
        (window as any).$(input).datepicker('destroy');
      }
    });
  }

  toggleSort(key: string) {
    const primary = this.sortLevels[0];
    const secondary = this.sortLevels[1];
    if (primary && primary.key === key) {
      this.sortLevels = [
        { key, dir: primary.dir === 'asc' ? 'desc' : 'asc' },
        ...(secondary ? [secondary] : []),
      ];
      return;
    }
    if (primary && secondary && secondary.key === key) {
      this.sortLevels = [
        primary,
        { key, dir: secondary.dir === 'asc' ? 'desc' : 'asc' },
      ];
      return;
    }
    if (!primary) {
      this.sortLevels = [{ key, dir: 'asc' }];
      return;
    }
    this.sortLevels = [primary, { key, dir: 'asc' }];
  }

  setSortKey(index: number, event: Event) {
    const key = (event.target as HTMLSelectElement).value;
    const primary = this.sortLevels[0];
    const secondary = this.sortLevels[1];
    if (index === 0) {
      if (!key) {
        this.sortLevels = [];
        return;
      }
      const dir = primary && primary.key === key ? primary.dir : 'asc';
      const keptSecondary = secondary && secondary.key !== key ? secondary : null;
      this.sortLevels = keptSecondary ? [{ key, dir }, keptSecondary] : [{ key, dir }];
      return;
    }
    if (!primary) {
      return;
    }
    if (!key || key === primary.key) {
      this.sortLevels = [primary];
      return;
    }
    const dir = secondary && secondary.key === key ? secondary.dir : 'asc';
    this.sortLevels = [primary, { key, dir }];
  }

  toggleLevelDir(index: number) {
    const level = this.sortLevels[index];
    if (!level) {
      return;
    }
    const next = this.sortLevels.slice();
    next[index] = { key: level.key, dir: level.dir === 'asc' ? 'desc' : 'asc' };
    this.sortLevels = next;
  }

  clearSort() {
    this.sortLevels = [];
  }

  sortMark(key: string) {
    const index = this.sortLevels.findIndex(level => level.key === key);
    if (index === -1) {
      return '';
    }
    const arrow = this.sortLevels[index].dir === 'asc' ? '▲' : '▼';
    return `${index + 1}${arrow}`;
  }

  get hospitalFilterOptions() {
    return makeOptions(this.rows.map((r: any) => r.hospital));
  }

  get confirmDateFilterOptions() {
    return makeOptions(this.rows.map((r: any) => r.confirmDate))
      .sort((left, right) => (parseRuDate(left.id) || 0) - (parseRuDate(right.id) || 0));
  }

  get directionFilterOptions() {
    return makeOptions(this.rows.map((r: any) => r.direction), true);
  }

  get curatorNameFilterOptions() {
    return makeOptions(this.rows.map((r: any) => r.curatorName));
  }

  get indicatorTitleFilterOptions() {
    return makeOptions(this.rows.map((r: any) => r.indicatorTitle));
  }

  get hospitalValueFilterOptions() {
    return makeOptions(this.rows.map((r: any) => r.hospitalValue));
  }

  get scoreFilterOptions() {
    return makeOptions(this.rows.map((r: any) => r.score), true);
  }

  get curatorValueFilterOptions() {
    return makeOptions(this.rows.map((r: any) => r.curatorValue));
  }

  get curatorScoreFilterOptions() {
    return makeOptions(this.rows.map((r: any) => r.curatorScore), true);
  }

  get curatorStatusFilterOptions() {
    return makeOptions(this.rows.map((r: any) => rowCuratorStatusLabel(r)));
  }

  async load() {
    await this.$store.dispatch(actions.INC_LOADING);
    const data = await this.$api('indicators/search-indicator', {
      ...this.params,
      allIndicators: this.canSeeAllIndicators && this.params.allIndicators,
    });
    this.sortLevels = [];
    this.rows = data.rows;
    await this.$store.dispatch(actions.DEC_LOADING);
    this.loaded = true;
  }

  onRowUpdated(updatedRow: any) {
    const rowIndex = this.rows.findIndex((r: any) => (
      r.issledovaniye === updatedRow.issledovaniye
      && r.direction === updatedRow.direction
      && r.indicatorTitle === updatedRow.indicatorTitle
    ));
    if (rowIndex !== -1) {
      this.$set(this.rows, rowIndex, updatedRow);
    }
  }
}
</script>

<style>
.pagination {
  margin-top: 0 !important;
}
</style>

<style lang="scss" scoped>
.not-loaded {
  text-align: center;
  color: grey;
}

.data {
  padding: 0 20px;
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

.founded {
  text-align: center;
  padding: 5px;
  margin-top: -5px;
}

.addon-splitter {
  background-color: #fff;

  &.disabled {
    opacity: 0.4;
  }
}

.indicator-filters {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.all-indicators {
  display: inline-flex;
  align-items: center;
  height: 34px;
  margin: 0 0 0 8px;
  padding: 0 8px;
  background: #aab2bd;
  color: #fff;
  font-weight: normal;

  input {
    margin: 0 6px 0 0;
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

.date-nav ::v-deep .btn:last-child {
  border-top-right-radius: 4px;
  border-bottom-right-radius: 4px;
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

.checkbox-color {
  background-color: #9dcaeb
}
</style>
