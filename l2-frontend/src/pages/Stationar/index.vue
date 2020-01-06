<template>
  <div ref="root" class="root">
    <div class="sidebar">
      <div class="sidebar-top">
        <input type="text" class="form-control" v-model="pk" @keyup.enter="load" autofocus
               placeholder="Номер истории"/>
        <button class="btn btn-blue-nb" @click="load" :disabled="pk === ''">Загрузить</button>
      </div>
      <div class="sidebar-content">
        <div class="inner" v-if="direction !== null && patient !== null">
          <div class="inner-card">
            <a :href="`/forms/pdf?type=106.01&dir_pk=${direction}`" target="_blank" style="float: right">форма 003/у</a>
            История/б №{{direction}}
          </div>
          <div class="inner-card">
            {{issTitle}}
          </div>
          <patient-card :patient="patient" class="inner-card"/>
          <div class="sidebar-btn-wrapper"
               v-for="(title, key) in menuItems"
               :key="key">
            <button class="btn btn-blue-nb sidebar-btn"
                    @click="load_directions(key)"
            >
              <span v-if="Boolean(counts[key])" class="counts">{{counts[key]}} шт.</span> {{title}}
            </button>
            <button class="btn btn-blue-nb sidebar-btn"
                    v-if="menuNeedPlus[key]"
                    @click="plus(key)"
            >
              <i class="fa fa-plus"/>
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="content">
      <div class="top">
        <div class="top-block title-block" v-if="opened_list_key">
          <span>{{menuItems[opened_list_key]}}</span>
          <i class="fa fa-times" @click="close_list_directions"/>
        </div>
        <div class="top-block direction-block"
             :class="{confirmed: Boolean(d.confirm), active: opened_form_pk === d.pk}"
             @click="open_form(opened_list_key, d.pk)"
             v-tippy="{
                html: '#tp-' + d.pk,
                reactive: true,
                arrow: true,
                animation: 'fade',
                duration: 0,
                theme: 'light',
                placement: 'bottom',
                popperOptions: {
                  modifiers: {
                    preventOverflow: {
                      enabled: false
                    },
                    hide: {
                      enabled: false
                    }
                  }
                },
             }"
             :key="d.pk" v-for="d in list_directions">
          <span>
            {{d.pk}}
            <br/>
            {{d.date_create}}
          </span>
          <div :id="`tp-${d.pk}`" class="tp">
            <ul>
              <li v-for="r in d.researches" :key="r">{{r}}</li>
            </ul>
          </div>
        </div>
      </div>
      <div class="inner results-editor">
        <div v-for="row in researches_forms">
          <div class="research-title">
            <div class="research-left">
              {{row.research.title}}
              <span class="comment" v-if="row.research.comment && row.research.comment !== ''"> [{{row.research.comment}}]</span>
            </div>
            <div class="research-right">
              <template v-if="row.confirmed">
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
            :confirmed="row.confirmed"
            :patient="patient_form"
            :change_mkb="change_mkb(row)"
          />
          <div class="control-row">
            <div class="res-title">{{row.research.title}}:</div>
            <iss-status :i="row"/>
            <button class="btn btn-blue-nb" @click="save(row)" v-if="!row.confirmed">Сохранить</button>
            <button class="btn btn-blue-nb" @click="save_and_confirm(row)" v-if="!row.confirmed"
                    :disabled="!r(row)">
              Сохранить и подтвердить
            </button>
            <button class="btn btn-blue-nb" @click="reset_confirm(row)"
                    v-if="row.confirmed && row.allow_reset_confirm">
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
      </div>
    </div>
    <modal @close="closePlus" marginLeftRight="auto"
           margin-top="60px"
           max-width="1400px" ref="modalStationar" show-footer="true"
           v-if="openPlusMode === 'directions'"
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
              :main_diagnosis="'-'"
              :valid="true"
              :card_pk="patient.cardId"
              :initial_fin="finId"
              :parent_iss="iss"
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
    <results-viewer :pk="show_results_pk" v-if="show_results_pk > -1" no_desc/>
  </div>
</template>

