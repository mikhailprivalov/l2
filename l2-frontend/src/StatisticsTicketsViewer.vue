<template>
  <div style="height: 100%;width: 100%;position: relative">
    <div class="top-picker">
      <date-field style="width: 94px;display: inline-block;align-self: stretch" :val.sync="date" :def="date"/>
      <button class="btn btn-blue-nb" @click="load" style="width: 42px;display: inline-block;align-self: stretch"><i
        class="glyphicon glyphicon-refresh"></i></button>
      <button class="btn btn-blue-nb" style="width: 94px;display: inline-block;align-self: stretch" @click="print"><i
        class="glyphicon glyphicon-th-list"></i> Экспорт
      </button>
    </div>
    <div class="content-picker">
      <table class="table table-responsive table-bordered table-condensed" style="table-layout: fixed;margin-bottom: 0">
        <colgroup>
          <col width="25">
          <col width="170">
          <col width="95">
          <col width="55">
          <col>
          <col width="55">
          <col width="110">
          <col width="110">
          <col width="75">
          <col width="110">
          <col width="55">
        </colgroup>
        <thead>
        <tr>
          <th>№</th>
          <th>Пациент, карта</th>
          <th>Цель посещения</th>
          <th>Первич. приём</th>
          <th>Код диагноза (МКБ 10), виды услуг, виды травм</th>
          <th>Впервые</th>
          <th>Результат обращения</th>
          <th>Исход</th>
          <th>Дисп. учёт</th>
          <th>Врач</th>
          <th></th>
        </tr>
        </thead>
      </table>
      <div style="align-self: stretch;flex: 0 0 calc(100% - 53px);overflow: auto">
        <table class="table table-responsive table-bordered table-condensed"
               style="table-layout: fixed;margin-bottom: 0">
          <colgroup>
            <col width="25">
            <col width="170">
            <col width="95">
            <col width="55">
            <col>
            <col width="55">
            <col width="110">
            <col width="110">
            <col width="75">
            <col width="110">
            <col width="55">
          </colgroup>
          <tbody>
          <tr v-for="row in data" :class="{invalid: row.invalid}">
            <td>{{row.n}}</td>
            <td>{{row.patinet}}<br/>Карта: {{row.card}}</td>
            <td>{{row.purpose}}</td>

            <td v-if="row.primary">да</td>
            <td v-else>нет</td>

            <td v-html="row.info"></td>

            <td v-if="row.first_time">да</td>
            <td v-else>нет</td>

            <td>{{row.result}}</td>
            <td>{{row.outcome}}</td>
            <td>{{row.disp}}</td>
            <td class="doc">{{row.doc}}<br/>{{row.department}}</td>

            <td class="control-buttons">
              <div class="flex-wrap" v-if="row.can_invalidate">
                <button class="btn btn-sm btn-blue-nb" v-if="row.invalid" @click="invalidate(row.pk, false)">Вернуть
                </button>
                <button class="btn btn-sm btn-blue-nb" v-else @click="invalidate(row.pk, true)">Отменить</button>
              </div>
            </td>
          </tr>
          <tr v-if="data.length === 0">
            <td class="text-center" colspan="11">За выбранную дату нет статталонов</td>
          </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
  import moment from 'moment'
  import DateField from './DateField.vue'
  import * as action_types from './store/action-types'
  import statistics_tickets_point from './api/statistics-tickets-point'

  export default {
    name: 'statistics-tickets-viewer',
    components: {
      DateField
    },
    data() {
      return {
        date: moment().format('DD.MM.YYYY'),
        data: []
      }
    },
    created() {
      let vm = this
      this.load()
      this.$root.$on('create-ticket', () => {
        if (vm.date === moment().format('DD.MM.YYYY')) {
          vm.load()
        }
      })
    },
    watch: {
      date() {
        this.load()
      }
    },
    methods: {
      print() {
        window.open(`/statistic/xls?type=statistics-tickets-print&users=${encodeURIComponent(JSON.stringify([this.$store.getters.user_data.doc_pk]))}&date-start=${this.date}&date-end=${this.date}`, '_blank')
      },
      load() {
        let vm = this
        vm.$store.dispatch(action_types.INC_LOADING).then()
        statistics_tickets_point.loadTickets(this.date).then(data => {
          vm.data = data.data
        }).finally(() => {
          vm.$store.dispatch(action_types.DEC_LOADING).then()
        })
      },
      invalidate(pk, invalid) {
        let vm = this
        vm.$store.dispatch(action_types.INC_LOADING).then()
        statistics_tickets_point.invalidateTicket(pk, invalid).then(data => {
          if (!data.ok) {
            errmessage(data.message)
          }
          vm.load()
        }).finally(() => {
          vm.$store.dispatch(action_types.DEC_LOADING).then()
        })
      }
    }
  }
</script>

<style scoped lang="scss">
  .top-picker {
    height: 34px;
    background-color: #AAB2BD;
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    display: flex;
    align-items: stretch;
    justify-content: center;
    align-content: stretch;
  }

  .content-picker {
    overflow: hidden;
    display: flex;
    flex-direction: column;
    position: absolute;
    top: 34px;
    bottom: 0;
    left: 0;
    right: 0;
    font-size: 10px;
  }

  .content-picker .btn-blue-nb {
    font-size: 10px !important;
  }

  .top-picker .form-control, .top-picker .btn {
    border-radius: 0;
    border: none;
  }

  .top-picker .form-control {
    border-bottom: 1px solid #AAB2BD;
  }

  .invalid td:not(:hover):not(.control-buttons) {
    text-decoration: line-through;
    color: #bcbcbc;
  }

  .control-buttons {
    padding: 0;
    position: relative;

    .flex-wrap {
      display: flex;
      position: absolute;
      top: 0;
      left: 0;
      bottom: 0;
      right: 0;
      align-items: stretch;
      justify-content: stretch;

      .btn {
        white-space: normal;
        text-overflow: ellipsis;
        border-radius: 0;
        align-self: stretch;
        width: 100%;
        padding: 2px;
      }
    }
  }

  .doc {
    font-size: 12px;
    word-break: break-word;
  }
</style>
