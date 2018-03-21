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
        <button class="btn btn-blue-nb btn-ell" style="display: inline-block;vertical-align: top;border-radius: 0;width: auto;" title="Загрузить данные"
                @click="load_history" v-if="individual_pk > -1 && params.length > 0">
          <i class="glyphicon glyphicon-tasks"></i> Загрузить данные
        </button>
      </div>
    </div>
    <div class="content-picker" v-if="rows.length > 0">
      <table class="table table-bordered table-smm">
        <colgroup>
          <col width="90">
          <col>
          <col>
          <col width="120">
          <col width="110">
        </colgroup>
        <thead>
        <tr>
          <th>Дата</th>
          <th>Параметр</th>
          <th>Значение</th>
          <th>Референс</th>
          <th>Направление</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="r in rows" :class="{not_norm: r.is_norm !== 'normal'}">
          <td>{{r.date}}</td>
          <td>{{get_param_name(r.research, r.pk)}}</td>
          <td v-if="r.active_ref.r">{{r.value}}</td>
          <td v-if="r.active_ref.r">{{r.active_ref.r}}</td>
          <td v-else colspan="2">{{r.value}}</td>
          <td><a href="#" @click.prevent="print_results(r.direction)" title="Печать результатов направления">{{r.direction}}</a>
          </td>
        </tr>
        </tbody>
      </table>
    </div>
    <div class="content-none" v-else>
      Нет данных
    </div>
  </div>
</template>

<script>
  import DateRange from './ui-cards/DateRange'
  import directions_point from './api/directions-point'
  import * as action_types from './store/action-types'
  import moment from 'moment'

  export default {
    components: {DateRange},
    name: 'results-report-viewer',
    props: {
      individual_pk: {
        type: Number,
        default: -1
      },
      params: {
        type: Array,
        default: []
      },
      params_directory: {
        type: Object,
        default: {}
      },
    },
    data() {
      return {
        date_range: [moment().subtract(3, 'month').format('DD.MM.YYYY'), moment().format('DD.MM.YYYY')],
        is_created: false,
        rows: []
      }
    },
    computed: {},
    mounted() {
      this.is_created = true
    },
    methods: {
      get_param_name(rpk, ppk) {
        if (this.params_directory.hasOwnProperty(rpk)) {
          for (let p of this.params_directory[rpk].params) {
            if (p.pk === ppk) {
              return p.title
            }
          }
        }
        return ''
      },
      show_results(pk) {
        this.$root.$emit('show_results', pk)
      },
      print_direction(pk) {
        this.$root.$emit('print:directions', [pk])
      },
      print_results(pk) {
        this.$root.$emit('print:results', [pk])
      },
      load_history() {
        if (!this.is_created)
          return
        this.$root.$emit('validate-datepickers')
        this.is_created = false
        let vm = this
        vm.$store.dispatch(action_types.INC_LOADING).then()
        directions_point.getResultsReport(this.individual_pk, this.params, this.date_range[0], this.date_range[1]).then(data => {
          console.log(data)
          vm.rows = data.data
        }).finally(() => {
          vm.$store.dispatch(action_types.DEC_LOADING).then()
          vm.is_created = true
        })
      },
      clear() {
        this.rows = []
      }
    },
    watch: {
      individual_pk() {
        this.clear()
      }
    }
  }
</script>

<style scoped lang="scss">

  .table-smm {
    table-layout: fixed;

    td, th {
      padding: 2px;
    }
  }

  .not_norm {
    background-color: #f1f1f1;

    td:not(:first-child) {
      border-left-color: #ffa04d;
    }
    td:not(:last-child) {
      border-right-color: #ffa04d;
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

    /deep/ {
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
