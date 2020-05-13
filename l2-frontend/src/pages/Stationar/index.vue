<template>
  <div ref="root" class="root">
    <div class="sidebar">
      <div class="sidebar-top">
        <input type="text" class="form-control" v-model="pk" @keyup.enter="load()" autofocus
               placeholder="Номер истории"/>
        <button class="btn btn-blue-nb" @click="load()" :disabled="pk === ''">Загрузить</button>
      </div>
      <div class="sidebar-content">
        <div class="inner" v-if="direction !== null && !!patient.fio_age">
          <div class="inner-card">
            <a :href="`/forms/pdf?type=106.01&dir_pk=${direction}`" class="a-under"
               target="_blank" v-if="!every" style="float: right">
              форма 003/у
            </a>
            <a :href="`/forms/pdf?type=105.03&dir_pk=${direction}`" class="a-under" target="_blank" v-if="every">
              №{{tree.map(d => d.direction).join('-')}}
            </a>
            <a :href="`/forms/pdf?type=105.03&dir_pk=${direction}`" class="a-under" target="_blank" v-else>
              История/б №{{direction}}
            </a>
          </div>
          <div class="inner-card" v-if="every">
            Загружены все истории
          </div>
          <div class="inner-card" v-if="every">
            <a :href="`/forms/pdf?type=106.01&dir_pk=${direction}`" class="a-under" target="_blank">
              форма 003/у
            </a>
          </div>
          <div class="inner-card" v-else>
            {{issTitle}}
          </div>
          <div class="inner-card" v-if="cancel">
            <strong>Направление отменено</strong>
          </div>
          <patient-card :patient="patient" class="inner-card"/>
          <div class="inner-card">
            <a href="#"
               v-tippy="{ placement : 'right', arrow: true, reactive : true,
                  popperOptions: {
                    modifiers: {
                      preventOverflow: {
                        boundariesElement: 'window'
                      },
                      hide: {
                        enabled: false
                      }
                    }
                  },
                  interactive : true, html: '#template-anamnesis' }"
               @show="load_anamnesis"
               class="a-under"
               @click.prevent="edit_anamnesis">Анамнез жизни</a>
            <div id="template-anamnesis">
              <strong>Анамнез жизни</strong><br/>
              <span v-if="anamnesis_loading">загрузка...</span>
              <pre v-else
                   style="padding: 5px;text-align: left;white-space: pre-wrap;word-break: keep-all;max-width:600px"
              >{{anamnesis_data.text || 'нет данных'}}</pre>
            </div>
          </div>
          <div class="sidebar-btn-wrapper"
               v-for="(title, key) in menuItems"
               :key="key">
            <button class="btn btn-blue-nb sidebar-btn"
                    @click="load_directions(key)"
            >
              <span v-if="Boolean(counts[key])" class="counts">{{counts[key]}} шт.</span> {{title}}
            </button>
            <button class="btn btn-blue-nb sidebar-btn"
                    v-if="!every &&
                    menuNeedPlus[key] &&
                    (!allowedOnlyOneEntry[key] || !Boolean(counts[key])) &&
                    (!forbidden_edit || (can_add_tadp && key === 't, ad, p sheet'))"
                    @click="plus(key)"
            >
              <i class="fa fa-plus"/>
            </button>
          </div>
          <template v-for="(dir, index) in tree">
            <div class="sidebar-btn-wrapper" v-if="!every && dir.isCurrent" :key="dir.direction">
              <button class="btn btn-blue-nb sidebar-btn active-btn" style="font-size: 12px">
                <i class="fa fa-arrow-down" v-if="index < tree.length - 1"/>
                <i class="fa fa-dot-circle-o" v-else/>
                №{{dir.direction}} {{dir.research_title}}
                <i class="fa fa-check"/>
              </button>
            </div>
            <div class="sidebar-btn-wrapper" v-else :key="dir.direction">
              <button class="btn btn-blue-nb sidebar-btn"
                      style="font-size: 12px"
                      @click="load_pk(dir.direction)"
              >
                <i class="fa fa-arrow-down" v-if="index < tree.length - 1"/>
                <i class="fa fa-dot-circle-o" v-else/>
                №{{dir.direction}} {{dir.research_title}}
              </button>
            </div>
          </template>
          <div class="sidebar-btn-wrapper" v-if="tree.length > 1">
            <button class="btn btn-blue-nb sidebar-btn text-center"
                    style="font-size: 12px"
                    @click="load_pk(tree[0].direction, true)"
            >
              <i class="fa fa-cubes"/>
              Загрузить всё
            </button>
          </div>
          <div class="sidebar-btn-wrapper" v-if="tree.length > 1">
            <button class="btn btn-blue-nb sidebar-btn text-center"
                    style="font-size: 12px"
                    @click="close()"
            >
              <i class="fa fa-close"/>
              Отмена просмотра истории
            </button>
          </div>
        </div>
      </div>
    </div>
      <div class="sidebar-anesthesia" :class="[{show_anesthesia: show_anesthesia_menu}, {hide_anesthesia: !show_anesthesia_menu}  ]">
        <div class="title-anesthesia"><p style="color: whitesmoke">Течение анестезии</p></div>
        <vue-timepicker style="margin: 3px" v-model="timeValue" format="H:mm" input-width="100px" input-class="timepicker_attr"
                        hide-clear-button close-on-complete></vue-timepicker>
        <input type="text" class="no-outline" placeholder="SpO2"/>
        <input type="text" class="no-outline" placeholder="CO2"/>
        <input type="text" class="no-outline" placeholder="Температура"/>
        <input type="text" class="no-outline" placeholder="Систолическое давление"/>
        <input type="text" class="no-outline" placeholder="Диастолическое давление"/>
        <br/>
        <br/>
        <button class="btn btn-blue-nb" @click="close_form">
          Добавить
        </button>
      </div>
    <div class="content">
      <div class="top">
        <div class="top-block title-block" v-if="opened_list_key">
          <span>
            {{menuItems[opened_list_key]}}
            <br/>
            <a href="#" class="a-under" @click.prevent="print_all_list"><i class="fa fa-print"/> результатов</a>
          </span>
          <i class="top-right fa fa-times" @click="close_list_directions"/>
        </div>
        <div class="top-block direction-block"
             :class="{confirmed: Boolean(d.confirm), active: opened_form_pk === d.pk}"
             @click="open_form(d)"
             :key="d.pk" v-for="d in list_directions">
          <span>
            <display-direction :direction="d"/>
          </span>
        </div>
      </div>
      <div class="inner results-editor">
        <div v-for="row in researches_forms">
          <div class="research-title">
            <div class="research-left">
