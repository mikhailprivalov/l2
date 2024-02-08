<template>
  <div
    :class="[
      fullpage ? `fullpage-charts fullpage-charts-count-${charts.length}` : 'row',
      fullscreen && 'fullscreen',
      withoutLogin && 'without-login'
    ]"
  >
    <div
      v-for="c in charts"
      :key="c.pk"
      :class="fullpage ? 'fullpage-chart' : 'col-xs-12 col-md-6 col-xl-4'"
    >
      <div class="card-no-hover card card-1 chart">
        <h6 class="card-header">
          {{ c.title }}
        </h6>
        <div class="chart-inner">
          <VueApexCharts
            :key="`${c.pk}-${fullpage}`"
            :type="CHART_TYPES[c.type] || c.type.toLowerCase()"
            :options="getOptions(c)"
            :series="getSeries(c)"
            :height="getHeight(c)"
          />
        </div>
      </div>
    </div>
    <div
      v-for="i in emptyCharts"
      :key="`placeholder-${i}`"
    />
  </div>
</template>

<script lang="ts">
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import VueApexCharts from 'vue-apexcharts';

const CHART_TYPES = {
  BAR: 'bar',
  COLUMN: 'bar',
  PIE: 'pie',
  RADAR: 'radar',
};

export default {
  components: {
    VueApexCharts,
  },
  props: ['charts', 'fullscreen', 'withoutLogin', 'isNarrow'],
  data() {
    return {
      CHART_TYPES,
    };
  },
  computed: {
    fullpage() {
      return this.charts.length <= 4 && !this.isNarrow;
    },
    emptyCharts() {
      const r = [];

      for (let i = 0; i < 4 - this.charts.length; i++) {
        r.push(i);
      }

      return r;
    },
  },
  methods: {
    getHeight(c) {
      if (this.fullpage) {
        return '100%';
      }
      return Math.max(c.type === 'BAR' ? c.data.length * 15 * c.fields.length : 0, 330);
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
          parentHeightOffset: 0,
        },
        [{ BAR: 'xaxis', COLUMN: 'xaxis', PIE: 'labels' }[c.type] || 'xaxis']:
          c.type === 'PIE'
            ? c.dates
            : {
              categories: c.dates,
              labels: {
                maxHeight: 100,
                style: {
                  fontSize: '10px',
                },
              },
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
            fontSize: '9px',
            colors: ['#111'],
          },
          [c.type === 'BAR' ? 'offsetX' : 'offsetY']: c.type === 'BAR' ? 15 : -20,
        },
        grid: {
          padding: {
            top: c.type === 'PIE' ? 0 : -15,
            bottom: -10,
          },
        },
        legend: {
          show: true,
          showForSingleSeries: false,
        },
      };
    },
    getSeries(c) {
      if (c.type === 'PIE' && c.data.length === 1) {
        return c.data[0].values;
      }
      return c.fields.map((name, i) => ({ name, data: c.data[i].values.map((v) => Number(v) || 0) }));
    },
  },
};
</script>

<style scoped lang="scss">
h6 {
  font-weight: bold;
}

.chart {
  margin: 0 0 10px 0;
  padding: 10px 5px;

  .chart-inner {
    overflow-x: hidden;
    overflow-y: auto;
    min-height: 350px;
    max-height: 350px;
  }
}

.card-header {
  margin-top: 0;
  margin-bottom: 0;
  height: 24px;
}

.fullpage-charts.fullscreen {
  top: 74px;
}

.fullpage-charts.without-login:not(.fullscreen) {
  top: 92px;
}

.fullpage-charts {
  position: absolute;
  top: 122px;
  left: 10px;
  right: 10px;
  bottom: 10px;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
  grid-column-gap: 5px;
  grid-row-gap: 5px;

  &.fullpage-charts-count-1 {
    grid-template-columns: repeat(1, 1fr);
    grid-template-rows: repeat(1, 1fr);
  }

  &.fullpage-charts-count-2 {
    grid-template-columns: repeat(2, 1fr);
    grid-template-rows: repeat(1, 1fr);
  }

  .fullpage-chart {
    height: 100%;
    position: relative;

    .chart {
      position: absolute;
      top: 0;
      bottom: 0;
      right: 0;
      left: 0;
      margin: 0;
    }

    .chart-inner {
      min-height: unset;
      max-height: unset;
      height: calc(100% - 22px);
      overflow-y: hidden;
    }
  }
}
</style>
