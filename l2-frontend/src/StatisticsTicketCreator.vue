<template>
  <div style="align-self: stretch;display: flex;flex-direction: column">
    <div class="input-group" style="height: 34px">
      <span class="input-group-addon">Цель посещения</span>
      <div class="input-group-btn" style="width: 100%;">
        <button class="btn btn-blue-nb btn-ell dropdown-toggle" type="button" data-toggle="dropdown"
                style="width: 100%;text-align: left;">
          {{selected_visit.title}} <span class="caret"></span>
        </button>
        <ul class="dropdown-menu">
          <li v-for="row in types.visit" :value="row.pk" v-if="row.pk !== visit">
            <a href="#" @click.prevent="select_visit(row.pk)">{{row.title}}</a>
          </li>
        </ul>
      </div>
    </div>
    <div style="height: 100%;overflow-y: auto">
      <div class="form-group basic-textarea" style="margin-top: 5px;margin-bottom: 0">
        <label style="width: 100%;font-weight: normal;">Диагноз, виды услуг, виды травм:
          <textarea class="form-control" v-model="info" rows="2" style="resize: none;width: 100%"></textarea>
        </label>
      </div>
      <div class="row" style="margin-top: 5px;">
        <div class="col-xs-6">
          <label style="display: block;font-weight: normal;">Первый раз: <input v-model="first_time" type="checkbox"/>
            {{first_time? 'да': 'нет'}}</label>
        </div>
        <div class="col-xs-6">
          <label style="display: block;font-weight: normal;">Первичный приём: <input v-model="primary_visit"
                                                                                     type="checkbox"/> {{primary_visit?
            'да': 'нет'}}</label>
        </div>
      </div>

      <div class="input-group flex-group">
        <span class="input-group-addon">Диспансерный учёт</span>
        <div class="input-group-btn">
          <button class="btn btn-blue-nb btn-ell dropdown-toggle" type="button" data-toggle="dropdown"
                  style="width: 100%;text-align: left;">
            {{selected_disp.title}} <span class="caret"></span>
          </button>
          <ul class="dropdown-menu">
            <li v-for="row in types.disp" :value="row.pk" v-if="row.pk !== disp">
              <a href="#" @click.prevent="select_disp(row.pk)">{{row.title}}</a>
            </li>
          </ul>
        </div>
      </div>

      <div class="input-group flex-group">
        <span class="input-group-addon">Результат обращения</span>
        <div class="input-group-btn">
          <button class="btn btn-blue-nb btn-ell dropdown-toggle" type="button" data-toggle="dropdown"
                  style="width: 100%;text-align: left;">
            {{selected_result.title}} <span class="caret"></span>
          </button>
          <ul class="dropdown-menu">
            <li v-for="row in types.result" :value="row.pk" v-if="row.pk !== result">
              <a href="#" @click.prevent="select_result(row.pk)">{{row.title}}</a>
            </li>
          </ul>
        </div>
      </div>

      <button @click="create" class="btn btn-blue-nb" style="margin-top: 10px;width: 100%">Сохранить</button>
    </div>
  </div>
</template>

<script>
  import * as action_types from './store/action-types'
  import statistics_tickets_point from './api/statistics-tickets-point'

  export default {
    name: 'statistics-ticket-creator',
    props: {
      base: {
        type: Object,
        reqired: true
      },
      card_pk: {
        type: Number
      },
    },
    data() {
      return {
        types: {
          visit: [],
          result: [],
          disp: [
            {pk: 0, title: 'Не состоит'},
            {pk: 1, title: 'Состоит'},
            {pk: 2, title: 'Взят'},
            {pk: 3, title: 'Снят'},
          ]
        },
        visit: -1,
        result: -1,
        disp: 0,
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
      }).finally(() => {
        vm.$store.dispatch(action_types.DEC_LOADING).then()
      })
    },
    computed: {
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
      select_visit(pk) {
        this.visit = pk
      },
      select_result(pk) {
        this.result = pk
      },
      select_disp(pk) {
        this.visit = pk
      },
      create() {
        this.clear()
      },
      clear() {
        this.info = ''
      }
    },
    mounted() {
      $('.dropdown').on('show.bs.dropdown', function () {
        var $btnDropDown = $(this).find('.dropdown-toggle')
        var $listHolder = $(this).find('.dropdown-menu')

        $(this).css('position', 'static')
        $listHolder.css({
          'top': ($btnDropDown.offset().top + $btnDropDown.outerHeight(true)) + 'px',
          'left': $btnDropDown.offset().left + 'px'
        })
        $listHolder.data('open', true)
      })

      $('.dropdown').on('hidden.bs.dropdown', function () {
        var $listHolder = $(this).find('.dropdown-menu')
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
  .dropdown {
    position: inherit;
  }
</style>
