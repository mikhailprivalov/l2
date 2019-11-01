<template>
  <div style="height: 100%;width: 100%;position: relative">
    <div class="top-picker" :class="{internalType: selected_base.internal_type}">
      <div class="input-group">
        <div class="input-group-btn" v-if="bases.length > 1">
          <button class="btn btn-blue-nb btn-ell dropdown-toggle nbr" type="button" data-toggle="dropdown"
                  style="width: 200px;text-align: left!important;">
            <span class="caret"></span> {{selected_base.title}}
          </button>
          <ul class="dropdown-menu">
            <li v-for="row in bases" :value="row.pk" v-if="!row.hide && row.pk !== selected_base.pk">
              <a href="#" @click.prevent="select_base(row.pk)">{{row.title}}</a>
            </li>
          </ul>
        </div>
        <div class="input-group-btn" v-else>
          <button class="btn btn-blue-nb btn-ell dropdown-toggle nbr" type="button" data-toggle="dropdown"
                  style="max-width: 200px;text-align: left!important;">{{selected_base.title}}
          </button>
        </div>
        <input type="text" class="form-control bob" v-model="query" placeholder="Введите запрос" ref="q"
               maxlength="255" @keyup.enter="search">
        <span class="rmis-search input-group-btn" v-if="selected_base.internal_type && user_data.rmis_enabled">
          <label class="btn btn-blue-nb nbr" style="padding: 5px 12px;">
            <input type="checkbox" v-model="inc_rmis"/> Вкл. РМИС
          </label>
        </span>
        <span class="input-group-btn">
          <button style="margin-right: -2px"
                  class="btn last btn-blue-nb nbr" type="button" :disabled="!query_valid || inLoading" @click="search">
            Поиск
          </button>
        </span>
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
          <tr>
            <td class="table-header-row">
              <span class="hospital" style="display: block;line-height: 1.2;"
                    v-if="history_n === 'true'">Номер истории:</span>
            </td>
            <td class="table-content-row">
              <div style="height: 34px" v-if="history_n === 'true'">
                <span class="hospital">
                  <input type="text" class="form-control" maxlength="11" v-model="history_num"
                         :disabled="!selected_base.history_number"/>
                </span>
              </div>
            </td>
            <td colspan="2">
              <div v-if="selected_base.internal_type && l2_cards" class="internal_type">
                <button class="btn last btn-blue-nb nbr" :class="{[`disp_${selected_card.status_disp}`]: true}"
                        ref="disp"
                        type="button" v-tippy="{ placement : 'bottom', arrow: false, reactive : true,
                                                theme : 'light bordered',
                                                duration : 0,
                                                distance: 4,
                                                sticky: true,
                                                trigger: 'click',
                                                interactive : true, html: '#template-disp' }"
                        v-if="selected_card.pk && selected_card.status_disp && selected_card.status_disp !== 'notneed'">
                  Д
                </button>
                <button class="btn last btn-blue-nb nbr" type="button"
                        v-tippy="{ placement : 'bottom', arrow: true }"
                        title="Льготы пациента" @click="open_benefit()"
                        v-if="l2_benefit && selected_card.pk"><i class="fa fa-cubes"></i></button>
                <button class="btn last btn-blue-nb nbr" type="button"
                        v-tippy="{ placement : 'bottom', arrow: true }"
                        title="Диспансерный учёт" @click="open_dreg()"
                        v-if="is_l2_cards && selected_card.pk"><i class="fa fa-database"></i></button>
                <button class="btn last btn-blue-nb nbr" type="button"
                        v-tippy="{ placement : 'bottom', arrow: true }"
                        title="Анамнез жизни" @click="open_anamnesis()"
                        v-if="is_l2_cards && selected_card.pk"><i class="fa fa-book"></i></button>
                <button class="btn last btn-blue-nb nbr" type="button"
                        v-tippy="{ placement : 'bottom', arrow: true }"
                        title="Новая L2 карта" @click="open_editor(true)"
                        v-if="is_l2_cards && allow_l2_card_edit"><i class="fa fa-plus"></i></button>
                <button class="btn last btn-blue-nb nbr" type="button"
                        v-tippy="{ placement : 'bottom', arrow: true }"
                        title="Редактирование карты" style="margin-left: -1px" :disabled="!selected_card.pk"
                        @click="open_editor()"
                        v-if="is_l2_cards && allow_l2_card_edit"><i class="glyphicon glyphicon-pencil"></i></button>
              </div>
              <div class="internal_type" v-else-if="l2_cards && allow_l2_card_edit">
                <button class="btn last btn-blue-nb nbr" type="button"
                        v-tippy="{ placement : 'bottom', arrow: true }"
                        title="Открыть пациента в базе L2" style="margin-left: -1px"
                        :disabled="!selected_card.pk" @click="open_as_l2_card()">L2
                </button>
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
      <div id="template-disp"
           class="disp"
           v-if="selected_card.pk && selected_card.status_disp && selected_card.status_disp !== 'notneed'">
        <strong>Диспансеризация</strong><br/>
        <ul style="padding-left: 25px;text-align: left">
          <li v-for="d in selected_card.disp_data">
          <span :class="{disp_row: true, [!!d[2] ? 'disp_row_finished' : 'disp_row_need']: true}">
            <span v-if="!d[2]">требуется</span>
            <a v-else href="#" @click.prevent="show_results([d[2]])" class="not-black">
              пройдено
            </a>
          </span>

            <a href="#" @click.prevent="add_researches([d[0]])">
              {{d[5]}}
            </a>
          </li>
        </ul>
        <div>
          <a href="#"
             class="btn btn-blue-nb"
             v-if="selected_card.status_disp === 'need'"
             @click.prevent="add_researches(selected_card.disp_data.filter(d => !d[2]).map(d => d[0]), true)">
            Выбрать требуемые
          </a>
          <a href="#"
             class="btn btn-blue-nb"
             v-else
             @click.prevent="show_results(selected_card.disp_data.map(d => d[2]))">
            Печать всех результатов
          </a>
        </div>
      </div>
    </div>
    <div class="bottom-picker" v-if="bottom_picker === 'true'">
      <slot name="for_card_bottom"/>
    </div>
    <modal ref="modal" v-if="showModal" @close="hide_modal" show-footer="true">
      <span slot="header">Найдено несколько карт</span>
      <div slot="body">
        <div class="founded" v-for="(row, i) in founded_cards" @click="select_card(i)">
          <div class="founded-row">Карта <span class="b">{{row.type_title}} {{row.num}}</span></div>
          <div class="founded-row"><span class="b">ФИО, пол:</span> {{row.family}} {{row.name}} {{row.twoname}},
            {{row.sex}}
          </div>
          <div class="founded-row"><span class="b">Дата рождения:</span> {{row.birthday}} ({{row.age}})</div>
          <div class="founded-row" v-for="d in row.docs">
            <span class="b">{{d.type_title}}:</span> {{d.serial}} {{d.number}}
          </div>
        </div>
      </div>
      <div slot="footer" class="text-center">
        <small>Показано не более 10 карт</small>
      </div>
    </modal>
    <l2-card-create :card_pk="editor_pk" v-if="editor_pk !== -2" :base_pk="base"/>
    <d-reg :card_pk="selected_card.pk" :card_data="selected_card" v-if="dreg"/>
    <benefit :card_pk="selected_card.pk" :card_data="selected_card" v-if="benefit" :readonly="false"/>
    <modal v-if="anamnesis" ref="modalAnamnesis" @close="hide_modal_anamnesis" show-footer="true" white-bg="true"
           max-width="710px" width="100%" marginLeftRight="auto" margin-top class="an">
      <span slot="header">Анамнез жизни – карта {{selected_card.num}}, {{selected_card.fio_age}}</span>
      <div slot="body" class="an-body">
        <div class="an-sidebar">
          <div class="an-s" :class="{active: an_state.tab === 'text'}" @click="an_tab('text')">Анамнез</div>
          <div class="an-s" :class="{active: an_state.tab === 'history'}" @click="an_tab('history')">История изменений
          </div>
        </div>
        <div class="an-content">
          <div v-if="an_state.tab === 'text'">
            <pre>{{anamnesis_data.text || 'нет данных'}}</pre>
          </div>
          <div v-else class="an-history">
            <div v-for="h in anamnesis_data.history">
              <pre>{{h.text || 'нет данных'}}</pre>
              {{h.who_save.fio}}, {{h.who_save.department}}. {{h.datetime}}
            </div>
          </div>
        </div>
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-4">
            <button @click="hide_modal_anamnesis" class="btn btn-primary-nb btn-blue-nb" type="button">
              Закрыть
            </button>
          </div>
        </div>
      </div>
    </modal>
  </div>
