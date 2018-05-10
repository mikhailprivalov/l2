<template>
  <div style="align-self: stretch;overflow-y: auto;width: 100%;overflow-x: hidden;">
    <div class="input-group">
      <span class="input-group-addon">Цель посещения</span>
      <div class="input-group-btn" style="width: 100%;">
        <select-picker-b no-border-left="true" :options="visit_select" v-model="visit"/>
      </div>
    </div>
    <div class="form-group basic-textarea" style="margin-top: 5px;margin-bottom: 0">
      <label style="width: 100%;font-weight: normal;">Код диагноза (МКБ 10), виды услуг, виды травм:
        <textarea class="form-control" v-model="info" rows="2" style="resize: none;width: 100%"></textarea>
      </label>
    </div>
    <div class="row" style="margin-top: 5px;">
      <div class="col-xs-6">
        <label style="display: block;font-weight: normal;">Впервые: <input v-model="first_time" type="checkbox"/>
          {{first_time? 'да': 'нет'}}</label>
      </div>
      <div class="col-xs-6">
        <label style="display: block;font-weight: normal;">
          Первичный приём: <input v-model="primary_visit" type="checkbox"/> {{primary_visit? 'да': 'нет'}}</label>
      </div>
    </div>

    <div class="input-group flex-group">
      <span class="input-group-addon">Диспансерный учёт</span>
      <div class="input-group-btn">
        <select-picker-b no-border-left="true" :options="disp_select" v-model="disp"/>
      </div>
    </div>

    <div class="input-group flex-group" v-show="disp === '1' || disp === '2' || disp === '3'">
      <span class="input-group-addon">Диагноз учёта</span>
      <input type="text" class="form-control" v-model="disp_diagnos"/>
    </div>

    <div class="input-group flex-group" v-show="disp === '3'">
      <span class="input-group-addon">Причина снятия</span>
      <div class="input-group-btn">
        <select-picker-b no-border-left="true" :options="exclude_select" v-model="exclude"/>
      </div>
    </div>

    <div class="input-group flex-group">
      <span class="input-group-addon">Результат обращения</span>
      <div class="input-group-btn">
        <select-picker-b no-border-left="true" :options="result_select" v-model="result"/>
      </div>
    </div>

    <div class="input-group flex-group">
      <span class="input-group-addon">Исход</span>
      <div class="input-group-btn">
        <select-picker-b no-border-left="true" :options="outcome_select" v-model="outcome"/>
      </div>
    </div>

    <div class="input-group flex-group">
      <span class="input-group-addon">Дата талона</span>
      <date-field-2 class="text-date-left" v-model="date_ticket"/>
    </div>

    <button @click="create" class="btn btn-blue-nb" :disabled="card_pk === -1" style="margin-top: 10px;margin-bottom: 5px;width: 100%">
      Сохранить
    </button>
  </div>
</template>

