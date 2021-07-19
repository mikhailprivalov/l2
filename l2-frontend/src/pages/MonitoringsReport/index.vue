<template>
  <div class="report-root">
    <h3>{{ title }}</h3>
    <div class="filters">
      <div class="row">
        <div class="hidden-xs hidden-sm col-md-1"></div>
        <div class="col-xs-3">
          <div class="input-group treeselect-noborder-left">
            <span class="input-group-addon">Мониторинг</span>
            <treeselect
              :multiple="false"
              :disable-branch-nodes="true"
              :options="monitorings"
              placeholder="Мониторинг не выбран"
              v-model="research"
            />
          </div>
        </div>
        <div class="col-xs-6 col-md-5">
          <div class="input-group">
            <span class="input-group-addon">Дата<span class="hidden-xs hidden-sm"> или начало периода</span></span>
            <input class="form-control" type="date" v-model="date" />
            <span class="input-group-addon">Час</span>
            <select class="form-control" v-model="hour">
              <option v-for="h in HOURS" :key="h.id" :value="h.id">{{ h.label }}</option>
            </select>
          </div>
        </div>
        <div class="col-xs-3 col-md-2">
          <button class="btn btn-blue-n btn-block" @click="load_data" :disabled="research === null">
            Загрузить<span class="hidden-sm hidden-xs"> данные</span>
          </button>
        </div>
      </div>
    </div>
    <div class="scroll-container" v-if="data" ref="scrollContainer">
      <table class="table table-bordered table-condensed table-striped">
        <colgroup>
          <col style="width: 220px" />
          <col style="width: 140px" />
          <col style="width: 85px" />
        </colgroup>
        <thead v-if="data.rows.length > 0">
          <tr>
            <th>&nbsp;</th>
            <th>&nbsp;</th>
            <th>&nbsp;</th>
          </tr>
          <tr>
            <th>Организация</th>
            <th>Подтверждено</th>
            <th>№</th>
          </tr>
        </thead>
        <tbody v-if="data.rows.length > 0">
          <tr v-for="(r, i) in data.rows" :key="i">
            <td :title="r.hospTitle" v-tippy>
              {{ r.hospTitle }}
            </td>
            <td>
              {{ r.confirm }}
            </td>
            <td>
              {{ r.direction }}
            </td>
          </tr>
          <tr v-if="data.total && data.total.length > 0">
            <th colspan="3">Итого</th>
          </tr>
        </tbody>
        <thead v-if="data.rows.length > 0">
          <tr>
            <th>Организация</th>
            <th>Подтверждено</th>
            <th>№</th>
          </tr>
          <tr>
            <th>&nbsp;</th>
            <th>&nbsp;</th>
            <th>&nbsp;</th>
          </tr>
        </thead>
        <tbody v-if="data.empty_hospital.length > 0">
          <tr v-for="(h, i) in data.empty_hospital" :key="`empty_${i}`">
            <th :title="h" v-tippy>{{ h }}</th>
            <th colspan="2">Мониторинг не заполнен</th>
          </tr>
        </tbody>
      </table>
      <table class="table table-bordered table-condensed table-striped" ref="tableLeft">
        <colgroup>
          <template v-for="(t, i) in data.titles">
            <col v-for="(f, j) in t.fields" :key="`${i}_${j}`" width="140" />
          </template>
        </colgroup>
        <thead v-if="data.rows.length > 0">
          <tr>
            <th v-for="(t, i) in data.titles" :key="i" :colspan="t.fields.length" class="param-title">
              {{ t.groupTitle }}
            </th>
          </tr>
          <tr>
            <template v-for="(t, i) in data.titles">
              <th v-for="(f, j) in t.fields" :key="`${i}_${j}`" class="param-title">
                {{ f }}
              </th>
            </template>
          </tr>
        </thead>
        <tbody v-if="data.rows.length > 0">
          <tr v-for="(r, i) in data.rows" :key="i">
            <template v-for="(v, j) in r.values">
              <td v-for="(rv, k) in v" :key="`${i}_${j}_${k}`">
                {{ rv }}
              </td>
            </template>
          </tr>
          <tr v-if="data.total && data.total.length > 0">
            <template v-for="(v, j) in data.total">
              <td v-for="(rv, k) in v" :key="`total_${j}_${k}`">
                {{ rv }}
              </td>
            </template>
          </tr>
        </tbody>
        <thead v-if="data.rows.length > 0">
          <tr>
            <template v-for="(t, i) in data.titles">
              <th v-for="(f, j) in t.fields" :key="`${i}_${j}`" class="param-title">
                {{ f }}
              </th>
            </template>
          </tr>
          <tr>
            <th v-for="(t, i) in data.titles" :key="i" :colspan="t.fields.length" class="param-title">
              {{ t.groupTitle }}
            </th>
          </tr>
        </thead>
        <tbody v-if="data.titles.reduce((a, b) => a + b.fields.length, 0) > 0 && data.empty_hospital.length > 0">
          <tr v-for="(h, i) in data.empty_hospital" :key="`empty_${i}`">
            <td :colspan="data.titles.reduce((a, b) => a + b.fields.length, 0)"></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script lang="ts">
import { mapGetters } from 'vuex';
import moment from 'moment';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import api from '@/api';
import * as actions from '@/store/action-types';

const HOURS = [{ id: '-', label: 'нет' }];

for (let i = 0; i < 24; i++) {
  const id = i < 10 ? `0${i}` : String(i);
  const label = `${id}:00`;
  HOURS.push({ id, label });
}

export default {
  components: {
    Treeselect,
  },
  data() {
    return {
      title: 'Просмотр мониторингов',
      research: null,
      date: moment().format('YYYY-MM-DD'),
      hour: '-',
      HOURS,
      data: null,
    };
  },
  async mounted() {
    await this.$store.dispatch(actions.INC_LOADING);
    await this.$store.dispatch(actions.GET_RESEARCHES);
    await this.$store.dispatch(actions.DEC_LOADING);
  },
  computed: {
    ...mapGetters(['researches']),
    monitorings() {
      return (this.researches['-12'] || []).map(r => ({ id: r.pk, label: r.title }));
    },
  },
  methods: {
    async load_data() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { rows } = await api('/monitorings/search', this, ['research', 'date', 'hour']);
      this.data = rows;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
};
</script>

<style scoped lang="scss">
.report-root {
  position: absolute;
  top: 36px;
  left: 10px;
  right: 10px;
  bottom: 0;
}

.filters {
  margin-bottom: 10px;

  .row {
    margin-left: 0;
    margin-right: 0;
  }
}

.param-title {
  font-size: 12px;
  word-break: break-word;
}

.scroll-container {
  white-space: nowrap;
  overflow-x: auto;
  overflow-y: auto;
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  margin-left: -10px;
  margin-right: -10px;
  position: absolute;
  top: 125px;
  left: 0;
  right: 0;
  bottom: 0;

  table {
    table-layout: fixed;
    background: #fff;

    thead {
      font-size: 12px;
    }

    &:first-child {
      width: 445px;
      position: sticky;
      margin-left: 10px;
      z-index: 102;
      left: 0;

      thead {
        th {
          z-index: 102 !important;
        }
      }
    }

    &:last-child {
      width: auto;
      border-left: none;

      tr {
        td:first-child,
        th:first-child {
          border-left: none;
        }
      }
    }

    &,
    td,
    th {
      white-space: nowrap;
      text-overflow: ellipsis;
      overflow-x: hidden;
    }
  }
}
</style>