<!--              <button style="margin-right: 5px" class="btn btn-blue-nb" @click="show_anesthesia_menu=!show_anesthesia_menu" title="Добавить значения в наркозную карту" v-tippy v-if="row.research.title.includes('анестез')">-->
              <button style="margin-right: 5px" class="btn btn-blue-nb" @click="show_anesthesia_sidebar" title="Добавить значения в наркозную карту" v-tippy v-if="row.research.title.includes('анестез')">
                <i class="fa fa-heartbeat fa-lg" aria-hidden="true"></i>
              </button>
              {{row.research.title}}
              <span class="comment" v-if="row.research.comment"> [{{row.research.comment}}]</span>
              <dropdown :visible="research_open_history === row.pk"
                        :position='["left", "bottom", "left", "top"]'
                        @clickout="hide_results">
                <a style="font-weight: normal"
                   href="#" @click.prevent="open_results(row.pk)">
                  (другие результаты)
                </a>
                <div class="results-history" slot="dropdown">
                  <ul>
                    <li v-for="r in research_history">
                      Результат от {{r.date}}
                      <a href="#" @click.prevent="print_results(r.direction)">печать</a>
                      <a href="#" @click.prevent="copy_results(row, r.pk)" v-if="!row.confirmed">скопировать</a>
                    </li>
                    <li v-if="research_history.length === 0">результатов не найдено</li>
                  </ul>
                </div>
              </dropdown>
            </div>
            <div class="research-right">
              <template v-if="row.confirmed">
                <a :href="`/forms/pdf?type=105.02&napr_id=[${opened_form_pk}]`"
                   class="btn btn-blue-nb" target="_blank" v-if="stat_btn">Статталон</a>
                <a href="#" class="btn btn-blue-nb"
                   @click.prevent="print_results(opened_form_pk)">Печать</a>
              </template>
              <template>
                <a :href="row.pacs" class="btn btn-blue-nb" v-if="!!row.pacs"
                   target="_blank"
                   title="Снимок" v-tippy>
                  &nbsp;<i class="fa fa-camera"/>&nbsp;
                </a>
                <template v-if="!row.confirmed">
                  <button class="btn btn-blue-nb" @click="save(row)" v-if="!row.confirmed"
                          title="Сохранить без подтверждения" v-tippy>
                    &nbsp;<i class="fa fa-save"/>&nbsp;
                  </button>
                  <button class="btn btn-blue-nb" @click="clear_vals(row)" title="Очистить протокол" v-tippy>
                    &nbsp;<i class="fa fa-times"/>&nbsp;
                  </button>
                  <div class="right-f" v-if="fte">
                    <select-picker-m v-model="templates[row.pk]"
                                     :search="true"
                                     :options="row.templates.map(x => ({label: x.title, value: x.pk}))"/>
                  </div>
                  <button class="btn btn-blue-nb" @click="load_template(row, templates[row.pk])" v-if="fte">
                    Загрузить шаблон
                  </button>
                </template>
              </template>
            </div>
          </div>
          <DescriptiveForm
            :research="row.research"
            :pk="row.pk"
            :confirmed="Boolean(!!row.confirmed || !!row.forbidden_edit)"
            :patient="patient_form"
            :change_mkb="change_mkb(row)"
            :hospital_r_type="'desc'"
          />
          <div class="group" v-if="r_is_transfer(row)">
            <div class="group-title">Отделение перевода</div>
            <div class="fields">
              <div class="content-picker" v-if="!row.confirmed">
                <research-pick :class="{ active: r.pk === stationar_research }" :research="r"
                               @click.native="stationar_research = r.pk"
                               class="research-select"
                               v-for="r in stationar_researches_filtered"
                               force_tippy
                               :key="r.pk"/>
              </div>
              <div v-else-if="row.research.transfer_direction">
                История болезни №{{row.research.transfer_direction}}
                <br/>
                {{row.research.transfer_direction_iss[0]}}
                <br/>
                <a class="a-under" href="#" @click.prevent="print_hosp(row.research.transfer_direction)">
                  Печать ш/к браслета
                </a>
                <br/>
                <a class="a-under" href="#" @click.prevent="print_direction(row.research.transfer_direction)">
                  Печать направления
                </a>
                <br/>
                <a class="a-under" href="#" @click.prevent="load_pk(row.research.transfer_direction)">
                  Открыть историю
                </a>
              </div>
            </div>
          </div>
          <div class="group" v-if="is_diary(row.research)">
            <div class="group-title">Направления в рамках приёма</div>
            <div class="row">
              <div class="col-xs-12">
                <div class="sd">
                  <directions-history :iss_pk="row.pk" kk="stationar" forHospSlave/>
                </div>
                <div class="sd empty" v-if="!row.confirmed">
                  <button @click="create_directions(row)"
                          class="btn btn-primary-nb btn-blue-nb" type="button">
                    <i class="fa fa-plus"></i> создать направления
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div class="control-row" :key="row.research.version">
            <div class="res-title">{{row.research.title}}:</div>
            <iss-status :i="row"/>
            <button class="btn btn-blue-nb" @click="save(row)"
                    v-if="!row.confirmed && !row.forbidden_edit">
              Сохранить
            </button>
            <button class="btn btn-blue-nb" @click="save_and_confirm(row)"
                    v-if="!row.confirmed && !row.forbidden_edit"
                    :disabled="!r(row)">
              Сохранить и подтвердить
            </button>
            <button class="btn btn-blue-nb" @click="reset_confirm(row)"
                    v-if="row.confirmed && row.allow_reset_confirm && (!row.forbidden_edit || can_reset_transfer)">
              Сброс подтверждения
            </button>
            <button class="btn btn-blue-nb" @click="close_form">
              Закрыть
            </button>
            <div class="status-list" v-if="!r(row) && !row.confirmed">
              <div class="status status-none">Не заполнено:</div>
              <div class="status status-none" v-for="rl in r_list(row)">{{rl}};</div>
            </div>
          </div>
        </div>
        <div style="padding: 5px" v-if="!opened_form_pk">
          <AggregateLaboratory v-if="opened_list_key === 'laboratory'" :pk="iss" disabled />
          <AggregateDesc
            v-if="['paraclinical', 'consultation', 'diaries'].includes(opened_list_key)"
            :pk="iss"
            :r_type="opened_list_key"
            disabled
          />
          <AggregateTADP
            v-if="opened_list_key === 't, ad, p sheet'"
            :directions="every ? tree.map(d => d.direction) : [direction]"
          />
        </div>
      </div>
    </div>
    <modal @close="closePlus" marginLeftRight="auto"
           margin-top="60px"
           max-width="1400px" ref="modalStationar" show-footer="true"
           v-if="openPlusMode === 'directions' || create_directions_for > -1"
           white-bg="true" width="100%">
      <span slot="header">Создание направлений – история {{direction}} {{issTitle}}, {{patient.fio_age}}</span>
      <div class="registry-body" slot="body" style="min-height: 140px">
        <div class="row">
          <div class="col-xs-6"
               style="height: 450px;border-right: 1px solid #eaeaea;padding-right: 0;">
            <researches-picker v-model="create_directions_data"
                               :types-only="pickerTypesOnly"
                               kk="stationar"
                               style="border-top: 1px solid #eaeaea;border-bottom: 1px solid #eaeaea;"/>
          </div>
          <div class="col-xs-6" style="height: 450px;padding-left: 0;">
            <selected-researches
              kk="stationar"
              :base="bases_obj[patient.base]"
              :researches="create_directions_data"
              :main_diagnosis="create_directions_diagnosis"
              :valid="true"
              :card_pk="patient.cardId"
              :initial_fin="finId"
              :parent_iss="iss"
              :parent_slave_iss="create_directions_for > -1 ? create_directions_for : null"
              :clear_after_gen="true"
              style="border-top: 1px solid #eaeaea;border-bottom: 1px solid #eaeaea;"
            />
          </div>
        </div>
        <div v-if="create_directions_data.length > 0"
             style="margin-top: 5px;text-align: left">
          <table class="table table-bordered lastresults">
            <colgroup>
              <col width="180">
              <col>
              <col width="110">
              <col width="110">
            </colgroup>
            <tbody>
            <last-result :individual="patient.individualId" :key="p" v-for="p in create_directions_data"
                         :parent-iss="iss"
                         :noScroll="true"
                         :research="p"/>
            </tbody>
          </table>
        </div>
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-4">
            <button @click="closePlus" class="btn btn-primary-nb btn-blue-nb" type="button">
              Закрыть
            </button>
          </div>
        </div>
      </div>
    </modal>
    <modal v-if="openPlusMode === 'stationar'" ref="modalStationar2" @close="closePlus"
           margin-top="50px"
           show-footer="true" white-bg="true" max-width="710px" width="100%" marginLeftRight="auto">
      <span slot="header">{{menuItems[openPlusId]}} – история {{direction}} {{issTitle}}, {{patient.fio_age}}</span>
      <div slot="body" style="min-height: 200px;background-color: #fff" class="registry-body">
        <div class="text-left">
          <div class="content-picker">
            <research-pick :class="{ active: row.pk === direction_service }" :research="row"
                           @click.native="select_research(row.pk)"
                           class="research-select"
                           force_tippy
                           v-for="row in hosp_services"
                           :key="row.pk"/>
            <div v-if="hosp_services.length === 0">не настроено</div>
          </div>
          <div class="text-center" style="margin-top: 10px;">
            <button @click="confirm_service"
                    :disabled="direction_service === -1"
                    class="btn btn-primary-nb btn-blue-nb" type="button">
              Сохранить назначение и заполнить протокол
            </button>
          </div>
        </div>
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-4">
            <button @click="closePlus" class="btn btn-primary-nb btn-blue-nb" type="button">
              Закрыть
            </button>
          </div>
        </div>
      </div>
    </modal>
    <modal v-if="anamnesis_edit" ref="modalAnamnesisEdit" @close="hide_modal_anamnesis_edit" show-footer="true"
           white-bg="true" max-width="710px" width="100%" marginLeftRight="auto" margin-top>
      <span slot="header">Редактор анамнеза жизни – карта {{patient.card}}, {{patient.fio_age}}</span>
      <div slot="body" style="min-height: 140px" class="registry-body">
          <textarea v-model="anamnesis_data.text" rows="14" class="form-control"
                    placeholder="Анамнез жизни"></textarea>
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-4">
            <button @click="hide_modal_anamnesis_edit" class="btn btn-primary-nb btn-blue-nb" type="button">
              Отмена
            </button>
          </div>
          <div class="col-xs-4">
            <button @click="save_anamnesis()" class="btn btn-primary-nb btn-blue-nb" type="button">
              Сохранить
            </button>
          </div>
        </div>
      </div>
    </modal>
    <results-viewer :pk="show_results_pk" v-if="show_results_pk > -1" no_desc/>
  </div>
