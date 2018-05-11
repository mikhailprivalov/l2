<template>
  <div style="height: 100%;width: 100%;position: relative">
    <div class="top-picker">
      <div class="input-group">
        <div class="input-group-btn">
          <button class="btn btn-blue-nb btn-ell dropdown-toggle nbr" type="button" data-toggle="dropdown"
                  style="width: 200px;text-align: left!important;"><span class="caret"></span> {{selected_base.title}}
          </button>
          <ul class="dropdown-menu">
            <li v-for="row in bases" :value="row.pk" v-if="!row.hide && row.pk !== selected_base.pk"><a href="#"
                                                                                                        @click.prevent="select_base(row.pk)">{{row.title}}</a>
            </li>
          </ul>
        </div>
        <input type="text" class="form-control bob" v-model="query" placeholder="Введите запрос" ref="q"
               maxlength="255" @keyup.enter="search">
        <span class="input-group-btn"><button style="margin-right: -2px" class="btn last btn-blue-nb nbr" type="button"
                                              :disabled="!query_valid || inLoading"
                                              @click="search">Поиск</button></span>
      </div>
    </div>
    <div class="content-picker scrolldown">
      <div style="padding-left: 5px;padding-right: 5px;">
        <table class="table table-bordered">
          <colgroup>
            <col width="124">
            <col>
            <col width="54">
            <col>
          </colgroup>
          <tbody>
          <tr>
            <td style="max-width: 124px;" class="table-header-row">ФИО:</td>
            <td style="max-width: 99%;" class="table-content-row">
              {{selected_card.family}} {{selected_card.name}} {{selected_card.twoname}}
            </td>
            <td style="max-width: 54px;" class="table-header-row">{{selected_card.is_rmis?'ID':'Карта'}}:</td>
            <td style="max-width: 99%;" class="table-content-row">{{selected_card.num}}</td>
          </tr>
          <tr>
            <td class="table-header-row">Дата рождения:</td>
            <td class="table-content-row">{{selected_card.birthday}}<span v-if="loaded"> ({{selected_card.age}})</span>
            </td>
            <td class="table-header-row">Пол:</td>
            <td class="table-content-row">{{selected_card.sex}}</td>
          </tr>
          <tr v-if="history_n === 'true'">
            <td class="table-header-row">
              <span class="hospital" style="display: block;line-height: 1.2;">Номер истории:</span>
            </td>
            <td class="table-content-row" colspan="3">
              <div style="height: 34px">
            <span class="hospital"><input type="text" class="form-control" maxlength="11" v-model="history_num"
                                          :disabled="!selected_base.history_number"/></span>
              </div>
            </td>
          </tr>
          <tr v-if="directive_from_need === 'true'">
            <td class="table-header-row" style="line-height: 1;">Работа от имени:</td>
            <td class="table-content-row select-td">
              <select-picker-b v-model="directive_department" :options="directive_departments_select"/>
            </td>
            <td class="table-content-row select-td" colspan="2">
              <select-picker-b v-model="directive_doc" :options="directive_docs_select"/>
            </td>
          </tr>
          </tbody>
        </table>
        <div v-if="phones.length > 0" class="hovershow">
          <div class="fastlinks hovershow1"><a href="#"><i class="glyphicon glyphicon-phone"></i> Позвонить</a></div>
          <div class="fastlinks hovershow2" style="margin-top: 1px">
            <a :href="'sip:' + p" v-for="p in phones" style="display: inline-block">
              <i class="glyphicon glyphicon-phone"></i> {{format_number(p)}}
            </a>
          </div>
        </div>
        <slot name="for_card" v-if="loaded" style="margin-top: 5px"/>
        <slot name="for_all" style="margin-top: 5px"/>
      </div>
    </div>
    <div class="bottom-picker" v-if="bottom_picker === 'true'">
      <slot name="for_card_bottom"/>
    </div>
    <modal ref="modal" v-show="showModal" @close="hide_modal" show-footer="true">
      <span slot="header">Найдено несколько карт</span>
      <div slot="body">
        <table class="table table-responsive table-bordered table-hover"
               style="background-color: #fff;max-width: 680px">
          <colgroup>
            <col width="95">
            <col width="155">
            <col>
            <col width="140">
          </colgroup>
          <thead>
          <tr>
            <th>Категория</th>
            <th>Карта</th>
            <th>ФИО, пол</th>
            <th>Дата рождения</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="(row, i) in founded_cards" class="cursor-pointer" @click="select_card(i)">
            <td class="text-center">{{row.type_title}}</td>
            <td>{{row.num}}</td>
            <td>{{row.family}} {{row.name}} {{row.twoname}}, {{row.sex}}</td>
            <td class="text-center">{{row.birthday}}</td>
          </tr>
          </tbody>
        </table>
      </div>
      <div slot="footer" class="text-center">
        <small>Показано не более 10 карт</small>
      </div>
    </modal>
  </div>
