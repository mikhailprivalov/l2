<template>
  <div ref="root" class="results-root">
    <div class="results-sidebar">
      <div class="sidebar-top">
        <input type="text" class="form-control" v-model="pk" @keyup.enter="load" autofocus
               placeholder="Номер направления"/>
        <button class="btn btn-blue-nb" @click="load">Загрузить</button>
      </div>
      <div class="sidebar-bottom-top">Результаты за
        <date-field style="width: 94px;display: inline-block;height: 34px" :val.sync="date" :def="date"/>
      </div>
      <div style="overflow-y: auto;overflow-x:hidden;">
        <div class="direction" v-for="direction in directions_history">
          <div>
            Направление №<a href="#" @click.prevent="print_direction(direction.pk)">{{direction.pk}}</a> от
            {{direction.date}}
          </div>
          <hr/>
          <div>
            {{direction.patient}}
          </div>
          <div>
            Карта: {{direction.card}}
          </div>
          <div v-for="i in direction.iss" class="research-row">
            <div class="row">
              <div class="col-xs-8">
                {{i.title}}
              </div>
              <div class="col-xs-4 text-right">
                <span class="status status-none" v-if="!i.confirmed && !i.saved">не сохр.</span>
                <span class="status status-saved" v-if="!i.confirmed && i.saved">сохр.</span>
                <span class="status status-confirmed" v-if="i.confirmed && i.saved">подтв.</span>
              </div>
            </div>
          </div>
          <hr/>
          <div class="row">
            <div class="col-xs-5"><a href="#" @click.prevent="load_pk(direction.pk)">Просмотр</a></div>
            <div class="col-xs-7 text-right">
              <a href="#" @click.prevent="print_results(direction.pk)" v-if="direction.all_confirmed">Печать
                результатов</a>
            </div>
          </div>
        </div>
        <div class="text-center" style="margin: 5px" v-if="directions_history.length === 0">
          Нет данных
        </div>
      </div>
    </div>
    <div class="results-content" v-if="data.ok">
      <div class="results-top">
        <div class="row">
          <div class="col-xs-6">
            <div>Направление №<a href="#" @click.prevent="print_direction(data.direction.pk)">{{data.direction.pk}}</a>
              от
              {{data.direction.date}}
            </div>
            <div>{{data.patient.fio_age}}</div>
            <div class="text-ell" :title="data.direction.diagnos">Диагноз: {{data.direction.diagnos}}</div>
          </div>
          <div class="col-xs-5">
            <div>Источник финансирования: {{data.direction.fin_source}}</div>
            <div>Карта: {{data.patient.card}}</div>
            <div class="text-ell" :title="data.patient.doc">Лечащий врач: {{data.patient.doc}}</div>
          </div>
          <div class="col-xs-1">
            <button type="button" class="close" @click="clear()">
              <span>&times;</span>
            </button>
          </div>
        </div>
      </div>
      <div class="results-editor">
        <div v-for="row in data.researches">
          <div class="research-title">{{row.research.title}}</div>
          <div class="group" v-for="group in row.research.groups">
            <div class="group-title" v-if="group.title !== ''">{{group.title}}</div>
            <div class="fields">
              <div class="field" v-for="field in group.fields" :class="{disabled: row.confirmed}"
                   @mouseenter="enter_field" @mouseleave="leave_field">
                <div v-if="field.title !== ''" class="field-title">
                  {{field.title}}
                </div>
                <longpress v-if="!row.confirmed" class="btn btn-default btn-field" :on-confirm="clear_val" :confirm-time="0" :duration="400" :value="field" pressing-text="×" action-text="×">×</longpress>
                <div v-if="field.values_to_input.length > 0 && !row.confirmed" class="field-inputs">
                  <div class="input-values-wrap">
                    <div class="input-values">
                      <div class="inner-wrap">
                        <div class="input-value" v-for="val in field.values_to_input" @click="append_value(field, val)">
                          {{val}}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="field-value">
                  <textarea v-model="field.value" :rows="field.lines" class="form-control"
                            v-if="field.lines > 1" :readonly="row.confirmed"></textarea>
                  <input v-model="field.value" class="form-control" :readonly="row.confirmed" v-else/>
                </div>
              </div>
            </div>
          </div>
          <div class="control-row">
            <div class="res-title">{{row.research.title}}:</div>
            <div class="status status-none" v-if="!row.confirmed && !row.saved">Не сохранено</div>
            <div class="status status-saved" v-if="!row.confirmed && row.saved">Сохранено</div>
            <div class="status status-confirmed" v-if="row.confirmed && row.saved">Подтверждено</div>
            <button class="btn btn-blue-nb" @click="save(row)" v-if="!row.confirmed">Сохранить</button>
            <button class="btn btn-blue-nb" @click="confirm(row)" v-if="row.saved && !row.confirmed" :disabled="changed">Подтвердить
            </button>
            <button class="btn btn-blue-nb" @click="save_and_confirm(row)" v-if="!row.confirmed">Сохранить и
              подтвердить
            </button>
            <button class="btn btn-blue-nb" @click="reset_confirm(row)" v-if="row.confirmed && row.allow_reset_confirm">
              Сброс подтверждения
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="results-content" v-else></div>
  </div>
