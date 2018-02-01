<template>
  <div>
    <div class="input-group">
      <div class="input-group-btn">
        <button class="btn btn-blue-nb btn-ell dropdown-toggle" type="button" data-toggle="dropdown"
                style="width: 200px;text-align: left!important;"><span class="caret"></span> {{selected_base.title}}
        </button>
        <ul class="dropdown-menu">
          <li v-for="row in bases" :value="row.pk" v-if="!row.hide && row.pk !== selected_base.pk"><a href="#"
                                                                                                      @click.prevent="select_base(row.pk)">{{row.title}}</a>
          </li>
        </ul>
      </div>
      <input type="text" class="form-control" v-model="query" placeholder="Введите запрос" autofocus
             :maxlength="query_limit" @keyup.enter="search">
      <span class="input-group-btn"><button style="margin-right: -2px" class="btn last btn-blue-nb" type="button"
                                            :disabled="!query_valid || inLoading" @click="search">Поиск</button></span>
    </div>

    <table class="table table-bordered">
      <colgroup>
        <col width="127">
        <col>
        <col width="127">
        <col>
      </colgroup>
      <tbody>
      <tr>
        <td style="max-width: 127px;" class="table-header-row">ФИО:</td>
        <td style="max-width: 99%;" class="table-content-row">{{selected_card.family}} {{selected_card.name}}
          {{selected_card.twoname}}
        </td>
        <td style="max-width: 127px;" class="table-header-row">Номер карты:</td>
        <td style="max-width: 99%;" class="table-content-row">{{selected_card.num}}</td>
      </tr>
      <tr>
        <td class="table-header-row">Дата рождения:</td>
        <td class="table-content-row">{{selected_card.birthday}}</td>
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
      <tr v-if="is_operator && directive_from_need === 'true'">
        <td class="table-header-row">Направлять от:</td>
        <td class="table-content-row select-td">
          <select-picker-b v-model="directive_department" :options="directive_departments_select"></select-picker-b>
        </td>
        <td class="table-content-row select-td" colspan="2">
          <select-picker-b v-model="directive_doc" :options="directive_docs_select"></select-picker-b>
        </td>
      </tr>
      </tbody>
    </table>
    <!--<div v-if="search_results === 'true' && loaded" style="text-align: right;margin-top: 5px;"><a
      class="btn btn-blue-nb btn-sm" href="#">Поиск результатов по видам исследований</a></div>-->
    <modal ref="modal" v-show="showModal" @close="hide_modal" show-footer="true">
      <span slot="header">Найдено несколько карт</span>
      <div slot="body">
        <table class="table table-responsive table-bordered table-hover"
               style="background-color: #fff;max-width: 650px">
          <colgroup>
            <col width="95">
            <col width="150">
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
        search_type: 'auto',
        search_types: [
          {key: 'auto', title: 'авто', about: 'Автоматическое определение типа запроса', pattern: '.+'},
          {
            key: 'full_fio',
            title: 'полное фио и дата рождения',
            about: 'Введите ФИО и дату раждения. Возможен ввод частями, например: Иванов Иван Иванович 01.01.1990 или Петров Пётр',
            pattern: '^([А-яЕё]+)( ([А-яЕё]+)( ([А-яЕё]*)( ([0-9]{2}\\.[0-9]{2}\\.[0-9]{4}))?)?)?$'
          },
          {
            key: 'short_fio',
            title: 'краткое фио и дата рождения',
            about: 'Введите инициалы и дату рождения, например: иии01011990',
            pattern: '^[а-яА-ЯёЁ]{3}[0-9]{8}$',
            limit: 11
          },
          {
            key: 'polis',
            title: 'номер полиса ОМС',
            about: 'Введите серию (при необходимости через пробел) и номер полиса, например: 1234АБВ 123456789 или 3876543213213413',
            pattern: '.+'
          },
        ],
        directive_department: '-1',
        directive_doc: '-1',
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

        if (vm.local_directive_departments.length > 0) {
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

      if (this.bases.length === 0) {
        this.$store.watch(state => state.bases, (oldValue, newValue) => {
          this.check_base()
        })
      }
      this.$root.$on('search', () => {
        vm.search()
      })
    },
    watch: {
      bases() {
        this.check_base()
      },
      directive_department() {
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
      selected_type() {
        for (let b of this.search_types) {
          if (b.key === this.search_type) {
            return b
          }
        }
        return {key: '', title: 'не выбрано', about: ''}
      },
      query_limit() {
        if (this.selected_type.limit !== undefined) {
          return this.selected_type.limit
        }
        return 255
      },
      selected_pattern() {
        if (this.selected_type.pattern !== undefined) {
          return this.selected_type.pattern
        }
        return '.*'
      },
      normalized_query() {
        return this.query.trim()
      },
      query_valid() {
        let re = new RegExp(this.selected_pattern)
        return this.normalized_query.match(re)
      },
      active_type() {
        for (let b of this.search_types) {
          let re = new RegExp(b.pattern)
          if (b.key !== 'auto' && this.normalized_query.match(re)) {
            return b
          }
        }
        return {key: '', title: 'тип запроса не распознан', about: ''}
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
      }
    },
    methods: {
      hide_modal() {
        this.showModal = false
        this.$refs.modal.$el.style.display = 'none'
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
      },
      check_base() {
        if (this.base === -1 && this.bases.length > 0) {
          let params = new URLSearchParams(window.location.search)
          let rmis_uid = params.get('rmis_uid')
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
          } else {
            this.base = this.bases[0].pk
          }
          this.emit_input()
        }
      },
      emit_input() {
        let pk = -1
        if ('pk' in this.selected_card)
          pk = this.selected_card.pk
        this.$emit('input', {
          pk: pk,
          base: this.selected_base,
          ofname: parseInt(this.directive_doc),
          operator: this.is_operator,
          history_num: this.history_num
        })
      },
      clear() {
        this.loaded = false
        this.selected_card = {}
        this.history_num = ''
        this.founded_cards = []
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
    font-weight: bolder;
    overflow: hidden;
    text-overflow: ellipsis;
    vertical-align: middle;
  }

  .table-content-row {
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .cursor-pointer {
    cursor: pointer;
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
</style>
