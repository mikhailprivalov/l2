<template>
  <div class="dash-root">
    <div class="mode-select">
      <RadioField :variants="MODES" v-model="mode" />
    </div>
    <div v-if="mode === MODE_DASHBOARD" class="dashboard">
      <div class="filters">
        <div class="row">
          <div class="col-xs-6">
            <div class="input-group">
              <treeselect
                :multiple="false"
                :disable-branch-nodes="true"
                :options="dashboards"
                placeholder="Дэшборд не выбран"
                v-model="dashboardPk"
                :append-to-body="true"
              />
            </div>
          </div>
          <div class="col-xs-6">
            <div class="input-group" style="max-width: 300px">
              <span class="input-group-addon">Дата</span>
              <input class="form-control" type="date" v-model="dateDashboard" />
              <span class="input-group-btn">
                <button class="btn btn-blue-nb" @click="loadDashboard">
                  Загрузить
                </button>
              </span>
            </div>
          </div>
        </div>
      </div>
      <h4 v-if="dashboard.title">{{ dashboard.title }} — {{ loadedDashboardDateString }}</h4>
      <div class="row">
        <div class="col-xs-12 col-md-6 col-xl-4" v-for="c in charts" :key="c.pk">
          <div class="card-no-hover card card-1 chart">
            <h6>{{ c.title }}</h6>
            <div class="chart-inner">
              <VueApexCharts
                :type="CHART_TYPES[c.type] || c.type.toLowerCase()"
                :options="getOptions(c)"
                :series="getSeries(c)"
                :height="getHeight(c)"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-else-if="mode === MODE_SEARCH" :style="`--font-size-mon: ${fontSize}px;`" class="report-root">
      <div class="filters">
        <div class="row">
          <div class="hidden-xs hidden-sm col-md-1"></div>
          <div class="col-xs-3">
            <div class="input-group treeselect-noborder-left">
              <span class="input-group-addon">
                <span class="hidden-xs hidden-sm">Мониторинг</span>
                <i class="fas fa-search visible-xs visible-sm"></i>
              </span>
              <treeselect
                :multiple="false"
                :disable-branch-nodes="true"
                :options="monitorings"
                placeholder="Мониторинг не выбран"
                v-model="research"
                :append-to-body="true"
              />
            </div>
          </div>
          <div class="col-xs-6 col-md-5">
            <div class="input-group">
              <span class="input-group-addon">Дата<span class="hidden-xs hidden-sm"> или начало периода</span></span>
              <input class="form-control" type="date" v-model="date" />
              <span class="input-group-addon">Час</span>
              <select class="form-control" v-model="hour" style="width: 80px">
                <option v-for="h in HOURS" :key="h.id" :value="h.id">{{ h.label }}</option>
              </select>
            </div>
          </div>
          <div class="col-xs-3">
            <button class="btn btn-blue-nb" @click="loadSearch" :disabled="research === null" ref="loadButton">
              Загрузить<span class="hidden-sm hidden-xs"> данные</span>
            </button>

            <button
              class="btn btn-blue-nb"
              @click="print_data"
              :disabled="!data"
              title="Сохранение отображённых данных в XLSX"
              v-tippy
            >
              <i class="fas fa-download"></i>
            </button>
          </div>
        </div>
      </div>
      <div>
        <div class="text-right font-settings">
          <a href="#" @click.prevent="decFont()" class="a-under-reversed" title="Уменьшить шрифт таблицы" v-tippy>-A</a>
          &nbsp;
          <a href="#" @click.prevent="incFont()" class="a-under-reversed" title="Увеличить шрифт таблицы" v-tippy>+A</a>
        </div>
      </div>
      <div class="scroll-container" v-if="data">
        <table class="table table-bordered table-condensed table-striped">
          <colgroup>
            <col style="width: 220px" />
            <col style="width: 85px" />
          </colgroup>
          <thead v-if="data.rows.length > 0">
            <tr>
              <th>&nbsp;</th>
              <th>&nbsp;</th>
            </tr>
            <tr>
              <th>Организация</th>
              <th>№</th>
            </tr>
          </thead>
          <tbody v-if="data.rows.length > 0">
            <tr v-for="(r, i) in data.rows" :key="i">
              <td :title="`${r.hospTitle} – ${r.confirm}`" v-tippy v-html="r.hospTitle || '&nbsp;'">
                {{ r.hospTitle }}
              </td>
              <td>
                {{ r.direction }}
              </td>
            </tr>
            <tr v-if="data.total && data.total.length > 0">
              <th colspan="2" class="text-right">Итого</th>
            </tr>
          </tbody>
          <thead v-if="data.rows.length > 0">
            <tr>
              <th>Организация</th>
              <th>№</th>
            </tr>
            <tr>
              <th>&nbsp;</th>
              <th>&nbsp;</th>
            </tr>
          </thead>
          <tbody v-if="data.empty_hospital.length > 0">
            <tr v-for="(h, i) in data.empty_hospital" :key="`empty_${i}`">
              <th :title="h" v-tippy v-html="h || '&nbsp;'"></th>
              <th>пусто</th>
            </tr>
          </tbody>
        </table>
        <table
          class="table table-bordered table-condensed table-striped"
          :style="`width: ${140 * data.titles.reduce((a, b) => a + b.fields.length, 0)}px;`"
        >
          <colgroup>
            <template v-for="(t, i) in data.titles">
              <col v-for="(f, j) in t.fields" :key="`${i}_${j}`" width="140" />
            </template>
          </colgroup>
          <thead v-if="data.rows.length > 0">
            <tr>
              <th
                v-for="(t, i) in data.titles"
                :key="i"
                :colspan="t.fields.length"
                class="param-title group-start group-end"
                :title="t.groupTitle"
                v-tippy
                v-html="t.groupTitle || '&nbsp;'"
              ></th>
            </tr>
            <tr>
              <template v-for="(t, i) in data.titles">
                <th
                  v-for="(f, j) in t.fields"
                  :key="`${i}_${j}`"
                  class="param-title"
                  :class="[j === 0 && 'group-start', j + 1 === t.fields.length && 'group-end']"
                  :title="`${t.groupTitle} — ${f}`"
                  v-tippy
                  v-html="f || '&nbsp;'"
                ></th>
              </template>
            </tr>
          </thead>
          <tbody v-if="data.rows.length > 0">
            <tr v-for="(r, i) in data.rows" :key="i">
              <template v-for="(v, j) in r.values">
                <td
                  v-for="(rv, k) in v"
                  :key="`${i}_${j}_${k}`"
                  :class="[k === 0 && 'group-start', k + 1 === v.length && 'group-end']"
                  :title="`${data.titles[j].groupTitle} — ${data.titles[j].fields[k]}: ${rv}`"
                  v-tippy
                  v-html="rv || '&nbsp;'"
                ></td>
              </template>
            </tr>
            <tr v-if="data.total && data.total.length > 0">
              <template v-for="(v, j) in data.total">
                <td
                  v-for="(rv, k) in v"
                  :key="`total_${j}_${k}`"
                  :class="[k === 0 && 'group-start', k + 1 === v.length && 'group-end']"
                  :title="`Итого — ${data.titles[j].groupTitle} — ${data.titles[j].fields[k]}: ${rv}`"
                  v-tippy
                  v-html="rv || '&nbsp;'"
                ></td>
              </template>
            </tr>
          </tbody>
          <thead v-if="data.rows.length > 0">
            <tr>
              <template v-for="(t, i) in data.titles">
                <th
                  v-for="(f, j) in t.fields"
                  :key="`${i}_${j}`"
                  class="param-title"
                  :class="[j === 0 && 'group-start', j + 1 === t.fields.length && 'group-end']"
                  :title="`${t.groupTitle} — ${f}`"
                  v-tippy
                  v-html="f || '&nbsp;'"
                ></th>
              </template>
            </tr>
            <tr>
              <th
                v-for="(t, i) in data.titles"
                :key="i"
                :colspan="t.fields.length"
                class="param-title group-start group-end"
                :title="t.groupTitle"
                v-tippy
                v-html="t.groupTitle || '&nbsp;'"
              ></th>
            </tr>
          </thead>
          <tbody v-if="data.titles.reduce((a, b) => a + b.fields.length, 0) > 0 && data.empty_hospital.length > 0">
            <tr v-for="(h, i) in data.empty_hospital" :key="`empty_${i}`">
              <td :colspan="data.titles.reduce((a, b) => a + b.fields.length, 0)">&nbsp;</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import * as Cookies from 'es-cookie';