</template>

<script>
  import moment from 'moment'
  import * as action_types from './store/action-types'
  import directions_point from './api/directions-point'
  import DateField from './DateField.vue'
  import Longpress from 'vue-longpress'

  export default {
    name: 'results-paraclinic',
    components: {DateField, Longpress},
    data() {
      return {
        pk: '',
        data: {ok: false},
        date: moment().format('DD.MM.YYYY'),
        directions_history: [],
        prev_scroll: 0,
        changed: false,
        inserted: false
      }
    },
    watch: {
      date() {
        this.load_history()
      },
      data: {
        handler() {
          if(this.data.ok) {
            if (this.inserted) {
              this.changed = true
            } else {
              this.inserted = true
            }
          } else {
            this.changed = false
            this.inserted = false
          }
        },
        deep: true
      }
    },
    mounted() {
      let vm = this
      $(window).on('beforeunload', function () {
        if (vm.has_changed)
          return 'Возможно имеются несохраненные изменения! Вы уверены, что хотите покинуть страницу?'
      })
      vm.load_history()
    },
    methods: {
      enter_field($e) {
        this.prev_scroll = $('.results-editor').scrollTop()
        let $elem = $($e.target)
        $elem.addClass('open-field')
      },
      leave_field($e) {
        let oh = $('.results-editor > div')[0].offsetHeight
        let sh = $('.results-editor > div')[0].scrollHeight
        if (sh > oh)
          $('.results-editor').scrollTo(this.prev_scroll)
        let $elem = $($e.target)
        $elem.removeClass('open-field')
      },
      load_history() {
        let vm = this
        vm.directions_history = []
        vm.$store.dispatch(action_types.INC_LOADING).then()
        directions_point.paraclinicResultUserHistory(vm.date).then(data => {
          vm.directions_history = data.directions
        }).finally(() => {
          vm.$store.dispatch(action_types.DEC_LOADING).then()
        })
      },
      reload_if_need() {
        if (this.date === moment().format('DD.MM.YYYY')) {
          this.load_history()
        }
      },
      load_pk(pk) {
        this.pk = '' + pk
        this.load()
      },
      load() {
        if (this.has_changed && !confirm('Возможно имеются несохраненные изменения! Вы действительно хотите закрыть текущий протокол?')) {
          return
        }
        let vm = this
        vm.clear(true)
        vm.$store.dispatch(action_types.INC_LOADING).then()
        directions_point.getParaclinicForm(vm.pk_c).then(data => {
          if (data.ok) {
            vm.pk = ''
            vm.data = data
            vm.changed = false
          }
          else {
            errmessage(data.message)
          }
        }).finally(() => {
          vm.$store.dispatch(action_types.DEC_LOADING).then()
        })
      },
      save(iss) {
        let vm = this
        vm.inserted = false
        vm.$store.dispatch(action_types.INC_LOADING).then()
        directions_point.paraclinicResultSave(iss, false).then(data => {
          if (data.ok) {
            okmessage('Сохранено')
            iss.saved = true
            vm.reload_if_need()
            vm.changed = false
          }
          else {
            errmessage(data.message)
          }
        }).finally(() => {
          vm.$store.dispatch(action_types.DEC_LOADING).then()
          vm.inserted = true
        })
      },
      save_and_confirm(iss) {
        let vm = this
        vm.inserted = false
        vm.$store.dispatch(action_types.INC_LOADING).then()
        directions_point.paraclinicResultSave(iss, true).then(data => {
          if (data.ok) {
            okmessage('Сохранено')
            okmessage('Подтверждено')
            iss.saved = true
            iss.allow_reset_confirm = true
            iss.confirmed = true
            vm.reload_if_need()
            vm.changed = false
          }
          else {
            errmessage(data.message)
          }
        }).finally(() => {
          vm.$store.dispatch(action_types.DEC_LOADING).then()
          vm.inserted = true
        })
      },
      confirm(iss) {
        let vm = this
        vm.inserted = false
        vm.$store.dispatch(action_types.INC_LOADING).then()
        directions_point.paraclinicResultConfirm(iss.pk).then(data => {
          if (data.ok) {
            okmessage('Подтверждено')
            iss.confirmed = true
            iss.allow_reset_confirm = true
            vm.reload_if_need()
            vm.changed = false
          }
          else {
            errmessage(data.message)
          }
        }).finally(() => {
          vm.$store.dispatch(action_types.DEC_LOADING).then()
          vm.inserted = true
        })
      },
      reset_confirm(iss) {
        let vm = this
        let msg = `Сбросить подтверждение исследования ${iss.research.title}?`
        let doreset = confirm(msg)
        if (doreset === false || doreset === null) {
          return
        }
        vm.inserted = false
        vm.$store.dispatch(action_types.INC_LOADING).then()
        directions_point.paraclinicResultConfirmReset(iss.pk).then(data => {
          if (data.ok) {
            okmessage('Подтверждение сброшено')
            iss.confirmed = false
            vm.reload_if_need()
            vm.changed = false
          }
          else {
            errmessage(data.message)
          }
        }).finally(() => {
          vm.$store.dispatch(action_types.DEC_LOADING).then()
          vm.inserted = true
        })
      },
      clear(ignore) {
        ignore = ignore || false
        if (!ignore && this.has_changed && !confirm('Возможно имеются несохраненные изменения! Вы действительно хотите закрыть текущий протокол?')) {
          return
        }

        this.inserted = false
        this.changed = false
        this.data = {ok: false}
      },
      print_direction(pk) {
        this.$root.$emit('print:directions', [pk])
      },
      print_results(pk) {
        this.$root.$emit('print:results', [pk])
      },
      clear_val(field) {
        field.value = ''
      },
      append_value(field, value) {
        let add_val = value
        if(add_val !== ',' && add_val !== '.') {
          if (field.value.length > 0 && field.value[field.value.length - 1] !== ' ' && field.value[field.value.length - 1] !== '\n') {
            if (field.value[field.value.length - 1] === '.') {
              add_val = add_val.replace(/./, add_val.charAt(0).toUpperCase())
            }
            add_val = ' ' + add_val
          } else if ((field.value.length === 0 || (field.value.length >= 2 && field.value[field.value.length - 2] === '.' && field.value[field.value.length - 1] === '\n')) && field.title === '') {
            add_val = add_val.replace(/./, add_val.charAt(0).toUpperCase())
          }
        }
        field.value += add_val
      }
    },
    computed: {
      pk_c() {
        let lpk = this.pk.trim()
        if (lpk === '')
          return -1
        try {
          return parseInt(lpk)
        } catch (e) {
        }
        return -1
      },
      has_changed() {
        return this.changed && this.data && this.data.ok && this.inserted
      }
    }
  }
