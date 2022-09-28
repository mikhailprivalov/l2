<template>
  <div
    ref="dashboardRoot"
    class="dash-root"
    :class="[fullscreen && 'dash-fullscreen', withoutLogin && 'dash-without-login']"
  >
    <div class="dashboard">
      <div class="filters">
        <div class="row">
          <div
            class="col-xs-6"
            style="padding-right: 5px"
          >
            <div class="input-group treeselect-input-group input-multiple">
              <Treeselect
                v-if="!fullscreen"
                v-model="dashboardPk"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="dashboards"
                placeholder="Дэшборд не выбран"
                :append-to-body="true"
                class="treeselect-wide"
                :clearable="false"
              />
              <template v-if="showDatePicker">
                <input
                  v-model="dateStart"
                  type="text"
                  class="form-control"
                  placeholder="начальная дата"
                  @focus="paused = true"
                  @blur="paused = false"
                >
                <input
                  v-model="dateEnd"
                  type="text"
                  class="form-control"
                  placeholder="конечная дата"
                  @focus="paused = true"
                  @blur="paused = false"
                >
              </template>
            </div>
            <h4 v-if="dashboard.title && fullscreen">
              {{ dashboard.title }} — {{ loadedDashboardDateString }}
            </h4>
          </div>
          <div class="col-xs-6 text-right">
            {{ reloadingText }}
            &nbsp;
            &nbsp;
            &nbsp;
            <a
              v-tippy
              href="#"
              class="a-under fullscreen-link"
              title="Полный экран"
              @click.prevent="toggleFullscreen"
            >
              <i
                v-if="!fullscreen"
                class="fas fa-expand"
              />
              <i
                v-else
                class="fas fa-compress"
              />
            </a>
          </div>
          <div
            v-if="dashboard.title && !fullscreen"
            class="col-xs-12"
          >
            <h4 class="simple-header">
              {{ dashboard.title }} — {{ loadedDashboardDateString }}
            </h4>
          </div>
        </div>
      </div>

      <Charts
        :charts="charts"
        :fullscreen="fullscreen"
        :without-login="withoutLogin"
        :is-narrow="isNarrow"
      />
    </div>
  </div>
</template>

<script lang="ts">
import moment from 'moment';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import * as actions from '@/store/action-types';

import Charts from './Charts.vue';

