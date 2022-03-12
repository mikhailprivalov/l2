<template>
  <div class="dash-root">
    <div class="dashboard">
      <div class="filters">
        <div class="row">
          <div
            class="col-xs-6"
            style="padding-right: 5px"
          >
            <Treeselect
              v-model="dashboardPk"
              :multiple="false"
              :disable-branch-nodes="true"
              :options="dashboards"
              placeholder="Дэшборд не выбран"
              :append-to-body="true"
              class="treeselect-wide treeselect-32px"
            />
          </div>
          <div
            class="col-xs-6"
            style="padding-left: 5px"
          >
            <button
              class="btn btn-blue-nb"
              @click="loadDashboard"
            >
              Загрузить
            </button>
          </div>
        </div>
      </div>
      <h4 v-if="dashboard.title">
        {{ dashboard.title }} — {{ loadedDashboardDateString }}
      </h4>
      <div class="row">
        <div
          v-for="c in charts"
          :key="c.pk"
          class="col-xs-12 col-md-6 col-xl-4"
        >
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
  </div>
</template>

<script lang="ts">
import moment from 'moment';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import VueApexCharts from 'vue-apexcharts';

import * as actions from '@/store/action-types';

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
    VueApexCharts,
  },
  data() {
    return {
      loadedDate: '',
      hour: '-',
      CHART_TYPES,
      CHART_OPTIONS,
      dashboards: [],
      dashboardPk: null,
      loadedDashboardDate: '',
      dashboard: {
        title: null,
      },
      charts: [],
    };
  },
  computed: {
    loadedDashboardDateString() {
      const parts = this.loadedDashboardDate.split('-');
      if (parts.length < 3) {
        return '';
      }

      return `${parts[2]}.${parts[1]}.${parts[0]}`;
    },
  },
  mounted() {
    this.entryToDashboard();
  },
  methods: {
    async entryToDashboard() {
      if (Object.keys(this.dashboards).length === 0) {
        await this.$store.dispatch(actions.INC_LOADING);
        const { rows } = await this.$api('/dashboards/listdashboard');
        this.dashboards = rows;
        await this.$store.dispatch(actions.DEC_LOADING);
      }
      if (this.dashboards.length > 0 && this.dashboardPk === null) {
        this.dashboardPk = this.dashboards[0].id;
        await this.loadDashboard();
      }
    },
    async loadDashboard() {
      await this.$store.dispatch(actions.INC_LOADING);
      this.loadedDashboardDate = moment().format('YYYY-MM-DD');
      this.dashboard = {
        title: (this.dashboards.find((d) => d.id === this.dashboardPk) || {}).label,
      };
      const { rows, ok } = await this.$api('/dashboards/dashboard-charts', {
        dashboard: this.dashboardPk,
      });
      this.charts = rows || [];
      await this.$store.dispatch(actions.DEC_LOADING);
      if (!ok) {
        this.$root.$emit('msg', 'error', 'Ошибка выполнения запроса');
      }
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
            ? c.fields
            : {
              categories: c.dates,
            },
        plotOptions: {
          bar: {
            horizontal: c.type === 'BAR',
            dataLabels: {
              position: 'top',
            },
          },
        },
        dataLabels: {
          style: {
            colors: ['#111'],
          },
          [c.type === 'BAR' ? 'offsetX' : 'offsetY']: c.type === 'BAR' ? 20 : -20,
        },
      };
    },
    getSeries(c) {
      if (c.type === 'PIE' && c.fields.length === 1) {
        return c.data.map((d) => d.values[0]);
      }
      return c.fields.map((name, i) => ({ name, data: c.data[i].values.map((v) => Number(v) || 0) }));
    },
  },
};
</script>

<style scoped lang="scss">
.dashboard {
  padding: 10px 10px 10px 10px;

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
  margin-top: -20px;
}

.filters {
  margin-bottom: 10px;

  input[type='date'] {
    -webkit-appearance: textfield !important;
  }

  input,
  select,
  .btn,
  .input-group-addon {
    height: 32px;
    line-height: 26px;
    padding: 0 10px;
  }
  .btn,
  .input-group-addon {
    padding: 0 10px;
    border: none !important;
  }

  .input-group-btn {
    vertical-align: top;
  }
}

.scroll-container {
  white-space: nowrap;
  overflow-x: auto;
  overflow-y: auto;
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  align-items: flex-start;
  justify-content: flex-start;
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
