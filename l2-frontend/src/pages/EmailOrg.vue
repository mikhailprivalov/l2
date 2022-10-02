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
          <div class="col-xs-8">
            <div class="input-group treeselect-noborder-left">
              <span class="input-group-addon">Организация</span>
              <treeselect
                v-model="params.hospitalId"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="hospitals"
                placeholder="Организация не выбрана"
                :clearable="false"
                class="treeselect-wide"
              />
            </div>
          </div>
          <div class="col-xs-4">
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
            </div>
          </div>
        </div>
        <div style="margin-top: 5px">
          <div
            v-if="params.hospitalId !== -1 && hospitalById[params.hospitalId]"
            class="email-status"
          >
            Email: {{ hospitalById[params.hospitalId].email || 'не указан' }}
          </div>
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
          <col>
          <col style="width: 150px">
          <col style="width: 150px">
          <col style="width: 39px">
        </colgroup>
        <thead>
          <tr>
            <th>Организация</th>
            <th>Направление</th>
            <th>Статус</th>
            <th class="cl-td">
              <button
                v-tippy="{ placement: 'bottom' }"
                class="btn btn-blue-nb"
                title="Выбрать неотправленные"
                @click.prevent="selectNotSent()"
              >
                <i class="fa fa-check-square-o" />
              </button>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="r in rows"
            :key="r.pk"
          >
            <td>
              {{ hospitalById[r.hospitalId] && hospitalById[r.hospitalId].label }}
            </td>
            <td>
              {{ r.pk }}
            </td>
            <td>
              {{ statusRow(r) }}
            </td>
            <td
              class="x-cell"
              :class="`cb-${statusRowClass(r)}`"
            >
              <label>
                <input
                  v-if="statusRowClass(r) !== 'error'"
                  v-model="toSend[r.pk]"
                  type="checkbox"
                >
              </label>
            </td>
          </tr>
          <tr v-if="rows.length === 0">
            <td
              colspan="4"
              class="text-center"
            >
              не найдено
            </td>
          </tr>
        </tbody>
      </table>
      <div class="send-controls row">
        <div class="col-xs-6">
          Выбрано: {{ toSendNumbers.length }}
        </div>
        <div class="col-xs-6">
          <button
            class="btn btn-blue-nb"
            :disabled="toSendNumbers.length === 0"
            @click="send()"
          >
            Отправить
          </button>
        </div>
      </div>
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
import { Hospital } from '@/types/hospital';

interface DirectionRow {
  pk: number
  hospitalId: number
  emailWasSent: boolean
}

interface Params {
  date: string
  hospital: number
}

interface ToSend {
  [key: number]: boolean
}

const EMPTY_ROWS: DirectionRow[] = [];

@Component({
  components: {
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
        hospitalId: -1,
      },
      toSend: {},
    };
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
    const { hospitals } = await this.$api('hospitals', { filterByNeedSendResult: true });
    this.hospitals = hospitals;
    await this.$store.dispatch(actions.DEC_LOADING);
  },
})
export default class EmailOrg extends Vue {
  params: Params;

  rows: DirectionRow[];

  loaded: boolean;

  hospitals: Hospital[];

  toSend: ToSend;

  get watchParams() {
    return _.pick(this.params, ['date', 'hospital']);
  }

  get toSendNumbers() {
    return Object.keys(this.toSend).filter(k => this.toSend[k]).map(Number);
  }

  get hospitalById() {
    return _.keyBy(this.hospitals, 'id');
  }

  selectNotSent() {
    this.rows.forEach((r) => {
      this.toSend[r.pk] = this.statusRowClass(r) === 'none';
    });
  }

  async send() {
    try {
      await this.$dialog.confirm('Вы уверены, что хотите отправить результаты?');
    } catch (e) {
      return;
    }

    const ids = this.toSendNumbers;

    await this.$store.dispatch(actions.INC_LOADING);

    const groupedDirectionsByHospital = _.groupBy(ids, (id: number) => this.rows.find(r => r.pk === id).hospitalId);
    for (const [hospitalId, directionsIds] of Object.entries(groupedDirectionsByHospital)) {
      const { ok, message } = await this.$api('directions/send-results-to-hospital', { directionsIds, hospitalId });

      const orgLabel = this.hospitalById[hospitalId]?.label;

      if (ok) {
        for (const i of directionsIds) {
          this.toSend[i] = false;
        }
        this.rows = this.rows.map(r => {
          if (directionsIds.includes(r.pk)) {
            // eslint-disable-next-line no-param-reassign
            r.emailWasSent = true;
          }
          return r;
        });
        this.$root.$emit('msg', 'ok', `Результаты направлений отправлены в ${orgLabel}`);
      } else {
        this.$root.$emit('msg', 'error', `Ошибка при отправке результатов для ${orgLabel}: ${message || 'неизвестная ошибка'}`);
      }
    }
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  async load() {
    await this.$store.dispatch(actions.INC_LOADING);
    const data = await this.$api('directions/directions-by-hospital-sent', this.params);
    this.rows = data.rows;
    this.toSend = data.rows.reduce((a, r) => ({ ...a, [r.pk]: false }), {});
    await this.$store.dispatch(actions.DEC_LOADING);
    this.loaded = true;
  }

  statusRow(r) {
    if (r.emailWasSent) {
      return 'отправлено';
    }
    if (!this.hospitalById[r.hospitalId]?.email) {
      return 'не указан email';
    }
    return 'не отправлено';
  }

  statusRowClass(r) {
    if (r.emailWasSent) {
      return 'success';
    }
    if (!this.hospitalById[r.hospitalId]?.email) {
      return 'error';
    }
    return 'none';
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

.email-status {
  display: inline-block;
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

.cb-success {
  background-color: #dff0d8;
}

.cb-error {
  background-color: #f2dede
}

.x-cell label:not(.vue-treeselect__label) {
  min-height: 31px;
}

.send-controls {
  margin: 10px 0;

  .col-xs-6:first-child {
    text-align: left;
    padding-left: 0;
  }

  .col-xs-6:last-child {
    text-align: right;
    padding-right: 0;
  }
}
</style>
