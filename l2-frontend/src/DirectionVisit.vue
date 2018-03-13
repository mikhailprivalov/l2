<template>
  <div>
    <div class="row">
      <div class="col-xs-12 col-sm-12 col-md-6">
        <div>
          <div class="panel panel-flt nbl" style="margin-bottom: 10px">
            <div class="panel-heading" style="padding-top: 0;padding-bottom: 0;height: 34px">
              <span style="margin-top: 7px;display: inline-block;">Направление</span>
            </div>

            <ul class="list-group">
              <li class="list-group-item">
                <div class="input-group">
                  <input type="text" class="form-control" v-model="direction" data-container="body"
                         data-toggle="popover" data-placement="bottom" data-content="" spellcheck="false" autofocus
                         placeholder="Введите номер направления" @keyup.enter="load" ref="field">
                  <span class="input-group-btn">
                        <button class="btn btn-blue-nb" @click="load" type="button">Загрузить</button>
                  </span>
                </div>
              </li>

              <li class="list-group-item" v-if="loaded_pk > 0">
                <table class="table table-bordered table-condensed dirtb"
                       style="margin-bottom: 0;background-color: #fff">
                  <tr>
                    <td>Номер</td>
                    <td>
                      <h3 style="margin: 2px;padding: 0;">{{loaded_pk}}
                        <small><a href="#" @click.prevent="print_direction">печать</a></small>
                      </h3>
                    </td>
                  </tr>
                  <tr>
                    <td>Дата назначения</td>
                    <td>{{direction_data.date}}</td>
                  </tr>
                  <tr>
                    <td>Пациент</td>
                    <td>{{direction_data.client}}</td>
                  </tr>
                  <tr>
                    <td>Карта</td>
                    <td>{{direction_data.card}}</td>
                  </tr>
                  <tr>
                    <td>Л/врач</td>
                    <td>{{direction_data.doc}}</td>
                  </tr>
                  <tr>
                    <td>Источник финансирования</td>
                    <td>{{direction_data.fin_source}}</td>
                  </tr>
                  <tr>
                    <td>Диагноз</td>
                    <td>{{direction_data.diagnos}}</td>
                  </tr>
                </table>
              </li>
              <li class="list-group-item" v-if="loaded_pk > 0">
                <h5>Услуги направления:</h5>
                <ol>
                  <li v-for="r in researches">{{r.title}}</li>
                </ol>
              </li>
              <li class="list-group-item" v-if="loaded_pk > 0">
                <div class="row">
                  <div class="col-xs-12 col-sm-12 col-md-6">
                    <button class="btn btn-blue-nb" @click="cancel">Отмена</button>
                  </div>
                  <div class="col-xs-12 col-sm-12 col-md-6 text-right">
                    <button class="btn btn-blue-nb" @click="make_visit" v-if="!visit_status">
                      Зарегистрировать посещение
                    </button>
                    <div class="float-right" v-else>
                      Посещение {{visit_date}}<br/>
                      {{direction_data.visit_who_mark}}
                    </div>
                  </div>
                </div>
              </li>
              <li v-else class="list-group-item text-center">
                направление не загружено
              </li>
            </ul>
          </div>
        </div>
      </div>
      <div class="col-xs-12 col-sm-12 col-md-6">
        <div class="panel panel-flt">
          <div class="panel-heading" style="padding-top: 0;padding-bottom: 0;padding-right: 0;height: 34px">
            <date-field style="width: 50%;display: inline-block;float: right;border-radius: 0 4px 0 0;margin: 0"
                        :val.sync="journal_date" :def="journal_date"/>
            <span style="margin-top: 7px;display: inline-block;">Журнал посещений</span></div>
          <div class="panel-body">
            <div v-if="journal_data.length === 0" class="text-center">
              нет данных
            </div>
            <table class="table table-bordered table-condensed dirtb visits"
                   style="margin-bottom: 0;background-color: #fff"
                   v-else>
              <thead>
              <tr>
                <th>Направление</th>
                <th>Дата и время</th>
                <th>Пациент</th>
              </tr>
              </thead>
              <tbody>
              <tr v-for="r in journal_data">
                <td>{{r.pk}}</td>
                <td>{{r.datetime}}</td>
                <td>{{r.client}}</td>
              </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  import DateField from './DateField.vue'
  import directionsPoint from './api/directions-point'
  import * as action_types from './store/action-types'
  import moment from 'moment'

  function TryParseInt(str, defaultValue) {
    let retValue = defaultValue
    if (str !== null) {
      if (str.length > 0) {
        if (!isNaN(str)) {
          retValue = parseInt(str)
        }
      }
    }
    return retValue
  }

  export default {
    name: 'direction-visit',
    components: {
      DateField
    },
    data() {
      return {
        loaded_pk: -1,
        direction: '',
        in_load: false,
        researches: [],
        visit_status: false,
        visit_date: '',
        direction_data: {},
        journal_date: moment().format('DD.MM.YYYY'),
        journal_data: []
      }
    },
    computed: {
      query_int() {
        return TryParseInt(this.direction, -1)
      }
    },
    watch: {
      journal_date() {
        this.load_journal()
      }
    },
    mounted() {
      this.load_journal()
    },
    methods: {
      cancel() {
        this.loaded_pk = -1
        this.researches = []
        this.visit_status = false
        this.visit_date = ''
        this.direction_data = {}
      },
      print_direction() {
        if (this.loaded_pk === -1)
          return
        this.$root.$emit('print:directions', [this.loaded_pk])
      },
      load_journal() {
        let vm = this
        vm.$store.dispatch(action_types.INC_LOADING).then()
        directionsPoint.visitJournal(this.journal_date).then(data => {
          vm.journal_data = data.data
        }).finally(() => {
          vm.$store.dispatch(action_types.DEC_LOADING).then()
        })
      },
      load() {
        if (this.query_int === -1) {
          this.clear()
          return
        }
        if (this.in_load)
          return
        let vm = this
        vm.$store.dispatch(action_types.INC_LOADING).then()
        vm.in_load = true
        vm.cancel()
        directionsPoint.getDirectionsServices(this.query_int).then(data => {
          if (data.ok) {
            vm.loaded_pk = data.loaded_pk
            vm.researches = data.researches
            vm.direction_data = data.direction_data
            vm.visit_status = data.visit_status
            vm.visit_date = data.visit_date
            vm.blur()
          } else {
            errmessage(data.message)
          }
        }).finally(() => {
          vm.$store.dispatch(action_types.DEC_LOADING).then()
          vm.in_load = false
          vm.direction = ''
        })
      },
      focus() {
        $(this.$refs.field).focus()
      },
      blur() {
        $(this.$refs.field).blur()
      },
      make_visit() {
        if (this.loaded_pk === -1 || this.in_load)
          return
        let vm = this
        vm.$store.dispatch(action_types.INC_LOADING).then()
        vm.in_load = true
        directionsPoint.getMarkDirectionVisit(this.loaded_pk).then(data => {
          if (data.ok) {
            vm.visit_status = data.visit_status
            vm.visit_date = data.visit_date
            vm.focus()
          } else {
            errmessage(data.message)
          }
        }).finally(() => {
          vm.$store.dispatch(action_types.DEC_LOADING).then()
          vm.in_load = false
          vm.load_journal()
        })
      }
    }
  }
</script>

<style scoped lang="scss">
  .dirtb td {
    vertical-align: middle;
    padding: 2px;
    border: 1px solid #ddd;
  }

  .dirtb tr td:last-child {
    text-align: left;
  }

  .dirtb:not(.visits) tr td:first-child {
    font-weight: 600;
    width: 170px;
  }

  .dirtb td:first-child {
    padding-left: 10px;
  }
</style>