<script>
  import {mapGetters} from 'vuex'
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

  export default {
    mixins: [menuMixin],
    components: {
      ResultsViewer,
      DescriptiveForm,
      SelectPickerM,
      IssStatus, ResearchPick, SelectedResearches, LastResult, ResearchesPicker, Modal, PatientCard
    },
    data() {
      return {
        pk: '',
        direction: null,
        iss: null,
        issTitle: null,
        finId: null,
        counts: {},
        patient: new Patient({}),
        openPlusMode: null,
        openPlusId: null,
        create_directions_data: [],
        hosp_services: [],
        direction_service: -1,
        show_results_pk: -1,
        list_directions: [],
        opened_list_key: null,
        opened_form_key: null,
        opened_form_pk: null,
        researches_forms: [],
        patient_form: {},
        templates: {},
      }
    },
    watch: {
      pk() {
        this.pk = this.pk.replace(/\D/g, '')
      }
    },
    mounted() {
      this.$root.$on('hide_results', () => {
        this.show_results_pk = -1
      })
    },
    methods: {
      async confirm_service() {
        await this.$store.dispatch(action_types.INC_LOADING)
        const {pk} = await stationar_point.makeService({
          service: this.direction_service,
          main_direction: this.direction,
        })
        await this.load_directions(this.openPlusId)
        await this.open_form(this.openPlusId, pk)
        await this.closePlus()
        this.counts = await stationar_point.counts(this, ['direction'])
        await this.$store.dispatch(action_types.DEC_LOADING)
      },
      select_research(pk) {
        this.direction_service = pk
      },
      async open_form(key, pk) {
        const mode = this.plusDirectionsMode[key] ? 'directions' : 'stationar'
        if (mode === 'stationar') {
          this.close_form()
          this.opened_form_key = key
          this.opened_form_pk = pk
          await this.$store.dispatch(action_types.INC_LOADING)
          const {researches, patient} = await directions_point.getParaclinicForm({pk, force: true})
          this.researches_forms = researches
          this.patient_form = patient
          await this.$store.dispatch(action_types.DEC_LOADING)
        } else {
          this.show_results_pk = pk
        }
      },
      close_form() {
        this.opened_form_key = null
        this.opened_form_pk = null
        this.researches_forms = null
        this.patient_form = null
      },
      async load() {
        this.close_list_directions()
        this.direction = null
        this.iss = null
        this.issTitle = null
        this.finId = null
        this.counts = {}
        this.patient = new Patient({})
        this.openPlusId = null
        this.openPlusMode = null
        this.create_directions_data = []
        await this.$store.dispatch(action_types.INC_LOADING)
        const {ok, data, message} = await stationar_point.load(this, ['pk'])
        if (ok) {
          this.pk = ''
          this.direction = data.direction
          this.iss = data.iss
          this.issTitle = data.iss_title
          this.finId = data.fin_pk
          this.patient = new Patient(data.patient)
          this.counts = await stationar_point.counts(this, ['direction'])
        } else {
          errmessage(message)
        }
        await this.$store.dispatch(action_types.DEC_LOADING)
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
        this.openPlusMode = null
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

        this.$store.dispatch(action_types.INC_LOADING).then()
        this.counts = await stationar_point.counts(this, ['direction'])
        this.$store.dispatch(action_types.DEC_LOADING).then()
      },
      print_results(pk) {
        this.$root.$emit('print:results', [pk])
      },
      reload_if_need(no_close = false) {
        this.load_directions(this.opened_list_key, no_close)
      },
      save(iss) {
        this.$store.dispatch(action_types.INC_LOADING).then()
        directions_point.paraclinicResultSave({
          data: {
            ...iss,
            direction: {
              pk: this.opened_form_pk
            },
          },
          with_confirm: false,
          visibility_state: this.visibility_state(iss)
        }).then(data => {
          if (data.ok) {
            okmessage('Сохранено')
            iss.saved = true
            this.reload_if_need(true)
            this.changed = false
          } else {
            errmessage(data.message)
          }
        }).finally(() => {
          this.$store.dispatch(action_types.DEC_LOADING).then()
        })
      },
      save_and_confirm(iss) {
        this.$store.dispatch(action_types.INC_LOADING).then()
        directions_point.paraclinicResultSave({
          data: {
            ...iss,
            direction: {
              pk: this.opened_form_pk
            },
          },
          with_confirm: true,
          visibility_state: this.visibility_state(iss)
        }).then(data => {
          if (data.ok) {
            okmessage('Сохранено')
            okmessage('Подтверждено')
            iss.saved = true
            iss.allow_reset_confirm = true
            iss.confirmed = true
            this.reload_if_need(true)
            this.changed = false
          } else {
            errmessage(data.message)
          }
        }).finally(() => {
          this.$store.dispatch(action_types.DEC_LOADING).then()
        })
      },
      reset_confirm(iss) {
        let msg = `Сбросить подтверждение исследования ${iss.research.title}?`
        let doreset = confirm(msg)
        if (doreset === false || doreset === null) {
          return
        }
        this.$store.dispatch(action_types.INC_LOADING).then()
        directions_point.paraclinicResultConfirmReset({iss_pk: iss.pk}).then(data => {
          if (data.ok) {
            okmessage('Подтверждение сброшено')
            iss.confirmed = false
            this.reload_if_need()
            this.changed = false
          } else {
            errmessage(data.message)
          }
        }).finally(() => {
          this.$store.dispatch(action_types.DEC_LOADING).then()
        })
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
            if (f.required && (f.value === '' || f.value === '- Не выбрано' || !f.value) &&
              (f.field_type !== 3 ||
                vField(g, research.research.groups, f.visibility, this.patient_form))) {
              l.push((g.title !== '' ? g.title + ' ' : '') + (f.title === '' ? 'поле ' + n : f.title))
            }
          }
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
            if (![3].includes(f.field_type)) {
              f.value = data[f.pk] || ''
            }
          }
        }
      },
      append_fields_values(row, data) {
        for (const g of row.research.groups) {
          for (const f of g.fields) {
            if (![3, 1, 11].includes(f.field_type) && data[f.pk]) {
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
                if (![3].includes(f.field_type)) {
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
        this.$store.dispatch(action_types.INC_LOADING).then()
        researches_point.getTemplateData({pk: parseInt(pk)}).then(({data: {fields: data, title}}) => {
          this.template_fields_values(row, data, title)
        }).finally(() => {
          this.$store.dispatch(action_types.DEC_LOADING).then()
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
    },
    computed: {
      ...mapGetters({
        user_data: 'user_data',
        researches: 'researches',
        bases: 'bases',
      }),
      bases_obj() {
        return this.bases.reduce((a, b) => ({
          ...a,
          [b.pk]: b,
        }), {})
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
        return []
      },
      fte() {
        return this.$store.getters.modules.l2_fast_templates
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

        i {
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

        &:not(.confirmed):hover {
          z-index: 1;
          transform: scale(1.008);
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
    text-align: left;
    border-top: none !important;
    border-right: none !important;
    border-left: none !important;
    padding: 0 12px;
    height: 24px;

    &:not(:hover) {
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
    z-index: 2;
    display: flex;
  }

  .research-left {
    position: relative;
    text-align: left;
    width: calc(100% - 390px);
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

  .tp {
    text-align: left;
    line-height: 1.1;

    ul {
      padding-left: 20px;
      margin: 0;
    }
  }
</style>