<script>
  import * as action_types from './store/action-types'
  import statistics_tickets_point from './api/statistics-tickets-point'
  import SelectPickerB from './SelectPickerB'
  import DateField2 from './DateField2.vue'
  import moment from 'moment'

  export default {
    components: {SelectPickerB, DateField2},
    name: 'statistics-ticket-creator',
    props: {
      base: {
        type: Object,
        reqired: true
      },
      card_pk: {
        type: Number
      },
      ofname: {
        type: Number
      },
    },
    data() {
      return {
        types: {
          visit: [],
          result: [],
          outcome: [],
          exclude: [],
          disp: [
            {pk: 0, title: 'Не состоит'},
            {pk: 1, title: 'Состоит'},
            {pk: 2, title: 'Взят'},
            {pk: 3, title: 'Снят'},
          ]
        },
        visit: -1,
        result: -1,
        outcome: -1,
        exclude: -1,
        disp: -1,
        disp_diagnos: '',
        date_ticket: moment().format('DD.MM.YYYY'),
        info: '',
        first_time: false,
        primary_visit: true,
      }
    },
    created() {
      let vm = this
      vm.$store.dispatch(action_types.INC_LOADING).then()
      statistics_tickets_point.getTicketsTypes().then(data => {
        vm.types.visit = data.visit
        if (data.visit.length > 0)
          vm.visit = data.visit[0].pk
        vm.types.result = data.result
        if (data.result.length > 0)
          vm.result = data.result[0].pk
        vm.disp = vm.types.disp[0].pk

        vm.types.outcome = data.outcome
        if (data.outcome.length > 0)
          vm.outcome = data.outcome[0].pk
        vm.types.exclude = data.exclude
        if (data.exclude.length > 0)
          vm.exclude = data.exclude[0].pk
      }).finally(() => {
        vm.$store.dispatch(action_types.DEC_LOADING).then()
      })
    },
    computed: {
      exclude_val() {
        if (this.disp === '3') {
          return this.exclude
        }
        return -1
      },
      disp_diagnos_val() {
        if (this.disp === '1' || this.disp === '2' || this.disp === '3') {
          return this.disp_diagnos
        }
        return ""
      },
      outcome_select() {
        let r = []
        for (let row of this.types.outcome) {
          r.push({value: row.pk, label: row.title})
        }
        return r
      },
      exclude_select() {
        let r = []
        for (let row of this.types.exclude) {
          r.push({value: row.pk, label: row.title})
        }
        return r
      },
      visit_select() {
        let r = []
        for (let row of this.types.visit) {
          r.push({value: row.pk, label: row.title})
        }
        return r
      },
      disp_select() {
        let r = []
        for (let row of this.types.disp) {
          r.push({value: row.pk, label: row.title})
        }
        return r
      },
      result_select() {
        let r = []
        for (let row of this.types.result) {
          r.push({value: row.pk, label: row.title})
        }
        return r
      },
      selected_visit() {
        for (let row of this.types.visit) {
          if (row.pk === this.visit) {
            return row
          }
        }
        return {pk: -1, title: 'Не выбрано'}
      },
      selected_result() {
        for (let row of this.types.result) {
          if (row.pk === this.result) {
            return row
          }
        }
        return {pk: -1, title: 'Не выбрано'}
      },
      selected_disp() {
        for (let row of this.types.disp) {
          if (row.pk === this.disp) {
            return row
          }
        }
        return {pk: -1, title: 'Не выбрано'}
      },
    },
    methods: {
      create() {
        let vm = this
        vm.$store.dispatch(action_types.INC_LOADING).then()
        statistics_tickets_point.sendTicket(vm.card_pk,
          vm.visit,
          vm.info,
          vm.first_time,
          vm.primary_visit,
          vm.disp,
          vm.result,
          vm.outcome,
          vm.disp_diagnos_val,
          vm.exclude_val,
          vm.ofname,
          vm.date_ticket,
        )
          .then(() => {
            vm.clear()
            okmessage('Статталон добавлен')
            this.$root.$emit('create-ticket')
          }).finally(() => {
          vm.$store.dispatch(action_types.DEC_LOADING).then()
        })
      },
      clear() {
        this.info = ''
        this.disp_diagnos = ''
        this.date_ticket = moment().format('DD.MM.YYYY')
      }
    },
    mounted() {
      $('.dropdown:not(.dropdown-large)').on('show.bs.dropdown', function () {
        const $btnDropDown = $(this).find('.dropdown-toggle')
        const $listHolder = $(this).find('.dropdown-menu')

        $(this).css('position', 'static')
        $listHolder.css({
          'top': ($btnDropDown.offset().top + $btnDropDown.outerHeight(true)) + 'px',
          'left': $btnDropDown.offset().left + 'px'
        })
        $listHolder.data('open', true)
      }).on('hidden.bs.dropdown', function () {
        const $listHolder = $(this).find('.dropdown-menu')
        $listHolder.data('open', false)
      })
    }
  }
</script>

<style scoped lang="scss">
  .flex-group {
    display: flex;
    flex-direction: row;
    margin-bottom: 5px;

    .input-group-addon {
      display: flex;
      flex: 0 0 175px;
      align-self: stretch;
      align-items: center;
      text-align: left;
    }

    & > .input-group-btn {
      width: 100%;
    }
  }
</style>

<style lang="scss">
  .text-date-left {
    text-align: left !important;
    padding-left: 10px !important;
  }

  .dropdown {
    position: inherit;
  }
</style>
