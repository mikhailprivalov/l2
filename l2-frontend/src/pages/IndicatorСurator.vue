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
          <col style="width: 90px">
          <col>
          <col style="width: 120px">
          <col style="width: 120px">
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
              <input
                v-model.trim="columnFilters.hospital"
                class="form-control input-sm"
                placeholder="Фильтр..."
              >
            </th>
            <th>
              <input
                v-model.trim="columnFilters.direction"
                class="form-control input-sm"
                placeholder="Фильтр..."
              >
            </th>
            <th>
              <input
                v-model.trim="columnFilters.indicatorTitle"
                class="form-control input-sm"
                placeholder="Фильтр..."
              >
            </th>
            <th>
              <input
                v-model.trim="columnFilters.hospitalValue"
                class="form-control input-sm"
                placeholder="Фильтр..."
              >
            </th>
            <th>
              <input
                v-model.trim="columnFilters.score"
                class="form-control input-sm"
                placeholder="Фильтр..."
              >
            </th>
            <th>
              <input
                v-model.trim="columnFilters.curatorValue"
                class="form-control input-sm"
                placeholder="Фильтр..."
              >
            </th>
            <th>
              <input
                v-model.trim="columnFilters.curatorScore"
                class="form-control input-sm"
                placeholder="Фильтр..."
              >
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
        hospital: '',
        direction: '',
        indicatorTitle: '',
        hospitalValue: '',
        score: '',
        curatorValue: '',
        curatorScore: '',
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

  columnFilters: Record<string, string>;

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
    const toValue = (value: any) => String(value ?? '').toLowerCase();
    const filters = {
      hospital: toValue(this.columnFilters.hospital),
      direction: toValue(this.columnFilters.direction),
      indicatorTitle: toValue(this.columnFilters.indicatorTitle),
      hospitalValue: toValue(this.columnFilters.hospitalValue),
      score: toValue(this.columnFilters.score),
      curatorValue: toValue(this.columnFilters.curatorValue),
      curatorScore: toValue(this.columnFilters.curatorScore),
    };
    const hasFilters = Object.values(filters).some(Boolean);
    if (!hasFilters) {
      return this.rows;
    }
    return this.rows.filter((row: any) => (
      toValue(row.hospital).includes(filters.hospital)
      && toValue(row.direction).includes(filters.direction)
      && toValue(row.indicatorTitle).includes(filters.indicatorTitle)
      && toValue(row.hospitalValue).includes(filters.hospitalValue)
      && toValue(row.score).includes(filters.score)
      && toValue(row.curatorValue).includes(filters.curatorValue)
      && toValue(row.curatorScore).includes(filters.curatorScore)
    ));
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

  thead input {
    min-width: 80px;
  }
}

.checkbox-color {
  background-color: #9dcaeb
}
</style>