</template>

<script>
  import SelectPickerB from './SelectPickerB'
  import LinkSelector from './LinkSelector'
  import PatientCard from './ui-cards/PatientCard'
  import Modal from './ui-cards/Modal'
  import * as action_types from './store/action-types'
  import patients_point from './api/patients-point'

  export default {
    name: 'patient-picker',
    components: {LinkSelector, PatientCard, SelectPickerB, Modal},
    props: {
      directive_from_need: {
        default: 'false',
        type: String
      },
      search_results: {
        default: 'false',
        type: String
      },
      bottom_picker: {
        default: 'false',
        type: String
      },
      history_n: {
        default: 'true',
        type: String
      },
      value: {}
    },
    data() {
      return {
        base: -1,
        query: '',
        directive_department: '-1',
        directive_doc: '-1',
        ofname_to_set: '-1',
        ofname_to_set_dep: '-1',
        local_directive_departments: [],
        directive_departments_select: [],
        showModal: false,
        founded_cards: [],
        selected_card: {},
        loaded: false,
        history_num: '',
        search_after_loading: false
      }
    },
    created() {
      let vm = this

      vm.$store.dispatch(action_types.INC_LOADING).then()
      this.$store.dispatch(action_types.GET_DIRECTIVE_FROM).then(() => {
        vm.local_directive_departments = vm.$store.getters.directive_from
        vm.directive_departments_select = []
        for (let dep of vm.local_directive_departments) {
          vm.directive_departments_select.push({label: dep.title, value: dep.pk})
        }

        if (vm.local_directive_departments.length > 0 && vm.ofname_to_set === '-1') {
          for (let dep of vm.local_directive_departments) {
            if (dep.pk === vm.$store.getters.user_data.department.pk) {
              vm.directive_department = dep.pk + ''
              vm.check_base()
              return
            }
          }
          vm.directive_department = vm.local_directive_departments[0].pk.toString()
        }

        vm.check_base()
      }).finally(() => {
        vm.$store.dispatch(action_types.DEC_LOADING).then()
      })

      this.$store.watch(state => state.bases, (oldValue, newValue) => {
        this.check_base()
      })
      this.$root.$on('search', () => {
        vm.search()
      })
    },
    watch: {
      bases() {
        this.check_base()
      },
      directive_department() {
        this.update_ofname()
      },
      directive_doc() {
        this.emit_input()
      },
      is_operator() {
        this.emit_input()
      },
      history_num() {
        this.emit_input()
      },
      inLoading() {
        if (!this.inLoading  && (this.directive_department === '-1' || this.directive_doc === '-1')) {
          this.update_ofname()
        }
        if (!this.inLoading && this.search_after_loading) {
          this.search()
        }
      }
    },
    computed: {
      bases() {
        return this.$store.getters.bases
      },
      selected_base() {
        for (let b of this.bases) {
          if (b.pk === this.base) {
            return b
          }
        }
        return {title: 'Не выбрана база', pk: -1, hide: false, history_number: false, fin_sources: []}
      },
      normalized_query() {
        return this.query.trim()
      },
      query_valid() {
        return this.normalized_query.length > 0
      },
      is_operator() {
        if ('groups' in this.$store.getters.user_data) {
          for (let g of this.$store.getters.user_data.groups) {
            if (g === 'Оператор лечащего врача') {
              return true
            }
          }
        }
        return false
      },
      directive_from_departments() {
        let r = {}
        for (let dep of this.local_directive_departments) {
          r[dep.pk] = dep
        }
        return r
      },
      directive_docs_select() {
        let o = []
        if (this.directive_department in this.directive_from_departments) {
          for (let d of this.directive_from_departments[this.directive_department].docs) {
            o.push({label: d.fio, value: d.pk})
          }
        }
        return o
      },
      inLoading() {
        return this.$store.getters.inLoading
      },
      phones() {
        if ('phones' in this.selected_card) {
          return this.selected_card.phones
        }
        return []
      }
    },
    methods: {
      format_number(a) {
        if (a.length === 6) {
          return `${a.slice(0, 2)}-${a.slice(2, 4)}-${a.slice(4, 6)}`
        } else if (a.length === 11) {
          return `${a.slice(0, 1)}-${a.slice(1, 4)}-${a.slice(4, 6)}-${a.slice(6, 8)}-${a.slice(8, 10)}-${a.slice(10, 11)}`
        }
        return a
      },
      hide_modal() {
        this.showModal = false
        this.$refs.modal.$el.style.display = 'none'
      },
      update_ofname() {
        if (this.ofname_to_set === '-2' || this.inLoading)
          return
        if (this.ofname_to_set !== '-1') {
          if (this.ofname_to_set_dep !== '-1') {
            this.directive_department = this.ofname_to_set_dep
            this.directive_doc = this.ofname_to_set
            this.$root.$emit('resync')
            this.emit_input()
            this.ofname_to_set = '-2'
            return
          }
          let dps = Object.keys(this.directive_from_departments)
          if (dps.length > 0 && !this.inLoading) {
            let onts = this.ofname_to_set
            this.ofname_to_set = '-1'
            for (let d of dps) {
              let users = this.directive_from_departments[d].docs
              for (let u of users) {
                if (u.pk.toString() === onts) {
                  this.directive_department = d.toString()
                  this.directive_doc = onts
                  this.emit_input()
                  this.ofname_to_set = '-2'
                  return
                }
              }
            }
          }
          return
        }
        let dpk = -1
        if (this.directive_department !== '-1') {
          for (let d of this.directive_docs_select) {
            if (d.value === this.$store.getters.user_data.doc_pk) {
              dpk = d.value
              break
            }
          }
          if (dpk === -1 && this.directive_docs_select.length > 0) {
            dpk = this.directive_docs_select[0].value
          }
        }
        this.directive_doc = dpk.toString()
      },
      select_base(pk) {
        this.base = pk
        this.emit_input()
        this.search()
      },
      select_card(index) {
        this.hide_modal()
        this.selected_card = this.founded_cards[index]
        this.emit_input()
        this.loaded = true
        this.$root.$emit('patient-picker:select_card')
      },
      check_base() {
        if (this.base === -1 && this.bases.length > 0) {
          let params = new URLSearchParams(window.location.search)
          let rmis_uid = params.get('rmis_uid')
          let base_pk = params.get('base_pk')
          let card_pk = params.get('card_pk')
          let ofname = params.get('ofname')
          let ofname_dep = params.get('ofname_dep')
          if (rmis_uid) {
            window.history.pushState('', '', window.location.href.split('?')[0])
            for (let row of this.bases) {
              if (row.code === 'Р') {
                this.base = row.pk
                this.query = rmis_uid
                this.search_after_loading = true
                break
              }
            }
            if (this.base === -1) {
              this.base = this.bases[0].pk
            }
          } else if (base_pk) {
            window.history.pushState('', '', window.location.href.split('?')[0])
            if (ofname) {
              this.ofname_to_set = ofname
            }
            if (ofname_dep) {
              this.ofname_to_set_dep = ofname_dep
            }
            for (let row of this.bases) {
              if (row.pk === parseInt(base_pk)) {
                this.base = row.pk
                break
              }
            }
            if (this.base === -1) {
              this.base = this.bases[0].pk
            }
            if (card_pk) {
              this.query = `card_pk:${card_pk}`
              this.search_after_loading = true
            }
          }
          else {
            this.base = this.bases[0].pk
          }
          $(this.$refs.q).focus()
          this.emit_input()
        }
      },
      emit_input() {
        let pk = -1
        if ('pk' in this.selected_card)
          pk = this.selected_card.pk
        let individual_pk = -1
        if ('individual_pk' in this.selected_card)
          individual_pk = this.selected_card.individual_pk
        this.$emit('input', {
          pk: pk,
          individual_pk: individual_pk,
          base: this.selected_base,
          ofname_dep: parseInt(this.directive_department),
          ofname: parseInt(this.directive_doc),
          operator: this.is_operator,
          history_num: this.history_num,
          is_rmis: this.selected_card.is_rmis,
          family: this.selected_card.family,
          name: this.selected_card.name,
          twoname: this.selected_card.twoname,
          birthday: this.selected_card.birthday,
          age: this.selected_card.age,
          main_diagnosis: this.selected_card.main_diagnosis,
        })
        if(pk !== -1) {
          $("#fndsrc").focus()
        }
      },
      clear() {
        this.loaded = false
        this.selected_card = {}
        this.history_num = ''
        this.founded_cards = []
        if (this.query.includes('card_pk:')) {
          this.query = ''
        }
        this.emit_input()
      },
      search() {
        this.search_after_loading = false
        if (!this.query_valid || this.inLoading)
          return
        this.check_base()
        $('input').each(function () {
          $(this).trigger('blur')
        })
        let vm = this
        vm.$store.dispatch(action_types.ENABLE_LOADING, {loadingLabel: 'Поиск карты...'}).then()
        patients_point.searchCard(this.base, this.query).then((result) => {
          vm.clear()
          if (result.results) {
            vm.founded_cards = result.results
            if (vm.founded_cards.length > 1) {
              vm.$refs.modal.$el.style.display = 'flex'
              vm.showModal = true
            } else if (vm.founded_cards.length === 1) {
              vm.select_card(0)
            } else {
              errmessage('Не найдено', 'Карт по такому запросу не найдено')
            }
          } else {
            errmessage('Ошибка на сервере')
          }
        }).catch((error) => {
          errmessage('Ошибка на сервере', error.message)
        }).finally(() => {
          vm.$store.dispatch(action_types.DISABLE_LOADING).then()
        })
      }
    }
  }
