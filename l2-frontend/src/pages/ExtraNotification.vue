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
                <DateFieldNav2
                  v-model="params.date"
                  right
                  w="140px"
                  :brn="false"
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
            v-if="canEdit"
            class="a-under pull-right"
            href="#"
            style="padding-right: 10px"
            @click.prevent="covid()"
          >
            covid-json
          </a>
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
          <col>
          <col>
          <col style="width: 120px">
          <col style="width: 120px">
          <col style="width: 260px">
          <col style="width: 120px">
          <col style="width: 120px">
          <col style="width: 50px">
        </colgroup>
        <thead>
          <tr>
            <th>Медицинская организация</th>
            <th>Пациент</th>
            <th>№ заявки</th>
            <th>Дата заявки</th>
            <th>Эпид №</th>
            <th>Эпид № - дата</th>
            <th>№ в базе</th>
            <th class="text-center">
              <a
                v-if="toPrintNumbers.length > 0"
                v-tippy
                href="#"
                class="a-under"
                title="Печать выбранных"
                @click.prevent="print"
              >
                <i class="fas fa-print" />
              </a>
              <a
                v-if="toPrintNumbers.length > 0"
                v-tippy
                href="#"
                class="a-under"
                title="JSON-file"
                @click.prevent="savejson()"
              >
                <i class="fas fa-poll-h" />
              </a>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="r in rows"
            :key="r.mainDirection"
          >
            <td>
              {{ r.hospital }}
            </td>
            <td>{{ r.patient }} {{ r.born }}</td>
            <td>
              <a
                :href="`/ui/results/descriptive#{&quot;pk&quot;:${r.mainDirection}}`"
                target="_blank"
                class="a-under"
              >
                {{ r.mainDirection }}
              </a>
            </td>
            <td>
              {{ r.mainConfirm }}
            </td>
            <td class="cl-td">
              <ExtraNotificationFastEditor
                :data="r"
                :can-edit="canEdit"
              />
            </td>
            <td>
              {{ r.slaveConfirm || '–' }}
            </td>
            <td>
              <a
                v-if="r.slaveDir"
                :href="`/ui/results/descriptive#{&quot;pk&quot;:${r.slaveDir}}`"
                class="a-under"
                target="_blank"
              >
                {{ r.slaveDir }}
              </a>
            </td>
            <td
              class="text-center cl-td"
              :class="[r.slaveConfirm ? 'checkbox-color' : '']"
            >
              <input
                v-model="toPrint[r.slaveDir]"
                type="checkbox"
              >
            </td>
          </tr>
          <tr v-if="rows.length === 0">
            <td
              colspan="8"
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
import DateFieldNav2 from '@/fields/DateFieldNav2.vue';
import ExtraNotificationFastEditor from '@/ui-cards/ExtraNotificationFastEditor.vue';
import { ExtraNotificationData } from '@/types/extraNotification';

interface Params {
  date: string;
  status: number;
  hospital: number;
}

const EMPTY_ROWS: ExtraNotificationData[] = [];

@Component({
  components: {
    ExtraNotificationFastEditor,
    DateFieldNav2,
    DocCallRow,
    Treeselect,
  },
  data() {
    return {
      hospitals: [],
      rows: EMPTY_ROWS,
      loaded: false,
      params: {
        date: moment().format('YYYY-MM-DD'),
        status: 2,
        hospital: -1,
      },
      toPrint: {},
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

  loaded: boolean;

  hospitals: any[];

  toPrint: any;

  get canEdit() {
    for (const g of this.$store.getters.user_data.groups || []) {
      if (g === 'Заполнение экстренных извещений') {
        return true;
      }
    }
    return false;
  }

  get watchParams() {
    return _.pick(this.params, ['date', 'status', 'hospital']);
  }

  get visibleHospitals() {
    return this.canEdit ? this.hospitals : this.hospitals.filter(h => h.id === this.$store.getters.user_data.hospital);
  }

  get toPrintNumbers() {
    return Object.keys(this.toPrint).filter(k => this.toPrint[k]);
  }

  print() {
    const ids = this.toPrintNumbers;
    window.open(`/forms/extra-nofication?pk=[${ids}]`);
    for (const i of ids) {
      this.toPrint[i] = false;
    }
  }

  savejson() {
    const ids = this.toPrintNumbers;
    window.open(`/forms/json-nofication?pk=[${ids}]`);
    for (const i of ids) {
      this.toPrint[i] = false;
    }
  }

  async load() {
    await this.$store.dispatch(actions.INC_LOADING);
    const data = await this.$api('extra-notification/search', this.params);
    this.rows = data.rows;
    this.toPrint = data.rows.reduce((a, r) => ({ ...a, [r.slaveDir]: false }), {});
    await this.$store.dispatch(actions.DEC_LOADING);
    this.loaded = true;
  }

  covid() {
    window.open(`/forms/covid-result?date=${this.params.date}`);
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
}

.checkbox-color {
  background-color: #9dcaeb
}
</style>
