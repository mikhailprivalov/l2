<template>
  <div class="modal fade" tabindex="-1">
    <div class="modal-dialog" style="max-width: 800px;width: 100%">
      <div class="modal-content">
        <div class="modal-header">
          <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span></button>
          <h4 class="modal-title">Отчета по услуге</h4>
        </div>
        <div class="modal-body">
          <div class="row">
            <div class="col-xs-5 text-right">
              <date-selector :date_type.sync="date_type" :values.sync="values"/>
            </div>
            <div class="col-xs-7">
              <div v-if="deps_list.length > 0">
                <select-picker :val="dep" :options="deps_list" :func="change_dep"/>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <div class="row">
            <div class="col-xs-3"></div>
            <div class="col-xs-6">
              <button type="button" @click="make_report"
                      :disabled="(user === '-1' || user === '') && dep === '-1'"
                      class="btn btn-primary-nb btn-blue-nb2">
                Печать
              </button>
            </div>
            <div class="col-xs-3" style="padding-left: 0">
              <button type="button" class="btn btn-primary-nb btn-blue-nb" data-dismiss="modal">Закрыть</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  import DateSelector from './DateSelector.vue'
  import SelectPicker from './SelectPicker'

  export default {
    name: 'statistics-researches-print-modal',
    components: {
      DateSelector,
      SelectPicker
    },
    props: {
      deps: {
        type: Array,
        required: false,
        default() {
          return [];
        },
      },
    },
    data() {
      return {
        date_type: 'd',
        values: {
          date: '',
          month: '',
          year: ''
        },
        dep: '-1',
      }
    },
    computed: {
      deps_list() {
        let u = []
        for (let u_row of this.deps) {
          u.push({value: u_row.pk, label: u_row.title})
        }
        return u
      },
    },
    methods: {
      change_dep(v) {
        if (!v) {
          v = ''
        }
        if (Array.isArray(v)) {
          v = v.join(',')
        }
        this.dep = v
      },
      make_report() {
        // window.open(`/statistic/xls?type=statistics-tickets-print&user=${this.selected_users}&department=${this.dep}&date_type=${this.date_type}&date_values=${encodeURIComponent(JSON.stringify(this.values))}&fin=${this.fin}`, '_blank')
        window.open(`/statistic/xls?type=statistics-research&department=${this.dep}&date_type=${this.date_type}&date_values=${encodeURIComponent(JSON.stringify(this.values))}&fin=${this.fin}`, '_blank')
      }
    },
  }
</script>