</script>

<style scoped lang="scss">
  .results-root {
    display: flex;
    align-items: stretch;
    flex-direction: row;
    flex-wrap: nowrap;
    align-content: stretch;
    & > div {
      align-self: stretch;
    }
  }

  .results-sidebar {
    width: 294px;
    border-right: 1px solid #b1b1b1;
    display: flex;
    flex-direction: column;
  }

  .results-content {
    display: flex;
    flex-direction: column;
    width: calc(100% - 294px);
  }

  .results-top {
    border-bottom: 1px solid #b1b1b1;
    height: 68px;
    padding: 5px;
  }

  .results-top > div {
    font-family: "Courier New", Courier, monospace !important;
  }

  .sidebar-top {
    flex: 0 0 34px;
    display: flex;
    flex-direction: row;
    align-items: stretch;
    flex-wrap: nowrap;
    justify-content: stretch;
    input, button {
      align-self: stretch;
      border: none;
      border-radius: 0;
    }
    input {
      border-bottom: 1px solid #b1b1b1;
    }

    button {
      flex: 0 0 68px
    }
  }

  .research-title {
    position: sticky;
    top: 0;
    background-color: #ddd;
    text-align: center;
    padding: 5px;
    font-weight: bold;
    z-index: 2;
  }

  .results-editor {
    height: calc(100% - 68px);
    overflow-y: auto;
    overflow-x: hidden;
  }

  .group {
    margin: 5px;
    border: 1px solid #c1c1c1;
  }

  .group-title {
    background-color: #eaeaea;
    padding: 5px;
    font-weight: bold;
    position: sticky;
    top: 30px;
    z-index: 1;
  }

  .sidebar-bottom-top {
    background-color: #eaeaea;
    padding-left: 5px;
    flex: 0 0 34px;
    .form-control {
      border-radius: 0;
      border-top: none;
      border-left: none;
      border-right: none;
    }
  }

  .fields {
    padding: 5px 5px 5px 10px;
  }

  .field {
    display: flex;
    flex-direction: row;
    align-items: stretch;
    justify-content: stretch;
    & > div {
      align-self: stretch;
    }
    margin-top: 5px;
    margin-bottom: 5px;
    background-color: #fafafa;

    overflow: visible;

    &.open-field:not(.disabled) {
      background-color: #efefef;
      .input-values {
        overflow: visible !important;
      }
      .input-values-wrap {
        z-index: 3;
      }
      .inner-wrap {
        background-color: #cfd9db;
        box-shadow: 0 3px 3px rgba(0, 0, 0, .4);
      }
      .form-control {
        border-color: #00a1cb;
      }
    }
  }

  .field-title {
    flex: 1 0 150px;
    padding-left: 5px;
    padding-top: 5px;
  }

  .field-value {
    flex-basis: 100%;
    textarea {
      resize: none;
    }
    .form-control {
      width: 100%;
      border-radius: 0;
    }
  }

  .field-inputs {
    flex: 1 0 250px;
    position: relative;
    overflow: visible;
  }

  .input-values-wrap {
    position: absolute;
    left: 0;
    top: 0;
    right: 0;
    bottom: 0;
    overflow: visible;
  }

  .input-values {
    width: 250px;
    height: 100%;
    overflow: hidden;
  }

  .inner-wrap {
    white-space: normal;
    padding: 3px;
    background-color: #ECF0F1;
  }

  .input-value {
    padding: 3px;
    background-color: #ECF0F1;
    border-radius: 2px;
    border: 1px solid #95A5A6;
    color: #656D78;
    display: inline-block;
    margin-bottom: 4px;
    margin-right: 4px;
    cursor: pointer;
    min-width: 20px;
    text-align: center;
    word-break: break-word;
  }

  .input-value:hover {
    background-color: #049372;
    border: 1px solid #03614b;
    color: #ffffff;
  }

  .control-row {
    height: 34px;
    background-color: #f3f3f3;
    display: flex;
    flex-direction: row;
    button {
      align-self: stretch;
      border-radius: 0;
    }
    div {
      align-self: stretch
    }
  }

  .res-title {
    padding: 5px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .status {
    padding: 5px;
    font-weight: bold;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .status-none {
    color: #CF3A24
  }

  .status-saved {
    color: #F4D03F
  }

  .status-confirmed {
    color: #049372
  }

  .direction {
    padding: 5px;
    margin: 5px;
    border-radius: 5px;
    border: 1px solid rgba(0, 0, 0, 0.14);
    background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);

    hr {
      margin: 3px;
    }
  }

  .text-ell {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .research-row {
    margin-top: 3px;
    margin-bottom: 3px;
    padding: 3px;
    background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);
  }

  .btn-field, .btn-field:focus {
    align-self: stretch;
    border-radius: 0;
    border-left: 0;
    border-right: 0;
    background: rgba(0, 0, 0, .06);
    border: none;
    margin-right: 5px;
    color: #000;
  }

  .btn-field:hover {
    background: rgba(0, 0, 0, .2);
    color: #fff;
  }
</style>
