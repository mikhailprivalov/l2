<template>
  <div class="root-agg">
    <a
      v-if="selectedChartsValues.length > 0"
      :href="printHref"
      target="_blank"
      class="top-print a-under"
    >печать</a>
    <div
      v-for="chart in charts"
      v-if="/*eslint-disable-line vue/no-use-v-if-with-v-for*/ !!dataCharts[chart]"
      :key="chart"
      class="chart"
    >
      <label class="chart-title">
        <input
          v-model="selectedCharts[chart]"
          type="checkbox"
        >
        {{ chart }}
      </label>
      <VueApexCharts
        type="line"
        height="330"
        :options="get_options(dataCharts[chart])"
        :series="dataCharts[chart].series"
      />
    </div>
    <a
      v-if="selectedChartsValues.length > 0"
      :href="printHref"
      target="_blank"
      class="bottom-print a-under"
    >печать</a>
  </div>
</template>

<script lang="ts">
import VueApexCharts from 'vue-apexcharts';

import stationarPoint from '@/api/stationar-point';

const charts = ['Температура (°C)', 'Пульс (уд/м)', 'Давление'];

const mergeData = {
  'Систолическое давление (мм рт.с)': 'Давление',
  'Диастолическое давление (мм рт.с)': 'Давление',
};

export default {
  components: {
    VueApexCharts,
  },
  props: {
    directions: {},
  },
  data() {
    return {
      charts,
      data: {},
      selectedCharts: charts.reduce((a, c) => ({ ...a, [c]: false }), {}),
    };
  },
  computed: {
    dataCharts() {
      const result = {};
      for (const k of Object.keys(this.data)) {
        const lk = mergeData[k] || k;
        if (!result[lk]) {
          result[lk] = {
            xtext: this.data[k].xtext || [],
            series: [],
          };
        }
        result[lk].series.push({
          type: 'line',
          name: k,
          data: this.data[k].data || [],
        });
      }
      return result;
    },
    selectedChartsValues() {
      return this.charts.filter((c) => this.selectedCharts[c]);
    },
    printHref() {
      const titles = encodeURI(JSON.stringify(this.selectedChartsValues));
      const directions = encodeURI(JSON.stringify(this.directions));
      return `/forms/pdf?type=107.01&hosp_pks=${directions}&titles=${titles}`;
    },
  },
  async mounted() {
    await this.load();
  },
  methods: {
    async load() {
      this.data = await stationarPoint.aggregateTADP(this, ['directions']);
    },
    get_options(data) {
      return {
        chart: {
          type: 'area',
          animations: {
            enabled: false,
          },
          toolbar: {
            show: false,
          },
          zoom: {
            enabled: false,
          },
          fontFamily: 'Open Sans, Helvetica, Arial, sans-serif',
        },
        xaxis: {
          categories: data.xtext || [],
          labels: {
            cssClass: 'apexcharts-xaxis-label',
          },
        },
        yaxis: {
          labels: {
            show: true,
            align: 'right',
            minWidth: 0,
            maxWidth: 160,
            cssClass: 'apexcharts-yaxis-label',
          },
        },
        stroke: {
          curve: 'straight',
          width: 2,
          dashArray: [0, 8, 5],
        },
        theme: {
          palette: 'palette5',
        },
        grid: {
          show: true,
          yaxis: {
            lines: {
              show: false,
            },
          },
          xaxis: {
            lines: {
              show: true,
            },
          },
          padding: {
            right: 35,
            left: 35,
          },
        },
        dataLabels: {
          enabled: true,
        },
      };
    },
  },
};
</script>

<style scoped lang="scss">
.root-agg {
  position: relative;
}

.top-print {
  position: absolute;
  top: 0;
  right: 5px;
  z-index: 1;
}

.bottom-print {
  position: absolute;
  bottom: 0;
  right: 5px;
}

.chart {
  margin-bottom: 5px;

  &-title {
    font-weight: bold;
  }
}
</style>

<style lang="scss">
.apexcharts-yaxis-label {
  font-weight: 600;
  font-size: 13px;
}

.apexcharts-xaxis-label {
  max-width: 60px;
  white-space: normal;
  word-break: keep-all;
}
</style>