</template>

<script>
  import {mapGetters} from 'vuex'
  import dropdown from 'vue-my-dropdown'
  import menuMixin from './mixins/menu'
  import * as action_types from '../../store/action-types'
  import stationar_point from '../../api/stationar-point'
  import PatientCard from './PatientCard'
  import Patient from '../../types/patient'
  import Modal from '../../ui-cards/Modal'
  import ResearchesPicker from '../../ui-cards/ResearchesPicker'
  import LastResult from '../../ui-cards/LastResult'
  import SelectedResearches from '../../ui-cards/SelectedResearches'
  import ResearchPick from '../../ui-cards/ResearchPick'
  import directions_point from '../../api/directions-point'
  import IssStatus from '../../ui-cards/IssStatus'
  import {vField, vGroup} from '../../components/visibility-triggers'
  import researches_point from '../../api/researches-point'
  import SelectPickerM from '../../fields/SelectPickerM'
  import DescriptiveForm from '../../forms/DescriptiveForm'
  import ResultsViewer from '../../modals/ResultsViewer'
  import DisplayDirection from './DisplayDirection'
  import AggregateLaboratory from '../../fields/AggregateLaboratory'
  import AggregateDesc from '../../fields/AggregateDesc'
  import patients_point from '../../api/patients-point'
  import UrlData from '../../UrlData'
  import AggregateTADP from '../../fields/AggregateTADP'
  import DirectionsHistory from '../../ui-cards/DirectionsHistory'
  import VueTimepicker from 'vue2-timepicker/src/vue-timepicker.vue'

  export default {
    mixins: [menuMixin],
    components: {
      DirectionsHistory,
      dropdown,
      AggregateTADP,
      AggregateDesc,
      AggregateLaboratory,
      DisplayDirection,
      ResultsViewer,
      DescriptiveForm,
      SelectPickerM,
      IssStatus, ResearchPick, SelectedResearches, LastResult, ResearchesPicker, Modal, PatientCard,
      VueTimepicker
    },
    data() {
      return {
        pk: '',
        every: false,
        direction: null,
        forbidden_edit: null,
        cancel: false,
        iss: null,
        issTitle: null,
        finId: null,
        counts: {},
        patient: new Patient({}),
        openPlusMode: null,
        openPlusId: null,
        create_directions_data: [],
        tree: [],
        hosp_services: [],
        direction_service: -1,
        create_directions_for: -1,
        create_directions_diagnosis: '',
        show_results_pk: -1,
        list_directions: [],
        opened_list_key: null,
        opened_form_pk: null,
        researches_forms: [],
        patient_form: {},
        templates: {},
        stationar_researches: [],
        stationar_research: -1,
        anamnesis_edit: false,
        anamnesis_data: {
          text: '',
        },
        anamnesis_loading: false,
        new_anamnesis: null,
        research_open_history: null,
        research_history: [],
        inited: false,
        show_anesthesia_menu: false,
        timeValue: {
          H: '',
          mm : '',
        },
      }
    },
    watch: {
      pk() {
        this.pk = this.pk.replace(/\D/g, '')
      },
      navState() {
        if (this.inited) {
          UrlData.set(this.navState);
        }

        UrlData.title(this.every ? null : this.direction);
      },
    },
    async mounted() {
      await this.$store.dispatch(action_types.INC_LOADING)
      const {researches} = await researches_point.getResearchesByDepartment({department: -5})
      this.stationar_researches = researches
      await this.$store.dispatch(action_types.DEC_LOADING)
      this.$root.$on('hide_results', () => {
        this.show_results_pk = -1
      })
      const storedData = UrlData.get();
      if (storedData && typeof storedData === 'object') {
        if (storedData.pk) {
          await this.load_pk(storedData.pk, storedData.every || false);
        }
        if (storedData.opened_list_key) {
          await this.load_directions(storedData.opened_list_key)
        }
        if (storedData.opened_form_pk && Array.isArray(this.list_directions)) {
          for (const dir of this.list_directions) {
            if (storedData.opened_form_pk === dir.pk) {
              await this.open_form(dir);
              break;
            }
          }
        }
      }
      this.inited = true
    },
    methods: {
      getCurrentTime() {
        let timeInMs = new Date();
        this.timeValue.H = timeInMs.getHours().toString();
        this.timeValue.mm = timeInMs.getMinutes().toString();
      },
      show_anesthesia_sidebar() {
        this.show_anesthesia_menu = !this.show_anesthesia_menu;
        this.getCurrentTime();
        if (this.show_anesthesia_menu === false) {
          clearInterval(renewTime)
          }

        if (this.show_anesthesia_menu === true) {
          var renewTime = setInterval(()=> this.getCurrentTime(), 1000 * 20);
        }

      },

      is_diary(research) {
        const res_title = research.title.toLowerCase();
        return res_title.includes('осмотр') || res_title.includes('дневник');
      },
      create_directions(iss) {
        this.create_directions_diagnosis = iss.diagnos;
        this.create_directions_for = iss.pk
      },
      async confirm_service() {
        await this.$store.dispatch(action_types.INC_LOADING)
        const {pk} = await stationar_point.makeService({
          service: this.direction_service,
          main_direction: this.direction,
        })
        await this.load_directions(this.openPlusId)
        if (pk) {
          await this.open_form({pk, type: this.plusDirectionsMode[this.openPlusId] ? 'directions' : 'stationar'})
        }
        await this.closePlus()
        this.counts = await stationar_point.counts(this, ['direction'])
        await this.$store.dispatch(action_types.DEC_LOADING)
      },
      select_research(pk) {
        this.direction_service = pk
      },
      async open_form(d) {
        const mode = d.type
        if (mode === 'stationar') {
          this.close_form()
          this.opened_form_pk = d.pk
          await this.$store.dispatch(action_types.INC_LOADING)
          const {researches, patient} = await directions_point.getParaclinicForm({pk: d.pk, force: true})
          this.researches_forms = researches
          this.patient_form = patient
          await this.$store.dispatch(action_types.DEC_LOADING)
        } else {
          this.show_results_pk = d.pk
        }
      },
      close_form() {
        this.hide_results();
        this.opened_form_pk = null
        this.researches_forms = null
        this.patient_form = null
        this.stationar_research = -1
      },
      async load_pk(pk, every = false) {
        this.pk = String(pk)
        await this.load(every)
      },
      async close(force = false) {
        this.hide_results();
        if (!force) {
          try {
            await this.$dialog.confirm(`Подтвердите отмену просмотра истории «${this.direction}»`)
          } catch (_) {
            return
          }
        }
        this.close_list_directions()
        this.anamnesis_edit = false
        this.anamnesis_data = {
          text: ''
        }
        this.direction = null
        this.cancel = false
        this.iss = null
        this.issTitle = null
        this.finId = null
        this.counts = {}
        this.patient = new Patient({})
        this.openPlusId = null
        this.openPlusMode = null
        this.forbidden_edit = false
        this.every = false
        this.stationar_research = -1
        this.create_directions_data = []
        this.tree = []
      },
      async load(every = false) {
        this.hide_results();
        await this.close(true);
        await this.$store.dispatch(action_types.INC_LOADING)
        const {ok, data, message} = await stationar_point.load(this, ['pk'], {every})
        if (ok) {
          this.pk = ''
          this.every = every
          this.direction = data.direction
          this.cancel = data.cancel
          this.iss = data.iss
          this.issTitle = data.iss_title
          this.finId = data.fin_pk
          this.forbidden_edit = data.forbidden_edit
          this.soft_forbidden = !!data.soft_forbidden
          this.tree = data.tree
          this.patient = new Patient(data.patient)
          this.counts = await stationar_point.counts(this, ['direction'], {every})
          if (message && message.length > 0) {
            wrnmessage(message)
          }
        } else {
          errmessage(message)
        }
        await this.$store.dispatch(action_types.DEC_LOADING)
      },
      print_all_list() {
        this.$root.$emit('print:results', this.list_directions.map(d => d.pk))
      },
      close_list_directions() {
        this.close_form()
        this.list_directions = []
        this.opened_list_key = null
      },
      async load_directions(key, no_close = false) {
        await this.$store.dispatch(action_types.INC_LOADING)
        if (!no_close) {
          this.close_list_directions()
        }
        const {data} = await stationar_point.directionsByKey({
          direction: this.direction,
          r_type: key,
          every: this.every,
        })
        this.list_directions = data
        this.opened_list_key = key
        await this.$store.dispatch(action_types.DEC_LOADING)
      },
      async plus(key) {
        const mode = this.plusDirectionsMode[key] ? 'directions' : 'stationar'
        if (mode === 'stationar') {
          await this.$store.dispatch(action_types.INC_LOADING)
          const {data} = await stationar_point.hospServicesByType({
            direction: this.direction,
            r_type: key,
          })
          this.hosp_services = data
          if (data.length === 1) {
            this.direction_service = data[0].pk
          }
          await this.$store.dispatch(action_types.DEC_LOADING)
        }
        this.openPlusMode = mode
        this.openPlusId = key
      },
      async closePlus() {
        this.create_directions_for = -1
        this.openPlusMode = null
        this.create_directions_diagnosis = ''
        this.openPlusId = null
        this.create_directions_data = []
        this.hosp_services = []
        this.direction_service = -1

        if (this.$refs.modalStationar && this.$refs.modalStationar.$el) {
          this.$refs.modalStationar.$el.style.display = 'none'
        }

        if (this.$refs.modalStationar2 && this.$refs.modalStationar2.$el) {
          this.$refs.modalStationar2.$el.style.display = 'none'
        }

        this.$store.dispatch(action_types.INC_LOADING)
        this.counts = await stationar_point.counts(this, ['direction'])
        this.$store.dispatch(action_types.DEC_LOADING)
        this.reload_if_need(true)
      },
      print_results(pk) {
        this.$root.$emit('print:results', [pk])
      },
      reload_if_need(no_close = false) {
        if (!this.opened_list_key) {
          return
        }
        this.load_directions(this.opened_list_key, no_close)
      },
      save(iss) {
        this.hide_results();
        this.$store.dispatch(action_types.INC_LOADING)
        directions_point.paraclinicResultSave({
          force: true,
          data: {
            ...iss,
            direction: {
              pk: this.opened_form_pk
            },
            stationar_research: this.stationar_research,
          },
          with_confirm: false,
          visibility_state: this.visibility_state(iss)
        }).then(data => {
          if (data.ok) {
            okmessage('Сохранено')
            iss.saved = true
            iss.research.transfer_direction_iss = data.transfer_direction_iss
            this.reload_if_need(true)
          } else {
            errmessage(data.message)
          }
        }).finally(() => {
          this.$store.dispatch(action_types.DEC_LOADING)
        })
      },
      save_and_confirm(iss) {
        this.hide_results();
        this.$store.dispatch(action_types.INC_LOADING)
        directions_point.paraclinicResultSave({
          force: true,
          data: {
            ...iss,
            direction: {
              pk: this.opened_form_pk
            },
            stationar_research: this.stationar_research,
          },
          with_confirm: true,
          visibility_state: this.visibility_state(iss)
        }).then(data => {
          if (data.ok) {
            okmessage('Сохранено')
            okmessage('Подтверждено')
            iss.saved = true
            iss.allow_reset_confirm = !data.forbidden_edit || this.can_reset_transfer
            iss.confirmed = true
            iss.research.transfer_direction = data.transfer_direction
            iss.research.transfer_direction_iss = data.transfer_direction_iss
            iss.forbidden_edit = data.forbidden_edit
            this.forbidden_edit = data.forbidden_edit
            this.soft_forbidden = data.soft_forbidden
            this.stationar_research = -1
            this.reload_if_need(true)
          } else {
            errmessage(data.message)
          }
        }).finally(() => {
          this.$store.dispatch(action_types.DEC_LOADING)
        })
      },
      async reset_confirm(iss) {
        this.hide_results();
        try {
          await this.$dialog.confirm(`Подтвердите сброс подтверждения услуги «${iss.research.title}»`)
        } catch (_) {
          return
        }

        await this.$store.dispatch(action_types.INC_LOADING)

        const data = await directions_point.paraclinicResultConfirmReset({iss_pk: iss.pk})

        if (data.ok) {
          okmessage('Подтверждение сброшено')
          iss.confirmed = false
          this.reload_if_need(true)
          if (data.is_transfer || data.is_extract) {
            this.forbidden_edit = !!data.forbidden_edit
          }
          iss.forbidden_edit = data.forbidden_edit
        } else {
          errmessage(data.message)
        }

        await this.$store.dispatch(action_types.DEC_LOADING)
      },
      async copy_results(row, pk) {
        await this.$store.dispatch(action_types.INC_LOADING);
        this.hide_results();
        const {data} = await directions_point.paraclinicDataByFields({pk});
        this.replace_fields_values(row, data);
        await this.$store.dispatch(action_types.DEC_LOADING);
      },
      async open_results(pk) {
        if (this.research_open_history) {
          this.hide_results();
          return
        }
        await this.$store.dispatch(action_types.INC_LOADING);
        this.research_history = (await directions_point.paraclinicResultPatientHistory({pk, isSameParent: true})).data || [];
        await this.$store.dispatch(action_types.DEC_LOADING);
        this.research_open_history = pk
      },
      hide_results() {
        this.research_history = [];
        this.research_open_history = null
      },
      r_is_transfer({research}) {
        return research.can_transfer
      },
      r(research) {
        return this.r_list(research).length === 0
      },
      r_list(research) {
        const l = []
        if (research.confirmed) {
          return []
        }

        for (const g of research.research.groups) {
          if (!vGroup(g, research.research.groups, this.patient_form)) {
            continue
          }
          let n = 0
          for (const f of g.fields) {
            n++
            if (f.required && f.field_type !== 3 && (f.value === '' || f.value === '- Не выбрано' || !f.value) &&
              vField(g, research.research.groups, f.visibility, this.patient_form)) {
              l.push((g.title !== '' ? g.title + ' ' : '') + (f.title === '' ? 'поле ' + n : f.title))
            }
          }
        }
        if (this.r_is_transfer(research) && this.stationar_research === -1) {
          l.push('Отделение перевода')
        }
        return l.slice(0, 2)
      },
      change_mkb() {
      },
      template_fields_values(row, dataTemplate, title) {
        this.$dialog.alert(title, {
          view: 'replace-append-modal',
        }).then(({data}) => {
          if (data === 'append') {
            this.append_fields_values(row, dataTemplate)
          } else {
            this.replace_fields_values(row, dataTemplate)
          }
        })
      },
      replace_fields_values(row, data) {
        for (const g of row.research.groups) {
          for (const f of g.fields) {
            if (![1, 3, 16, 17, 20, 13, 14, 11].includes(f.field_type)) {
              f.value = data[f.pk] || ''
            }
          }
        }
      },
      append_fields_values(row, data) {
        for (const g of row.research.groups) {
          for (const f of g.fields) {
            if (![1, 3, 16, 17, 20, 13, 14, 11].includes(f.field_type) && data[f.pk]) {
              this.append_value(f, data[f.pk])
            }
          }
        }
      },
      clear_vals(row) {
        this.$dialog
          .confirm('Вы действительно хотите очистить результаты?')
          .then(() => {
            okmessage('Очищено')
            for (const g of row.research.groups) {
              for (const f of g.fields) {
                if (![1, 3, 16, 17, 20, 13, 14, 11].includes(f.field_type)) {
                  this.clear_val(f)
                }
              }
            }
          })
      },
      clear_val(field) {
        field.value = ''
      },
      append_value(field, value) {
        let add_val = value
        if (add_val !== ',' && add_val !== '.') {
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
      },
      load_template(row, pk) {
        this.$store.dispatch(action_types.INC_LOADING)
        researches_point.getTemplateData({pk: parseInt(pk)}).then(({data: {fields: data, title}}) => {
          this.template_fields_values(row, data, title)
        }).finally(() => {
          this.$store.dispatch(action_types.DEC_LOADING)
        })
      },
      visibility_state(iss) {
        const groups = {}
        const fields = {}
        const {groups: igroups} = iss.research
        for (const group of iss.research.groups) {
          if (!vGroup(group, igroups, this.patient_form)) {
            groups[group.pk] = false
          } else {
            groups[group.pk] = true
            for (const field of group.fields) {
              fields[field.pk] = vField(group, igroups, field.visibility, this.patient_form)
            }
          }
        }

        return {
          groups,
          fields,
        }
      },
      print_direction(pk) {
        this.$root.$emit('print:directions', [pk])
      },
      print_hosp(pk) {
        this.$root.$emit('print:hosp', [pk])
      },
      async load_anamnesis() {
        this.anamnesis_loading = true
        this.anamnesis_data = await patients_point.loadAnamnesis(this.patient, 'card_pk')
        this.anamnesis_loading = false
      },
      async edit_anamnesis() {
        await this.$store.dispatch(action_types.INC_LOADING)
        this.anamnesis_data = await patients_point.loadAnamnesis(this.patient, 'card_pk')
        await this.$store.dispatch(action_types.DEC_LOADING)
        this.anamnesis_edit = true
      },
      async save_anamnesis() {
        await this.$store.dispatch(action_types.INC_LOADING)
        await patients_point.saveAnamnesis(this.patient, 'card_pk', {text: this.anamnesis_data.text})
        await this.$store.dispatch(action_types.DEC_LOADING)
        this.new_anamnesis = this.anamnesis_data.text
        this.hide_modal_anamnesis_edit()
      },
      hide_modal_anamnesis_edit() {
        if (this.$refs.modalAnamnesisEdit) {
          this.$refs.modalAnamnesisEdit.$el.style.display = 'none'
        }
        this.anamnesis_edit = false
      },
    },
    computed: {
      ...mapGetters({
        user_data: 'user_data',
        researches: 'researches',
        bases: 'bases',
      }),
      navState() {
        if (!this.direction) {
          return null
        }
        return {
          pk: this.direction,
          opened_list_key: this.opened_list_key,
          opened_form_pk: this.opened_form_pk,
          every: this.every,
        };
      },
      stationar_researches_filtered() {
        return [{
          pk: -1,
          title: 'Не выбрано'
        }, ...(this.stationar_researches || []).filter(r => r.title !== this.issTitle && !r.hide)]
      },
      bases_obj() {
        return this.bases.reduce((a, b) => ({
          ...a,
          [b.pk]: b,
        }), {})
      },
      stat_btn() {
        return this.$store.getters.modules.l2_stat_btn
      },
      pickerTypesOnly() {
        if (this.openPlusId === 'laboratory') {
          return [2]
        }
        if (this.openPlusId === 'paraclinical') {
          return [3]
        }
        if (this.openPlusId === 'consultation') {
          return [4]
        }
        if (this.openPlusId === null) {
          return [2, 3, 4]
        }
        return []
      },
      fte() {
        return this.$store.getters.modules.l2_fast_templates
      },
      can_reset_transfer() {
        for (let g of (this.$store.getters.user_data.groups || [])) {
          if (g === 'Сброс подтверждения переводного эпикриза') {
            return true
          }
        }
        return false
      },
      can_add_tadp() {
        for (let g of (this.$store.getters.user_data.groups || [])) {
          if (g === 't, ad, p') {
            return !!this.soft_forbidden || !this.forbidden_edit
          }
        }
        return false
      },
    }
  }
</script>

<style scoped lang="scss">
  .root {
    display: flex;
    align-items: stretch;
    flex-direction: row;
    flex-wrap: nowrap;
    align-content: stretch;

    & > div {
      align-self: stretch;
    }
  }

  .sidebar {
    width: 260px;
    border-right: 1px solid #b1b1b1;
    display: flex;
    flex-direction: column;
  }

  .show_anesthesia {
    width: 260px;
  }

  .hide_anesthesia {
    width: 0;
  }

  .sidebar-anesthesia {
    /*width: 260px; !* 0 width - change this with JavaScript *!*/
    height: 100%;
    position: fixed; /* Stay in place */
    z-index: 1;
    top: 100px;
    left: 0;
    background-color: #eee;
    overflow-x: hidden;
    transition: 0.6s;
    display: flex;
    flex-direction: column;
    border-right: 1px solid #56616c ;
    .btn {
      border-radius: 0;
      padding: 5px 4px;
      width: 50%;
    }
    .title-anesthesia {
      height: 5%;
      width: 260px;
      background-color: #56616c;
    }
      input {
        border-top-style: hidden;
        border-right-style: hidden;
        border-left-style: hidden;
        border-bottom-style: groove;
        background-color: #eee;
        margin-left: 3px;
        margin-right: 3px;
        margin-top: 8px;
      }
      input:focus,
      input:active {
        /*border-color: transparent;*/
        border-bottom: 2px solid #56616c;
      }
      .no-outline:focus {
        outline: none;
      }
      p {
        padding: 5px;
        margin-left: 5px;

      }
  }


  .content {
    display: flex;
    flex-direction: column;
    width: calc(100% - 260px);
    border: none;

    .top {
      border-bottom: 1px solid #b1b1b1;
      height: 80px;
      padding: 5px;
      overflow-x: auto;
      overflow-y: visible;
      white-space: nowrap;

      .top-block {
        display: inline-flex;
        align-items: center;
        justify-content: center;

        span {
          align-self: center;
          display: inline-block;
          text-align: center;
        }

        vertical-align: top;
        height: 100%;
        white-space: normal;
        width: 130px;
        padding: 3px;
        margin-right: 3px;
        border-radius: 3px;
        border: 1px solid rgba(0, 0, 0, 0.14);
        background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);
      }

      .title-block {
        position: relative;
        margin-right: 0;

        .top-right {
          position: absolute;
          top: 0;
          right: 0;
          padding: 3px;
          color: lightgray;
          cursor: pointer;

          &:hover {
            color: #000;
          }
        }
      }

      .direction-block {
        cursor: pointer;
        transition: all .2s cubic-bezier(.25, .8, .25, 1);
        position: relative;

        span {
          display: block;
          position: absolute;
          top: 0;
          right: 0;
          bottom: 0;
          left: 0;
        }

        &:hover {
          z-index: 1;
          transform: translateY(-1px);
        }

        &:not(.confirmed):hover {
          box-shadow: 0 7px 14px rgba(0, 0, 0, 0.1), 0 5px 5px rgba(0, 0, 0, 0.12);
        }

        &.confirmed {
          border-color: #049372;
          background: linear-gradient(to bottom, #04937254 0%, #049372ba 100%);

          &:hover {
            box-shadow: 0 7px 14px #04937254, 0 5px 5px #049372ba;
          }
        }

        &.active {
          background-image: linear-gradient(#6C7A89, #56616c) !important;
          color: #fff !important;
        }
      }
    }

    .inner {
      height: calc(100% - 80px);
      overflow-y: auto;
      overflow-x: hidden;
    }
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
      width: 166px !important;
      flex: 2 166px;
      min-width: 0;
    }

    button {
      flex: 3 94px;
      width: 94px
    }
  }

  .sidebar-content {
    position: relative;
    height: calc(100% - 34px);

    .inner {
      height: 100%;
      overflow-y: auto;
      overflow-x: hidden;

      &-card {
        width: 100%;
        background: #fff;
        border-bottom: 1px solid #b1b1b1 !important;
        padding: 4px 12px;
      }
    }
  }

  .sidebar-btn {
    border-radius: 0;

    &:not(.text-center) {
      text-align: left;
    }

    border-top: none !important;
    border-right: none !important;
    border-left: none !important;
    padding: 0 12px;
    height: 24px;

    &:not(:hover), &.active-btn:hover {
      cursor: default;
      background-color: rgba(#000, .02) !important;
      color: #000;
      border-bottom: 1px solid #b1b1b1 !important;
    }
  }

  .sidebar-btn-wrapper {
    display: flex;
    flex-direction: row;

    .sidebar-btn:first-child {
      flex: 1 1 auto;
    }
  }

  .lastresults {
    table-layout: fixed;
    padding: 0;
    margin: 0;
    color: #000;
    background-color: #ffdb4d;
    border-color: #000;

    /deep/ th, /deep/ td {
      border-color: #000;
    }

    /deep/ a {
      color: #000;
      text-decoration: dotted underline;
    }

    /deep/ a:hover {
      text-decoration: none;
    }
  }

  .counts {
    float: right;
  }

  .content-picker {
    display: flex;
    flex-wrap: wrap;
    justify-content: stretch;
    align-items: stretch;
    align-content: flex-start;
  }

  .research-select {
    align-self: stretch;
    display: flex;
    align-items: center;
    padding: 1px 2px 1px;
    color: #000;
    background-color: #fff;
    text-decoration: none;
    transition: .15s linear all;
    margin: 0;
    font-size: 12px;
    min-width: 0;
    flex: 0 1 auto;
    width: 25%;
    height: 34px;
    border: 1px solid #6C7A89 !important;
    cursor: pointer;
    text-align: left;
    outline: transparent;

    &.active {
      background: #049372 !important;
      color: #fff;
    }

    &:hover {
      box-shadow: inset 0 0 8px rgba(0, 0, 0, .8) !important;
    }
  }

  .research-title {
    position: sticky;
    top: 0;
    background-color: #ddd;
    text-align: center;
    padding: 5px;
    font-weight: bold;
    z-index: 4;
    display: flex;
  }

  .research-left {
    position: relative;
    text-align: left;
    width: calc(100% - 390px);
    .btn {
      border-radius: 0;
      padding: 5px 4px;
      margin-top: -5px;
      margin-bottom: -5px;
      white-space: nowrap;
    }
  }


  .research-right {
    text-align: right;
    width: 390px;
    margin-top: -5px;
    margin-right: -5px;
    margin-bottom: -5px;
    white-space: nowrap;

    .btn {
      border-radius: 0;
      padding: 5px 4px;
    }
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

  .right-f {
    width: 140px;
    display: inline-block;

    /deep/ .btn {
      border-radius: 0;
      padding-top: 5px;
      padding-bottom: 5px;
    }
  }

  .status-list {
    display: flex;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .status, .control-row .amd {
    padding: 5px;
  }

  .status {
    font-weight: bold;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .status-none {
    color: #CF3A24
  }

  .results-history {
    margin-top: -95px;
    margin-left: -295px;
    margin-right: -100px;
    padding: 8px;
    background: #fff;
    border-radius: 4px;
    box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);

    ul {
      padding-left: 20px;
      margin: 0;

      li {
        font-weight: normal;

        a {
          font-weight: bold;
          display: inline-block;
          padding: 2px 4px;
          background: rgba(#000, .03);
          border-radius: 4px;
          margin-left: 3px;

          &:hover {
            background: rgba(#000, .1);
          }
        }
      }
    }
  }

  .direction, .sd {
    padding: 5px;
    margin: 5px;
    border-radius: 5px;
    border: 1px solid rgba(0, 0, 0, 0.14);
    background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);

    hr {
      margin: 3px;
    }
  }
</style>
