<template>
  <div style="height: 100%;width: 100%;position: relative">
    <div class="top-picker">
      <div style="align-self: stretch;display: inline-flex;align-items: center;padding: 1px 0 1px 5px;
      flex: 1;margin: 0;font-size: 12px;width: 101px;color:#fff">
        <span
          style="display: block;max-height: 2.2em;line-height: 1.1em;vertical-align: top">Дата<br/>подтверждения:</span>
      </div>
      <div style="width: 186px;display: inline-block;vertical-align: top">
        <date-range v-model="date_range"/>
      </div>
      <div class="top-inner">
        <button class="btn btn-blue-nb btn-ell"
                style="display: inline-block;vertical-align: top;border-radius: 0;width: auto;" title="Загрузить данные"
                @click="load_history" v-if="individual_pk > -1 && params.length > 0">
          <i class="glyphicon glyphicon-list-alt"></i> Загрузить данные
        </button>
        <!--<button class="btn btn-blue-nb btn-ell"
                style="display: inline-block;vertical-align: top;border-radius: 0;width: auto;"
                title="Построить графики"
                v-if="rows.length > 0" @click="build_graphs">
          <i class="glyphicon glyphicon-flash"></i> Построить графики
        </button>-->
      </div>
    </div>
    <div class="content-picker" v-if="rows.length > 0">
      <table class="table table-bordered table-smm">
        <colgroup>
          <col width="90">
          <col width="120">
          <col>
          <col>
          <col width="120">
          <col width="110">
        </colgroup>
        <thead>
        <tr>
          <th>Дата</th>
          <th>Исследование</th>
          <th>Параметр</th>
          <th>Значение</th>
          <th>Референс</th>
          <th>Результат</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="r in rows" :key="r.pk" :class="{not_norm: r.is_norm !== 'normal'}">
          <td>{{r.date}}</td>
          <td class="research">{{get_param_name(r.research, r.pk).research}}</td>
          <td>{{get_param_name(r.research, r.pk).title}}</td>
          <td v-if="r.active_ref.r" class="v-field">
            <span v-if="r.not_norm_dir === 'n_up'">&uarr;</span>
            <span v-if="r.not_norm_dir === 'up'">&uarr;&uarr;</span>
            <span v-if="r.not_norm_dir === 'n_down'">&darr;</span>
            <span v-if="r.not_norm_dir === 'down'">&darr;&darr;</span>
            {{r.value}} <span class="units">{{r.units}}</span>
          </td>
          <td v-if="r.active_ref.r">{{r.active_ref.r}}</td>
          <td v-else colspan="2">{{r.value}} <span class="units">{{r.units}}</span></td>
          <td><a href="#" @click.prevent="print_results(r.direction)" title="Печать результатов направления">{{r.direction}}</a>
          </td>
        </tr>
        </tbody>
      </table>
    </div>
    <div class="content-none" v-else>
      Нет данных
    </div>
    <!--<report-chart-viewer v-if="show_charts" :directory="params_titles" :rows_data="rows"/>-->
  </div>
</template>

<script>
import moment from 'moment';
import DateRange from './DateRange.vue';
// import ReportChartViewer from './ReportChartViewer'
import directionsPoint from '../api/directions-point';
import * as actions from '../store/action-types';

export default {
  components: { DateRange /* ReportChartViewer */ },
  name: 'results-report-viewer',
  props: {
    individual_pk: {
      type: Number,
      default: -1,
    },
    params: {
      type: Array,
      default: () => [],
    },
    params_directory: {
      type: Object,
      default: () => ({}),
    },
  },
  data() {
    return {
      date_range: [moment().subtract(3, 'month').format('DD.MM.YYYY'), moment().format('DD.MM.YYYY')],
      is_created: false,
      rows: [],
      show_charts: false,
    };
  },
  computed: {},
  mounted() {
    this.is_created = true;
    this.$root.$on('hide_report-chart-viewer', () => {
      this.show_charts = false;
    });
  },
  methods: {
    params_titles() {
      const d = {};
      for (const rpk of Object.keys(this.params_directory)) {
        if (!d[rpk]) d[rpk] = {};
        for (const p of this.params_directory[rpk].params) {
          d[rpk][p.pk] = { title: p.title, research: this.params_directory[rpk].short_title };
        }
      }
      return d;
    },
    get_param_name(rpk, ppk) {
      const pt = this.params_titles();
      if (pt[rpk] && pt[rpk][ppk]) {
        return pt[rpk][ppk];
      }
      return { title: '', research: '' };
    },
    build_graphs() {
      this.show_charts = true;
    },
    show_results(pk) {
      this.$root.$emit('show_results', pk);
    },
    print_direction(pk) {
      this.$root.$emit('print:directions', [pk]);
    },
    print_results(pk) {
      this.$root.$emit('print:results', [pk]);
    },
    load_history() {
      if (!this.is_created) return;
      this.$root.$emit('validate-datepickers');
      this.is_created = false;
      this.$store.dispatch(actions.INC_LOADING);
      directionsPoint.getResultsReport({
        individual: this.individual_pk,
        params: this.params,
        date_start: this.date_range[0],
        date_end: this.date_range[1],
      }).then((data) => {
        this.rows = data.data;
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
        this.is_created = true;
      });
    },
    clear() {
      this.rows = [];
    },
  },
  watch: {
    individual_pk() {
      this.clear();
    },
  },
};
</script>

<style scoped lang="scss">

  .table-smm {
    table-layout: fixed;

    td, th {
      padding: 2px;
      word-break: break-all;
    }
  }

  .research {
    font-size: 12px;
    word-break: break-word!important;
  }

  .units {
    font-size: 12px;
    color: #8d8d8d;
  }

  tr:hover .units {
    color: #000
  }

  .not_norm {
    background-color: #f1f1f1;

    td:not(:first-child) {
      border-left-color: #ffa04d;
    }
    td:not(:last-child) {
      border-right-color: #ffa04d;
    }

    .v-field {
      font-weight: bold;
      span {
        padding-right: 4px;
        font-weight: normal;
      }
    }
  }

  .top-picker, .bottom-picker {
    height: 34px;
    background-color: #AAB2BD;
    position: absolute;
    left: 0;
    right: 0;
  }

  .top-picker {
    top: 0;
    white-space: nowrap;

    ::v-deep {
      input {
        border-radius: 0;
        border: none;
        border-bottom: 1px solid #AAB2BD;
        background: #fff;
      }

      .input-group-addon {
        border: 1px solid #AAB2BD;
        border-top: none;
      }
    }
  }

  .content-picker, .content-none, .bottom-inner {
    display: flex;
    flex-wrap: wrap;
    justify-content: stretch;
    align-content: center;
    align-items: stretch;
    overflow-y: auto;
  }

  .content-picker {
    align-content: flex-start;
  }

  .content-none {
    align-items: center;
    align-content: center;
    justify-content: center;
  }

  .top-inner {
    position: absolute;
    left: 290px;
    top: 0;
    right: 0;
    height: 34px;
    overflow: visible;
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
    align-items: stretch;
    justify-content: flex-start;
  }

  .content-picker, .content-none {
    position: absolute;
    top: 34px;
    bottom: 0;
    left: 0;
    right: 0;
    overflow-y: auto;
  }
</style>
