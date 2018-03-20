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
                @click="load_history">
          <i class="glyphicon glyphicon-tasks"></i> Загрузить данные
        </button>
      </div>
    </div>
    <div class="content-picker">
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
      params_directory: {
        type: Object,
        default: {}
      },
    },
    data() {
      return {
        date_range: [moment().subtract(3, 'month').format('DD.MM.YYYY'), moment().format('DD.MM.YYYY')],
        is_created: false,
        params: []
      }
    },
    computed: {},
    mounted() {
      this.is_created = true
    },
    methods: {
      show_results(pk) {
        this.$root.$emit('show_results', pk)
      },
      print_direction(pk) {
        this.$root.$emit('print:directions', [pk])
      },
      update_params() {
        let p = []
        for (let rpk of Object.keys(this.params_directory)) {
          for (let par of this.params_directory[rpk].selected_params) {
            p.push(par)
          }
        }
        this.params = p
      },
      load_history() {
        if (!this.is_created)
          return
        this.$root.$emit('validate-datepickers')
        this.update_params()
        // this.is_created = false
        // let vm = this
        // vm.$store.dispatch(action_types.INC_LOADING).then()
      },
    },
  }
</script>

<style scoped lang="scss">

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
