<template>
  <div class="root-agg">
    <div class="chart" v-for="chart in charts" v-if="!!dataCharts[chart]">
      <div class="chart-title">{{chart}}</div>
      <VueApexCharts
        type="line"
        height="330"
        :options="get_options(dataCharts[chart])" :series="dataCharts[chart].series"
      />
    </div>
  </div>
</template>

<script>
  import VueApexCharts from 'vue-apexcharts'

  import stationar_point from '../api/stationar-point'

  const charts = [
    'Температура (°C)',
    'Пульс (уд/с)',
    'Давление',
  ];

  const mergeData = {
    'Систолическое давление (мм рт.с)': 'Давление',
    'Диастолическое давление (мм рт.с)': 'Давление',
  };

  export default {
    components: {
      VueApexCharts,
    },
    props: {
      pk: {},
    },
    data() {
      return {
        charts,
        data: {},
      }
    },
    async mounted() {
      await this.load()
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
            }
          }
          result[lk].series.push({
            name: k,
            data: this.data[k].data || [],
          })
        }
        return result;
      },
    },
    methods: {
      async load() {
        this.data = await stationar_point.aggregateTADP(this, ['pk'])
      },
      get_options(data) {
        return {
          chart: {
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
          xaxis: {categories: data.xtext || []},
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
          },
          theme: {
            palette: 'palette5',
          },
          grid: {
            show: true,
            yaxis: {
              lines: {
                show: true,
              }
            },
            xaxis: {
              lines: {
                show: true,
              }
            },
          },
          markers: {
            size: 4,
          },
        };
      },
    },
  }
</script>

<style scoped lang="scss">
  .root-agg {
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
</style>