</template>

<script>
    import SelectPickerB from '../fields/SelectPickerB'
    import L2CardCreate from '../modals/L2CardCreate'
    import DReg from '../modals/DReg'
    import Benefit from '../modals/Benefit'
    import LinkSelector from '../fields/LinkSelector'
    import PatientCard from './PatientCard'
    import Modal from './Modal'
    import * as action_types from '../store/action-types'
    import patients_point from '../api/patients-point'
    import {mapGetters} from 'vuex'

    export default {
        name: 'patient-picker',
        components: {LinkSelector, PatientCard, SelectPickerB, Modal, L2CardCreate, DReg, Benefit},
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
            value: {},
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
                search_after_loading: false,
                editor_pk: -2,
                inc_rmis: false,
                anamnesis: false,
                anamnesis_data: {},
                an_state: {
                    tab: 'text',
                },
                dreg: false,
                benefit: false,
            }
        },
        created() {
            this.$store.dispatch(action_types.INC_LOADING).then()
            this.$store.dispatch(action_types.GET_DIRECTIVE_FROM).then(() => {
                this.local_directive_departments = this.$store.getters.directive_from
                this.directive_departments_select = []
                for (let dep of this.local_directive_departments) {
                    this.directive_departments_select.push({label: dep.title, value: dep.pk})
                }

                if (this.local_directive_departments.length > 0 && this.ofname_to_set === '-1') {
                    for (let dep of this.local_directive_departments) {
                        if (dep.pk === this.$store.getters.user_data.department.pk) {
                            this.directive_department = dep.pk + ''
                            this.check_base()
                            return
                        }
                    }
                    this.directive_department = this.local_directive_departments[0].pk.toString()
                }

                this.check_base()
            }).finally(() => {
                this.$store.dispatch(action_types.DEC_LOADING).then()
            })

            this.$store.watch(state => state.bases, (oldValue, newValue) => {
                this.check_base()
            })
            this.$root.$on('search', () => {
                this.search()
            })
            this.$root.$on('select_card', data => {
                this.base = data.base_pk
                this.query = `card_pk:${data.card_pk}`
                this.search_after_loading = true
                $(this.$refs.q).focus()
                this.emit_input()
                if (!data.hide) {
                    this.editor_pk = data.card_pk
                } else {
                    this.editor_pk = -2
                }
                setTimeout(() => {
                    this.search()
                    if (!data.hide) {
                        setTimeout(() => {
                            this.$root.$emit('reload_editor')
                        }, 5)
                    }
                }, 5)
            })
            this.$root.$on('hide_l2_card_create', () => {
                this.editor_pk = -2
            })
            this.$root.$on('hide_dreg', () => {
                this.dreg = false
            })
            this.$root.$on('hide_benefit', () => {
                this.benefit = false
            })
        },
        watch: {
            query() {
                this.query = this.query.split(' ')
                    .map((s) => s.split('-').map(x => x.charAt(0).toUpperCase() + x.substring(1).toLowerCase()).join('-'))
                    .join(' ')
            },
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
                this.emit_input(true)
            },
            inLoading() {
                if (!this.inLoading && (this.directive_department === '-1' || this.directive_doc === '-1')) {
                    this.update_ofname()
                }
                if (!this.inLoading && this.search_after_loading) {
                    this.search()
                }
            }
        },
        computed: {
            bases() {
                return this.$store.getters.bases.filter(b => !b.hide)
            },
            selected_base() {
                for (let b of this.bases) {
                    if (b.pk === this.base) {
                        return b
                    }
                }
                return {
                    title: 'Не выбрана база',
                    pk: -1,
                    hide: false,
                    history_number: false,
                    fin_sources: [],
                    internal_type: false,
                }
            },
            normalized_query() {
                return this.query.trim()
            },
            query_valid() {
                return this.normalized_query.length > 0
            },
            l2_cards() {
                return this.$store.getters.modules.l2_cards_module
            },
            l2_benefit() {
                return this.$store.getters.modules.l2_benefit
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
            is_doc() {
                if ('groups' in this.$store.getters.user_data) {
                    for (let g of this.$store.getters.user_data.groups) {
                        if (g === 'Лечащий врач') {
                            return true
                        }
                    }
                }
                return false
            },
            is_l2_cards() {
                if ('groups' in this.$store.getters.user_data) {
                    for (let g of this.$store.getters.user_data.groups) {
                        if (g === 'Картотека L2' || g === 'Admin' || g === 'Лечащий врач' || g === 'Оператор лечащего врача') {
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
                if (!this.is_doc && o.length > 0) {
                    o = [{label: 'Выберите врача', value: -2}, ...o]
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
            },
            ...mapGetters(['user_data']),
            allow_l2_card_edit() {
                return this.user_data.su || this.user_data.groups.includes('Картотека L2')
            },
        },
        methods: {
            open_anamnesis() {
                this.$store.dispatch(action_types.INC_LOADING).then()
                patients_point.loadAnamnesis({card_pk: this.selected_card.pk}).then(data => {
                    this.an_tab('text')
                    this.anamnesis_data = data
                }).finally(() => {
                    this.$store.dispatch(action_types.DEC_LOADING).then()
                    this.anamnesis = true
                })
            },
            hide_modal_anamnesis() {
                this.$refs.modalAnamnesis.$el.style.display = 'none'
                this.anamnesis_data = {}
                this.anamnesis = false
            },
            an_tab(tab) {
                this.an_state.tab = tab
            },
            open_dreg() {
                this.dreg = true
            },
            open_benefit() {
                this.benefit = true
            },
            open_editor(isnew) {
                if (isnew) {
                    this.editor_pk = -1
                } else {
                    this.editor_pk = this.selected_card.pk
                }
            },
            format_number(a) {
                if (a.length === 6) {
                    return `${a.slice(0, 2)}-${a.slice(2, 4)}-${a.slice(4, 6)}`
                } else if (a.length === 11) {
                    if (a.charAt(1) !== '9' && a.charAt(1) !== '8') {
                        return `${a.slice(0, 1)}-${a.slice(1, 5)}-${a.slice(5, 7)}-${a.slice(7, 9)}-${a.slice(9, 11)}`
                    }
                    return `${a.slice(0, 1)}-${a.slice(1, 4)}-${a.slice(4, 6)}-${a.slice(6, 8)}-${a.slice(8, 10)}-${a.slice(10, 11)}`
                }
                return a
            },
            hide_modal() {
                this.showModal = false
                if (this.$refs.modal)
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
                if (this.selected_card.base_pk) {
                    if (this.base && this.base !== this.selected_card.base_pk) {
                        this.query = ''
                    }
                    this.base = this.selected_card.base_pk
                }
                setTimeout(() => {
                    if (this.selected_card.status_disp === 'need' && this.$refs.disp) {
                        $(this.$refs.disp).click()
                    }
                }, 10)
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
                        let has_internal = false
                        for (let row of this.bases) {
                            if (row.internal_type) {
                                this.base = row.pk
                                this.query = rmis_uid
                                this.search_after_loading = true
                                has_internal = true
                                break
                            }
                        }
                        if (!has_internal) {
                            for (let row of this.bases) {
                                if (row.code === 'Р') {
                                    this.base = row.pk
                                    this.query = rmis_uid
                                    this.search_after_loading = true
                                    break
                                }
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
                    } else {
                        this.base = this.bases[0].pk
                    }
                    $(this.$refs.q).focus()
                    this.emit_input()
                }
            },
            emit_input(from_hn = false) {
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
                if (pk !== -1 && !from_hn) {
                    $('#fndsrc').focus()
                }
            },
            clear() {
                this.loaded = false
                this.selected_card = {}
                this.history_num = ''
                this.founded_cards = []
                if (this.query.toLowerCase().includes('card_pk:')) {
                    this.query = ''
                }
                this.emit_input()
            },
            open_as_l2_card() {
                this.$store.dispatch(action_types.ENABLE_LOADING, {loadingLabel: 'Загрузка...'}).then()
                patients_point.searchL2Card({card_pk: this.selected_card.pk}).then((result) => {
                    this.clear()
                    if (result.results) {
                        this.founded_cards = result.results
                        if (this.founded_cards.length > 1) {
                            this.showModal = true
                        } else if (this.founded_cards.length === 1) {
                            this.select_card(0)
                        }
                    } else {
                        errmessage('Ошибка на сервере')
                    }
                }).catch((error) => {
                    errmessage('Ошибка на сервере', error.message)
                }).finally(() => {
                    this.$store.dispatch(action_types.DISABLE_LOADING).then()
                })
            },
            search() {
                if (!this.query_valid || this.inLoading)
                    return
                const q = this.query
                this.check_base()
                $('input').each(function () {
                    $(this).trigger('blur')
                })
                this.$store.dispatch(action_types.ENABLE_LOADING, {loadingLabel: 'Поиск карты...'}).then()
                patients_point.searchCard({
                    type: this.base,
                    query: q,
                    list_all_cards: false,
                    inc_rmis: this.inc_rmis || this.search_after_loading
                }).then((result) => {
                    this.clear()
                    if (result.results) {
                        this.founded_cards = result.results
                        if (this.founded_cards.length > 1) {
                            this.showModal = true
                        } else if (this.founded_cards.length === 1) {
                            this.select_card(0)
                        } else {
                            errmessage('Не найдено', 'Карт по такому запросу не найдено')
                        }
                    } else {
                        errmessage('Ошибка на сервере')
                    }
                    if (this.search_after_loading) {
                        this.search_after_loading = false
                        this.query = ''
                    }
                }).catch((error) => {
                    errmessage('Ошибка на сервере', error.message)
                }).finally(() => {
                    this.$store.dispatch(action_types.DISABLE_LOADING).then()
                })
            },
            add_researches(pks, full = false) {
                for (const pk of pks) {
                    this.$root.$emit('researches-picker:add_research', pk)
                }
                if (full) {
                    if (this.$refs.disp) {
                        $(this.$refs.disp).click()
                        $(this.$refs.disp).blur()
                    }
                }
            },
            show_results(pk) {
                this.$root.$emit('print:results', pk)
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

    a:not(.ddm) {
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

  .an {
    align-items: stretch !important;
    justify-content: stretch !important;

    /deep/ .panel-flt {
      margin: 41px;
      align-self: stretch !important;
      width: 100%;
      display: flex;
      flex-direction: column;
    }

    /deep/ .panel-body {
      flex: 1;
      padding: 0;
      height: calc(100% - 91px);
      min-height: 200px;
      position: relative;
    }

    &-body {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      width: 100%;
      height: 100%;
      display: flex;
      align-items: stretch;
      flex-direction: row;
      flex-wrap: nowrap;
      align-content: stretch;

      & > div {
        align-self: stretch;
      }
    }

    &-sidebar {
      width: 100px;
      background: rgba(0, 0, 0, .04);
      border-right: 1px solid rgba(0, 0, 0, .16);
      overflow-y: auto;
      overflow-x: hidden;
    }

    &-content {
      display: flex;
      flex-direction: column;
      width: calc(100% - 100px);

      & > div {
        flex: 1;
        padding: 5px 10px;
        overflow-y: auto;
      }
    }

    &-history > div {
      margin-bottom: 10px;
      padding: 5px;
      background: rgba(#000, .1);
      border-radius: 5px;
    }

    &-s {
      padding: 5px;
      margin: 5px;
      border-radius: 5px;
      border: 1px solid rgba(0, 0, 0, 0.14);
      background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);

      &:not(.active) {
        cursor: pointer;
        transition: all .2s cubic-bezier(.25, .8, .25, 1);
      }

      position: relative;

      &.active {
        background-image: linear-gradient(#6C7A89, #56616c);
        color: #fff;
      }

      &:not(.active):hover {
        box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
        z-index: 1;
        transform: scale(1.008);
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

  .internal_type {
    width: 100%;
    display: flex;
    flex-wrap: nowrap;
    flex-direction: row;
    justify-content: stretch;

    .btn {
      align-self: stretch;
      flex: 1;
      padding: 6px 0;
    }
  }

  .founded {
    background: #fff;
    margin-bottom: 10px;
    cursor: pointer;
    padding: 5px;
    border-radius: 5px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
    transition: all .2s cubic-bezier(.25, .8, .25, 1);
    position: relative;

    &:hover {
      transform: scale(1.03);
      box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
      z-index: 1;
    }
  }

  .b {
    font-weight: bold;
  }

  .hospital input {
    border-radius: 0;
  }

  .disp {
    a:not(.btn):not(.not-black) {
      color: #0d0d0d !important;
      text-decoration: dotted underline;

      &:hover {
        text-decoration: none;
      }
    }

    &_need, &_need:focus, &_need:active, &_need:hover {
      background: #F4D03F !important;
    }

    &_finished, &_finished:focus, &_finished:active, &_finished:hover {
      background: #049372 !important;
    }

    .btn {
      width: 100%;
      padding: 4px;
    }
  }

  .disp_row {
    font-weight: bold;
    display: inline-block;
    width: 76px;

    &_need, &_need a {
      color: #ff0000 !important;
    }

    &_finished, &_finished a {
      color: #049372 !important;
    }

    a {
      text-decoration: dotted underline;

      &:hover {
        text-decoration: none;
      }
    }
  }
</style>

<style>
  #tippy-46 {
    transform: translate3d(253px, 166px, 0) !important;
  }
</style>
