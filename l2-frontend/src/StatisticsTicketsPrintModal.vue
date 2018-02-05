<template>
  <div class="modal fade" tabindex="-1">
    <div class="modal-dialog" style="width: 680px">
      <div class="modal-content">
        <div class="modal-header">
          <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span></button>
          <h4 class="modal-title">Печать статталонов</h4>
        </div>
        <div class="modal-body">
          <div class="row">
            <div class="col-xs-5 text-right">
              <date-range style="width: auto" v-model="date_range"/>
            </div>
            <div class="col-xs-7">
              <select-picker :val="user" :options="users_list" :func="change_user" :multiple="users.length > 1"
                             :actions_box="users.length > 1"/>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <div class="row">
            <div class="col-xs-3"></div>
            <div class="col-xs-6">
              <button type="button" @click="make_report" class="btn btn-primary-nb btn-blue-nb2">
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
  import moment from 'moment'
  import DateRange from './ui-cards/DateRange'
  import SelectPicker from './SelectPicker'

  export default {
    name: 'statistics-tickets-print-modal',
    components: {
      DateRange,
      SelectPicker
    },
    props: {
      users: {
        type: Array
      }
    },
    data() {
      return {
        date_range: [moment().format('DD.MM.YYYY'), moment().format('DD.MM.YYYY')],
        user: '-1',
      }
    },
    computed: {
      users_list() {
        let u = []
        for (let u_row of this.users) {
          u.push({value: u_row.pk, label: u_row.fio})
        }
        return u
      },
      selected_users() {
        return this.user.split(',')
      }
    },
    methods: {
      change_user(v) {
        if (!v) {
          v = ''
        }
        if (Array.isArray(v)) {
          v = v.join(',')
        }
        this.user = v
      },
      make_report() {
        window.open(`/statistic/xls?type=statistics-tickets-print&users=${encodeURIComponent(JSON.stringify(this.selected_users))}&date-start=${this.date_range[0]}&date-end=${this.date_range[1]}`, '_blank')
      }
    },
  }
</script>