</script>

<style scoped lang="scss">
  table {
    table-layout: fixed;
    padding: 0;
    margin: 5px 0 0;
  }

  td:not(.select-td) {
    padding: 2px !important;
  }

  .table-header-row {
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    vertical-align: middle;
  }

  .table-content-row {
    overflow: hidden;
    text-overflow: ellipsis;
    vertical-align: middle;
  }

  .cursor-pointer {
    cursor: pointer;
  }

  .content-picker {
    position: absolute;
    top: 34px;
    left: 0;
    right: 0;
    bottom: 34px;
    overflow-y: auto;
    overflow-x: hidden;
  }

  .top-picker, .bottom-picker {
    height: 34px;
    background-color: #AAB2BD;
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    white-space: nowrap;
  }

  .bottom-picker {
    bottom: 0;
  }

  .top-picker {
    top: 0;
  }

  .bottom-inner {
    display: flex;
    flex-wrap: wrap;
    flex-direction: row;
    justify-content: flex-end;
    align-items: stretch;
    position: absolute;
    left: 0;
    top: 0;
    right: 0;
    height: 34px;
    align-content: stretch;
    overflow: hidden;

    a {
      align-self: stretch;
      display: flex;
      align-items: center;
      padding: 1px 2px 1px;
      text-decoration: none;
      transition: .15s linear all;
      cursor: pointer;
      flex: 1;
      margin: 0;
      font-size: 12px;
      min-width: 0;
      max-width: 150px;
      background-color: #AAB2BD;
      color: #fff;
      text-align: right;
      justify-content: center;
      span {
        display: block;
        text-overflow: ellipsis;
        overflow: hidden;
        word-break: keep-all;
        max-height: 2.2em;
        line-height: 1.1em;
      }

      &:hover {
        background-color: #434a54;
      }
    }
  }
</style>

<style lang="scss">
  .select-td {
    padding: 0 !important;

    .bootstrap-select {
      height: 38px;
      display: flex !important;
      button {
        border: none !important;
        border-radius: 0 !important;
        .filter-option {
          text-overflow: ellipsis;
        }
      }
    }
  }

  .hovershow {
    position: relative;

    a {
      font-size: 12px;
    }

    .hovershow1 {
      top: 1px;
      position: absolute;

      a {
        color: grey;
        display: inline-block;
      }
      color: grey;
      white-space: nowrap;
      text-overflow: ellipsis;
      overflow: hidden;
    }
    .hovershow2 {
      opacity: 0;
    }

    &:hover {
      .hovershow1 {
        display: none;
      }
      .hovershow2 {
        opacity: 1;
        transition: .5s ease-in opacity;
      }
    }
  }

  .nbr {
    border-radius: 0;
  }

  .bob {
    border-left: none !important;
    border-top: none !important;
    border-right: none !important;
  }
</style>