import { mapGetters } from 'vuex';
import moment from 'moment';
import axios from 'axios';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import VueApexCharts from 'vue-apexcharts';

import api from '@/api';
import * as actions from '@/store/action-types';
import RadioField from '@/fields/RadioField.vue';

const HOURS = [{ id: '-', label: 'нет' }];

for (let i = 0; i < 24; i++) {
  const id = i < 10 ? `0${i}` : String(i);
  const label = `${id}:00`;
  HOURS.push({ id, label });
}

const MIN_FONT = 9;
const MAX_FONT = 14;

const MODE_DASHBOARD = 'Дэшборд мониторингов';
const MODE_SEARCH = 'Поиск';

const MODES = [MODE_DASHBOARD, MODE_SEARCH];

const CHART_TYPES = {
  BAR: 'bar',
  COLUMN: 'bar',
  PIE: 'pie',
  RADAR: 'radar',
};

const CHART_OPTIONS = {};

export default {
  components: {
    Treeselect,
    RadioField,
    VueApexCharts,
  },
  data() {
    return {
      research: null,
      loadedResearch: null,
      date: moment().format('YYYY-MM-DD'),
      loadedDate: '',
      hour: '-',
      HOURS,
      data: null,
      fontSize: 12,
      mode: MODE_DASHBOARD,
      MODE_DASHBOARD,
      MODE_SEARCH,
      MODES,
      CHART_TYPES,
      CHART_OPTIONS,
      dashboards: [],
      dashboardPk: null,
      dateDashboard: moment().format('YYYY-MM-DD'),
      loadedDashboardDate: '',
      dashboard: {
        title: null,
      },
      charts: [],
    };
  },
  watch: {
    mode: {
      handler() {
        if (this.mode === MODE_SEARCH) {
          this.entryToSearch();
        } else if (this.mode === MODE_DASHBOARD) {
          this.entryToDashboard();
        }
      },
      immediate: true,
    },
  },
  computed: {
    ...mapGetters(['researches']),
    monitorings() {
      return (this.researches['-12'] || []).map(r => ({ id: r.pk, label: r.title }));
    },
    canIncFont() {
      return this.fontSize < MAX_FONT;
    },
    canDecFont() {
      return this.fontSize > MIN_FONT;
    },
    loadedDashboardDateString() {
      const parts = this.loadedDashboardDate.split('-');
      if (parts.length < 3) {
        return '';
      }

      return `${parts[2]}.${parts[1]}.${parts[0]}`;
    },
  },
  methods: {
    async entryToSearch() {
      if (Object.keys(this.researches).length === 0) {
        await this.$store.dispatch(actions.INC_LOADING);
        await this.$store.dispatch(actions.GET_RESEARCHES);
        await this.$store.dispatch(actions.DEC_LOADING);
      }
    },
    async entryToDashboard() {
      if (Object.keys(this.dashboards).length === 0) {
        await this.$store.dispatch(actions.INC_LOADING);
        const { rows } = await api('/monitorings/listdashboard');
        this.dashboards = rows;
        await this.$store.dispatch(actions.DEC_LOADING);
      }
      if (this.dashboards.length > 0 && this.dashboardPk === null) {
        this.dashboardPk = this.dashboards[0].id;
      }
      if (this.dashboardPk !== null) {
        await this.loadDashboard();
      }
    },
    async loadSearch() {
      await this.$store.dispatch(actions.INC_LOADING);
      this.loadedResearch = this.research;
      this.loadedDate = this.date;
      const { rows } = await api('/monitorings/search', this, ['research', 'date', 'hour']);
      this.data = rows;
      await this.$store.dispatch(actions.DEC_LOADING);
      if (this.$refs.loadButton) {
        window.$(this.$refs.loadButton).blur();
      }
    },
    async loadDashboard() {
      await this.$store.dispatch(actions.INC_LOADING);
      this.loadedDashboardDate = this.dateDashboard;
      this.dashboard = {
        title: (this.dashboards.find(d => d.id === this.dashboardPk) || {}).label,
      };
      const { rows } = await api('/monitorings/dashboard', {
        dashboard: this.dashboardPk,
        date: this.dateDashboard,
      });
      this.charts = rows;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    incFont() {
      this.fontSize = Math.min(MAX_FONT, this.fontSize + 1);
    },
    decFont() {
      this.fontSize = Math.max(MIN_FONT, this.fontSize - 1);
    },
    print_data() {
      axios({
        method: 'post',
        url: '/api/monitorings/filexlsx',
        data: {
          research: this.loadedResearch,
          date: this.loadedDate,
          data: this.data,
        },
        responseType: 'blob',
        headers: {
          'X-CSRFToken': Cookies.get('csrftoken'),
        },
      })
        .then(response => {
          const blob = new Blob([response.data], { type: 'application/ms-excel' });
          const downloadUrl = window.URL.createObjectURL(blob);
          let filename = '';
          const disposition = response.headers['content-disposition'];
          if (disposition && disposition.indexOf('attachment') !== -1) {
            const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
            const matches = filenameRegex.exec(disposition);
            if (matches != null && matches[1]) {
              filename = matches[1].replace(/['"]/g, '');
            }
          }
          const a = document.createElement('a');
          if (typeof a.download === 'undefined') {
            window.location.href = downloadUrl;
          } else {
            a.href = downloadUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
          }
        })
        .catch(error => {
          console.error(error);
          this.$root.$emit('msg', 'error', 'Сохранить данные в виде XLSX не удалось');
        });
    },
    getHeight(c) {
      return Math.max(c.type === 'BAR' ? c.data.length * 15 * c.fields.length : 0, 390);
    },
    getOptions(c) {
      return {
        chart: {
          id: `${c.type}_${c.pk}`,
          toolbar: {
            show: false,
          },
          zoom: {
            enabled: false,
          },
          fontFamily: 'Open Sans, Helvetica, Arial, sans-serif',
        },
        [{ BAR: 'xaxis', COLUMN: 'xaxis', PIE: 'labels' }[c.type] || 'xaxis']:
          c.type === 'PIE'
            ? c.data.map(d => d.title)
            : {
              categories: c.data.map(d => d.title),
            },
        plotOptions: {
          bar: {
            horizontal: c.type === 'BAR',
            dataLabels: {
              position: 'top',
            },
          },
        },
      };
    },
    getSeries(c) {
      if (c.type === 'PIE' && c.fields.length === 1) {
        return c.data.map(d => d.values[0]);
      }
      return c.fields.map((name, i) => ({ name, data: c.data.map(d => Number(d.values[i]) || 0) }));
    },
  },
};
</script>

<style scoped lang="scss">
.mode-select {
  position: absolute;
  top: 41px;
  left: 10px;
  right: 10px;
  height: 36px;
}

.dashboard {
  padding: 30px 10px 10px 10px;

  h6 {
    font-weight: bold;
  }
}

.chart {
  margin: 0 0 10px 0;
  padding: 10px;

  .chart-inner {
    overflow-x: hidden;
    overflow-y: auto;
    min-height: 410px;
    max-height: 410px;
  }
}

.dash-root {
  overflow-x: hidden;
}

.report-root {
  position: absolute;
  top: 82px;
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

.scroll-container {
  white-space: nowrap;
  overflow-x: auto;
  overflow-y: auto;
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  align-items: start;
  justify-content: start;
  margin-left: -10px;
  margin-right: -10px;
  position: absolute;
  top: 72px;
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
      width: 305px;
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
      font-size: var(--font-size-mon, 12px);
      word-break: keep-all;
      white-space: nowrap;
      text-overflow: ellipsis;
      overflow-x: hidden;
    }

    td,
    th {
      transition: 0.15 all linear;
      &:hover {
        background-color: rgba(#049372, 0.1);
      }
    }
  }
}

.group-start {
  border-left-width: 3px;
}

.group-end {
  border-right-width: 3px;
}

.font-settings {
  font-weight: bold;
}
</style>