export default {
  components: {
    Treeselect,
    Charts,
  },
  data() {
    return {
      loadedDate: '',
      hour: '-',
      dashboards: [],
      dashboardPk: null,
      loadedDashboardDate: '',
      dashboard: {
        title: null,
      },
      charts: [],
      fullscreen: false,
      hasMount: false,
      loading: false,
      intervalReloadSeconds: 0,
      restMsToReload: 0,
      checkReloadInterval: null,
      isNarrow: false,
      dateStart: null,
      dateEnd: null,
      showDatePicker: false,
      paused: false,
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
    dashboardUrlPk() {
      return Number(this.$route.params.id);
    },
    withoutLogin() {
      return Boolean(this?.$route?.meta?.hideHeaderWithoutLogin);
    },
    reloadingText() {
      if (this.intervalReloadSeconds > 0) {
        const appendString = this.isNarrow ? 'c.' : 'сек. до перезагрузки';
        return `${Math.max(Math.round(this.restMsToReload / 100) / 10, 0).toFixed(1)} ${appendString}`;
      }
      return null;
    },
  },
  watch: {
    async dashboardPk() {
      if (this.dashboardPk !== this.dashboardUrlPk) {
        this.$router.push({ name: 'statistics_report', params: this.dashboardPk ? { id: this.dashboardPk } : {} });

        if (this.hasMount) {
          this.loading = false;
          this.paused = true;
          await this.loadDashboard();
          this.paused = false;
        }
      }
    },
    dashboardUrlPk() {
      if (this.hasMount && this.dashboardUrlPk !== this.dashboardPk) {
        this.dashboardPk = this.dashboardUrlPk;
        this.loading = false;
        this.loadDashboard();
      }
    },
    intervalReloadSeconds: {
      immediate: true,
      handler() {
        this.restMsToReload = this.intervalReloadSeconds * 1000;
      },
    },
    async restMsToReload() {
      if (this.intervalReloadSeconds > 0 && this.restMsToReload === 0) {
        await this.loadDashboard(true);
        this.restMsToReload = this.intervalReloadSeconds * 1000;
      }
    },
    dateStart() {
      this.updateQuery();
    },
    dateEnd() {
      this.updateQuery();
    },
  },
  created() {
    window.addEventListener('resize', this.onWindowResize);
    this.onWindowResize();
  },
  destroyed() {
    window.removeEventListener('resize', this.onWindowResize);
  },
  async mounted() {
    const params = new URLSearchParams(window.location.search);
    if (params.has('dateStart') && params.has('dateEnd')) {
      this.dateStart = params.get('dateStart');
      this.dateEnd = params.get('dateEnd');
    }
    await this.entryToDashboard();
    this.checkReloadInterval = setInterval(() => {
      if (this.restMsToReload > 0 && !this.paused) {
        this.restMsToReload = Math.max(this.restMsToReload - 200, 0);
      }
    }, 200);
  },
  beforeDestroy() {
    clearInterval(this.checkReloadInterval);
  },
  methods: {
    updateQuery() {
      if (!this.dateStart || !this.dateEnd) {
        window.history.replaceState(null, null, window.location.pathname);
      } else {
        const params = new URLSearchParams(window.location.search);
        params.set('dateStart', this.dateStart);
        params.set('dateEnd', this.dateEnd);
        window.history.replaceState(null, null, `${window.location.pathname}?${params.toString()}`);
      }
    },
    onWindowResize() {
      const { innerWidth: width } = window;
      this.isNarrow = width <= 550;
    },
    async toggleFullscreen() {
      await this.$fullscreen.toggle(this.$refs.dashboardRoot, {
        teleport: true,
        callback: (isFullscreen) => {
          this.fullscreen = isFullscreen;
        },
      });
    },
    async entryToDashboard() {
      if (Object.keys(this.dashboards).length === 0) {
        await this.$store.dispatch(actions.INC_LOADING);
        const { rows } = await this.$api('/dashboards/listdashboard');
        this.dashboards = rows;
        await this.$store.dispatch(actions.DEC_LOADING);
      }
      if (this.dashboards.length > 0 && this.dashboardPk === null) {
        this.dashboardPk = (this.dashboardUrlPk && this.dashboards.find(d => d.id === this.dashboardUrlPk))
          ? this.dashboardUrlPk
          : this.dashboards[0].id;
        this.loading = false;
        await this.loadDashboard();
      }
      this.hasMount = true;
    },
    async loadDashboard(hidden = false) {
      if (this.loading) {
        return;
      }
      if (!this.dashboardPk) {
        if (!hidden) {
          this.charts = [];
          this.dashboard = {
            title: null,
          };
        }
        return;
      }

      this.loading = true;
      if (!hidden) {
        await this.$store.dispatch(actions.INC_LOADING);
      }
      this.loadedDashboardDate = moment().format('YYYY-MM-DD');
      this.dashboard = {
        title: this.dashboards.find((d) => d.id === this.dashboardPk)?.label,
      };
      const {
        rows, ok, intervalReloadSeconds, datesParam, showDatesParam,
      } = await this.$api('/dashboards/dashboard-charts', this, ['dateStart', 'dateEnd'], {
        dashboard: this.dashboardPk,
      });
      this.charts = rows || [];
      this.intervalReloadSeconds = intervalReloadSeconds || 0;
      this.dateStart = null;
      this.dateEnd = null;
      this.showDatePicker = false;
      if (showDatesParam && datesParam) {
        this.showDatePicker = !!showDatesParam;
        this.dateStart = datesParam.date_start;
        this.dateEnd = datesParam.date_end;
      }
      if (!hidden) {
        await this.$store.dispatch(actions.DEC_LOADING);
      }
      if (!ok) {
        this.$root.$emit('msg', 'error', 'Ошибка выполнения запроса', this.intervalReloadSeconds * 1000 || 4000);
      }

      this.loading = false;
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

.dash-root {
  overflow-x: hidden;
  margin-top: -20px;
  background: #f2f2f2;

  &.dash-fullscreen, &.dash-without-login {
    margin-top: 0;
  }
}

.dash-fullscreen .filters h4 {
  margin-top: 5px;
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
      transition: all 0.15s linear;
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

.fullscreen-link {
  font-size: 16px;
}
</style>
