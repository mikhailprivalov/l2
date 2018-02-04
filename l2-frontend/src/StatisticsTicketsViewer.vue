<template>
  <div style="height: 100%;width: 100%;position: relative">
    <div class="top-picker">
      <date-field style="width: 94px;display: inline-block;align-self: stretch" :val.sync="date" :def="date"/>
      <button class="btn btn-blue-nb" @click="load" style="width: 42px;display: inline-block;align-self: stretch"><i
        class="glyphicon glyphicon-refresh"></i></button>
      <button class="btn btn-blue-nb" style="width: 94px;display: inline-block;align-self: stretch"><i
        class="glyphicon glyphicon-print"></i> Печать
      </button>
    </div>
    <div class="content-picker">
      <table class="table table-responsive table-bordered table-condensed" style="table-layout: fixed;margin-bottom: 0">
        <colgroup>
          <col width="35">
          <col width="300">
          <col width="170">
          <col width="90">
          <col width="100">
          <col>
          <col width="125">
          <col width="200">
        </colgroup>
        <thead>
        <tr>
          <th>№</th>
          <th>Пациент, карта</th>
          <th>Цель посещения</th>
          <th>Первый раз</th>
          <th>Первичный приём</th>
          <th>Диагнозы, виды услуг, травм</th>
          <th>Диспансерный учёт</th>
          <th>Результат обращения</th>
        </tr>
        </thead>
      </table>
      <div style="align-self: stretch;flex: 0 0 calc(100% - 53px);overflow: auto">
        <table class="table table-responsive table-bordered table-condensed" style="table-layout: fixed;margin-bottom: 0">
          <colgroup>
            <col width="35">
            <col width="300">
            <col width="170">
            <col width="90">
            <col width="100">
            <col>
            <col width="125">
            <col width="200">
          </colgroup>
          <tbody>
          <tr v-for="row in data">
            <td>{{row.n}}</td>
            <td>{{row.patinet}}<br/>Карта: {{row.card}}</td>
            <td>{{row.purpose}}</td>

            <td v-if="row.first_time">да</td>
            <td v-else>нет</td>

            <td v-if="row.primary">да</td>
            <td v-else>нет</td>

            <td v-html="row.info"></td>
            <td>{{row.disp}}</td>
            <td>{{row.result}}</td>
          </tr>
          <tr v-if="data.length === 0">
            <td class="text-center" colspan="8">За выбранную дату нет статталонов</td>
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
      load() {
        let vm = this
        vm.$store.dispatch(action_types.INC_LOADING).then()
        statistics_tickets_point.loadTickets(this.date).then(data => {
          vm.data = data.data
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
  }

  .top-picker .form-control, .top-picker .btn {
    border-radius: 0;
    border: none;
  }

  .top-picker .form-control {
    border-bottom: 1px solid #AAB2BD;
  }
</style>
