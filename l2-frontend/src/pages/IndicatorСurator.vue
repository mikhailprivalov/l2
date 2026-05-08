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
          <div class="col-xs-6">
            <div class="input-group treeselect-noborder-left">
              <span class="input-group-addon">Больница</span>
              <treeselect
                v-model="params.hospital"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="visibleHospitals"
                placeholder="Больница не выбрана"
                :clearable="false"
                class="treeselect-wide"
              />
            </div>
          </div>
          <div class="col-xs-6">
            <div class="input-group date-time treeselect-noborder-left">
              <span class="input-group-addon">Дата</span>
              <span
                class="input-group-addon"
                style="padding: 0;border: none;"
              >
                <!--                <DateFieldNav2-->
                <!--                  v-model="params.date"-->
                <!--                  right-->
                <!--                  w="140px"-->
                <!--                  :brn="false"-->
                <!--                />-->
                <DateRange
                  v-model="params.datePeriod"
                />

              </span>
              <span class="input-group-addon">Статус</span>
              <select
                v-model="params.status"
                class="form-control"
              >
                <option :value="2">
                  Все
                </option>
                <option :value="0">
                  Новые
                </option>
                <option :value="1">
                  Выполнены
                </option>
              </select>
            </div>
          </div>
        </div>
        <div style="margin-top: 5px">
          <a
            class="a-under pull-right"
            href="#"
            @click.prevent="load()"
          >перезагрузить данные</a>
          <a
            class="a-under pull-right"
            style="margin-right: 12px"
            href="#"
            @click.prevent="resetColumnFilters()"
          >сбросить фильтры</a>
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
      <table class="table table-bordered table-condensed table-hover table-list">
        <colgroup>
          <col style="width: 300px">
          <col style="width: 130px">
          <col>
          <col style="width: 120px">
          <col style="width: 90px">
          <col style="width: 160px">
          <col style="width: 120px">
        </colgroup>
        <thead>
          <tr>
            <th>Медицинская организация</th>
            <th>Номер</th>
            <th>Показатель</th>
            <th>Значение МО</th>
            <th>Балл, МО</th>
            <th>Значение, куратор</th>
            <th>Балл, куратор</th>
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
              colspan="7"
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
import DateRange from '@/ui-cards/DateRange.vue';

interface Params {
  datePeriod: any;
  status: number;
  hospital: number;
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

@Component({
  components: {
    DateRange,
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
        status: 2,
        hospital: -1,
        datePeriod: [moment().format('DD.MM.YYYY'), moment().format('DD.MM.YYYY')],
      },
      columnFilters: {
        hospital: null,
        direction: null,
        indicatorTitle: null,
        hospitalValue: null,
        score: null,
        curatorValue: null,
        curatorScore: null,
      },
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

  loaded: boolean;

  hospitals: any[];

  get canEdit() {
    for (const g of this.$store.getters.user_data.groups || []) {
      if (g === 'Заполнение экстренных извещений') {
        return true;
      }
    }
    return false;
  }

  get watchParams() {
    // return _.pick(this.params, ['date', 'status', 'hospital', 'datePeriod']);
    return _.pick(this.params, ['status', 'hospital', 'datePeriod']);
  }

  get visibleHospitals() {
    return this.canEdit ? this.hospitals : this.hospitals.filter(h => h.id === this.$store.getters.user_data.hospital);
  }

  get filteredRows() {
    const toValue = (value: any) => String(value ?? '');
    const filters = {
      hospital: normalizeFilterValue(this.columnFilters.hospital),
      direction: normalizeFilterValue(this.columnFilters.direction),
      indicatorTitle: normalizeFilterValue(this.columnFilters.indicatorTitle),
      hospitalValue: normalizeFilterValue(this.columnFilters.hospitalValue),
      score: normalizeFilterValue(this.columnFilters.score),
      curatorValue: normalizeFilterValue(this.columnFilters.curatorValue),
      curatorScore: normalizeFilterValue(this.columnFilters.curatorScore),
    };
    const hasFilters = Object.values(filters).some(v => v !== null);
    if (!hasFilters) {
      return this.rows;
    }
    return this.rows.filter((row: any) => (
      (filters.hospital === null || toValue(row.hospital) === filters.hospital)
      && (filters.direction === null || toValue(row.direction) === filters.direction)
      && (filters.indicatorTitle === null || toValue(row.indicatorTitle) === filters.indicatorTitle)
      && (filters.hospitalValue === null || toValue(row.hospitalValue) === filters.hospitalValue)
      && (filters.score === null || toValue(row.score) === filters.score)
      && (filters.curatorValue === null || toValue(row.curatorValue) === filters.curatorValue)
      && (filters.curatorScore === null || toValue(row.curatorScore) === filters.curatorScore)
    ));
  }

  get hospitalFilterOptions() {
    return makeOptions(this.rows.map((r: any) => r.hospital));
  }

  get directionFilterOptions() {
    return makeOptions(this.rows.map((r: any) => r.direction), true);
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

  async load() {
    await this.$store.dispatch(actions.INC_LOADING);
    const data = await this.$api('indicators/search-indicator', this.params);
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

  resetColumnFilters() {
    this.columnFilters = {
      hospital: null,
      direction: null,
      indicatorTitle: null,
      hospitalValue: null,
      score: null,
      curatorValue: null,
      curatorScore: null,
    };
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

.date-time {
  input {
    line-height: 1;
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
