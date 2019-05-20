<template>
  <div ref="root" class="results-root">
    <div class="results-sidebar">
      <div class="sidebar-top">
        <input type="text" class="form-control" v-model="pk" @keyup.enter="load" autofocus
               placeholder="Номер направления"/>
        <button class="btn btn-blue-nb" @click="load">Загрузить</button>
      </div>
      <div class="sidebar-bottom-top"><span>Результаты за</span>
        <date-field-nav :brn="false" :val.sync="date" :def="date"/>
      </div>
      <div class="directions" :class="{noStat: !stat_btn}">
        <div class="inner">
          <div class="direction" v-for="direction in directions_history">
            <div>
              {{direction.patient}}, {{direction.card}}
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
              <div class="col-xs-4"><a href="#" @click.prevent="load_pk(direction.pk)">Просмотр</a></div>
              <div class="col-xs-4 text-center">
                <a :href="`/forms/pdf?type=105.02&napr_id=[${direction.pk}]`"
                   target="_blank" v-if="direction.all_confirmed && stat_btn">Статталон</a>
              </div>
              <div class="col-xs-4 text-right">
                <a href="#" @click.prevent="print_results(direction.pk)" v-if="direction.all_confirmed">Печать</a>
              </div>
            </div>
          </div>
          <div class="text-center" style="margin: 5px" v-if="directions_history.length === 0">
            Нет данных
          </div>
        </div>
        <a v-if="directions_history.length > 0 && stat_btn"
           class="btn btn-blue-nb stat"
           :href="`/forms/preview?type=105.01&date=${date_to_form}`" target="_blank">печать статталонов</a>
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
            <div class="text-ell" :title="data.direction.diagnos" v-if="data.direction.diagnos !== ''">Диагноз:
              {{data.direction.diagnos}}
            </div>
          </div>
          <div class="col-xs-5">
            <div v-if="!data.patient.imported_from_rmis">Источник финансирования: {{data.direction.fin_source}}</div>
            <div>Карта: {{data.patient.card}}
              <a title="Анамнез жизни"
                 href="#"
                 v-if="data.card_internal && data.has_doc_referral"
                 v-tippy="{ placement : 'bottom', arrow: true }"
                 @click.prevent="edit_anamnesis"><i class="fa fa-book"></i></a>
              <a style="margin-left: 3px"
                 href="#"
                 v-if="data.card_internal && data.has_doc_referral"
                 v-tippy="{ placement : 'bottom', arrow: true, reactive : true,
                   interactive : true, html: '#template-dreg' }"
                 :class="{dreg_nex: !data.patient.has_dreg, dreg_ex: data.patient.has_dreg }"
                 @show="load_dreg_rows"
                 @click.prevent="dreg = true"><i class="fa fa-database"></i></a>
              <div id="template-dreg" :class="{hidden: !data.ok || !data.has_doc_referral}">
                <strong>Диспансерный учёт</strong><br/>
                <span v-if="dreg_rows_loading">загрузка...</span>
                <ul v-else style="padding-left: 25px;text-align: left">
                  <li v-for="r in dreg_rows">
                    {{r.diagnos}} – {{r.date_start}} <span v-if="r.illnes">– {{r.illnes}}</span>
                  </li>
                  <li v-if="dreg_rows.length === 0">нет активных записей</li>
                </ul>
              </div>
            </div>
            <div class="text-ell" :title="data.patient.doc" v-if="!data.patient.imported_from_rmis">Лечащий врач:
              {{data.patient.doc}}
            </div>
            <div v-else>Организация: {{data.patient.imported_org}}</div>
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
          <div class="research-title">
            <div class="research-left">
              {{row.research.title}}
              <dropdown :visible="research_open_history === row.pk"
                        :position='["left", "bottom", "left", "top"]'
                        @clickout="hide_results">
                <a style="font-weight: normal"
                   href="#" @click.prevent="open_results(row.pk)">
                  (другие результаты пациента)
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
            <div class="research-right" v-if="!row.confirmed">
              <button class="btn btn-blue-nb" @click="clear_vals(row)">Очистить</button>
              <div class="right-f" v-if="fte">
                <select-picker-m v-model="templates[row.pk]"
                                 :search="true"
                                 :options="row.templates.map(x => ({label: x.title, value: x.pk}))" />
              </div>
              <button class="btn btn-blue-nb" @click="load_template(row, templates[row.pk])" v-if="fte">
                Загрузить шаблон
              </button>
            </div>
          </div>
          <div class="group" v-for="group in row.research.groups">
            <div class="group-title" v-if="group.title !== ''">{{group.title}}</div>
            <div class="fields">
              <div class="field" v-for="field in group.fields" :class="{disabled: row.confirmed,
                empty: r_list_pk(row).includes(field.pk),
                required: field.required}"
                   :title="field.required && 'обязательно для заполнения'"
                   @mouseenter="enter_field" @mouseleave="leave_field">
                <div v-if="field.title !== ''" class="field-title">
                  {{field.title}}
                </div>
                <longpress v-if="!row.confirmed && field.field_type !== 3" class="btn btn-default btn-field" :on-confirm="clear_val" :confirm-time="0" :duration="400" :value="field" pressing-text="×" action-text="×">×</longpress>
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
                <div class="field-value" v-if="field.field_type === 0">
                  <textarea v-model="field.value" :rows="field.lines" class="form-control"
                            v-if="field.lines > 1" :readonly="row.confirmed"></textarea>
                  <input v-model="field.value" class="form-control" :readonly="row.confirmed" v-else/>
                </div>
                <div class="field-value" v-else-if="field.field_type === 1">
                  <input v-model="field.value" class="form-control" :readonly="row.confirmed" type="date" style="width: 160px"/>
                </div>
                <div class="field-value mkb10" v-else-if="field.field_type === 2 && !row.confirmed">
                  <m-k-b-field v-model="field.value" :short="false" @input="change_mkb(row, field)" />
                </div>
                <div class="field-value mkb10" v-else-if="field.field_type === 3">
                  <formula-field v-model="field.value" :formula="field.default_value" :fields="group.fields" />
                </div>
                <div class="field-value" v-else-if="field.field_type === 2 && row.confirmed">
                  <input v-model="field.value" class="form-control" :readonly="true" />
                </div>
              </div>
            </div>
          </div>
          <div class="group">
            <div class="group-title">Дополнительные услуги</div>
            <div class="row">
              <div class="col-xs-6"
                   style="height: 200px;border-right: 1px solid #eaeaea;padding-right: 0;">
                <researches-picker v-model="row.more" :hidetemplates="true"
                                   :readonly="row.confirmed"
                                   :just_search="true"
                                   :filter_types="[2]"/>
              </div>
              <div class="col-xs-6" style="height: 200px;padding-left: 0;">
                <selected-researches :researches="row.more"
                                     :readonly="row.confirmed" :simple="true"/>
              </div>
            </div>
          </div>
          <div class="group" v-if="row.research.is_doc_refferal && stat_btn">
            <div class="group-title">Данные статталона</div>
            <div class="fields">
              <div class="field">
                <div class="field-title">
                    Цель посещения
                </div>
                <div class="field-value">
                  <select v-model="row.purpose" :disabled="row.confirmed">
                    <option v-for="o in row.purpose_list" :value="o.pk">
                      {{o.title}}
                    </option>
                  </select>
                </div>
              </div>
              <div class="field">
                <div class="field-title">
                    Впервые
                </div>
                <label class="field-value">
                  <input type="checkbox" v-model="row.first_time" :disabled="row.confirmed" />
                </label>
              </div>
              <div class="field">
                <div class="field-title">
                    Результат обращения
                </div>
                <div class="field-value">
                  <select v-model="row.result" :disabled="row.confirmed">
                    <option v-for="o in row.result_list" :value="o.pk">
                      {{o.title}}
                    </option>
                  </select>
                </div>
              </div>
              <div class="field">
                <div class="field-title">
                    Исход
                </div>
                <div class="field-value">
                  <select v-model="row.outcome" :disabled="row.confirmed">
                    <option v-for="o in row.outcome_list" :value="o.pk">
                      {{o.title}}
                    </option>
                  </select>
                </div>
              </div>
              <div class="field">
                <div class="field-title">
                    Заключительный диагноз
                </div>
                <div class="field-value mkb10" v-if="!row.confirmed">
                  <m-k-b-field v-model="row.diagnos" />
                </div>
                <div class="field-value" v-else>
                  <input v-model="row.diagnos" class="form-control" :readonly="true" />
                </div>
              </div>
              <div class="field">
                <div class="field-title">
                    Подозрение на онко
                </div>
                <label class="field-value">
                  <input type="checkbox" v-model="row.maybe_onco" :disabled="row.confirmed" />
                </label>
              </div>
            </div>
          </div>
          <div class="control-row">
            <div class="res-title">{{row.research.title}}:</div>
            <div class="status status-none" v-if="!row.confirmed && !row.saved">Не сохранено</div>
            <div class="status status-saved" v-if="!row.confirmed && row.saved">Сохранено</div>
            <div class="status status-confirmed" v-if="row.confirmed && row.saved">Подтверждено</div>
            <button class="btn btn-blue-nb" @click="save(row)" v-if="!row.confirmed">Сохранить</button>
            <button class="btn btn-blue-nb" @click="save_and_confirm(row)" v-if="!row.confirmed" :disabled="!r(row)">Сохранить и
              подтвердить
            </button>
            <button class="btn btn-blue-nb" @click="reset_confirm(row)" v-if="row.confirmed && row.allow_reset_confirm">
              Сброс подтверждения
            </button>
            <div class="status-list" v-if="!r(row)">
              <div class="status status-none">Не заполнено:</div>
              <div class="status status-none" v-for="rl in r_list(row)">{{rl}};</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="results-content" v-else></div>
    <modal v-if="anamnesis_edit" ref="modalAnamnesisEdit" @close="hide_modal_anamnesis_edit" show-footer="true" white-bg="true" max-width="710px" width="100%" marginLeftRight="auto" margin-top>
      <span slot="header">Редактор анамнеза жизни – карта {{data.patient.card}}, {{data.patient.fio_age}}</span>
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
    <d-reg :card_pk="data.patient.card_pk" :card_data="data.patient" v-if="dreg" />
  </div>
</template>

<script>
  import moment from 'moment'
  import patients_point from './api/patients-point'
  import * as action_types from './store/action-types'
  import directions_point from './api/directions-point'
  import SelectPickerM from './SelectPickerM'
  import SelectPickerB from './SelectPickerB'
  import researches_point from './api/researches-point'
  import Longpress from 'vue-longpress'
  import Modal from './ui-cards/Modal'
  import MKBField from './MKBField'
  import DateFieldNav from './DateFieldNav'
  import FormulaField from './FormulaField'
  import DReg from './DReg'
  import dropdown from 'vue-my-dropdown';
  import ResearchesPicker from './ResearchesPicker'
  import SelectedResearches from './SelectedResearches'

  export default {
    name: 'results-paraclinic',
    components: {DateFieldNav, Longpress, Modal, MKBField, FormulaField, ResearchesPicker, SelectedResearches,
      dropdown, SelectPickerM, SelectPickerB, DReg},
    data() {
      return {
        pk: '',
        data: {ok: false},
        date: moment().format('DD.MM.YYYY'),
        directions_history: [],
        prev_scroll: 0,
        changed: false,
        inserted: false,
        anamnesis_edit: false,
        anamnesis_data: {},
        new_anamnesis: null,
        research_open_history: null,
        research_history: [],
        templates: {},
        dreg: false,
        dreg_rows_loading: false,
        dreg_rows: [],
      }
    },
    watch: {
      date() {
        this.load_history()
      },
    },
    mounted() {
      let vm = this
      $(window).on('beforeunload', function () {
        if (vm.has_changed)
          return 'Возможно имеются несохраненные изменения! Вы уверены, что хотите покинуть страницу?'
      })
      vm.load_history()
      this.$root.$on('hide_dreg', () => {
        this.load_dreg_rows();
        this.dreg = false;
      })
    },
    methods: {
      load_dreg_rows() {
        (async() => {
          this.dreg_rows_loading = true;
          this.dreg_rows = (await patients_point.loadDreg(this.data.patient.card_pk)).rows.filter(r => !r.date_end);
          this.data.patient.has_dreg = this.dreg_rows.length > 0
          this.dreg_rows_loading = false;
        })().then();
      },
      change_mkb(row, field) {
        console.log(row, field);
        if (field.value && !row.confirmed && row.research.is_doc_refferal && this.stat_btn) {
          const ndiagnos = field.value.split(' ')[0] || '';
          if (ndiagnos !== row.diagnos && ndiagnos.match(/^[A-Z]\d{1,2}(\.\d{1,2})?$/gm)) {
            okmessage('Диагноз в данных статталона обновлён', ndiagnos)
            row.diagnos = ndiagnos;
          }
        }
      },
      open_results(pk) {
        if (this.research_open_history) {
          this.hide_results()
          return;
        }
        let vm = this
        vm.$store.dispatch(action_types.INC_LOADING).then()
        this.research_history = [];
        directions_point.paraclinicResultPatientHistory(pk).then(({data}) => {
          vm.research_history = data
        }).finally(() => {
          vm.$store.dispatch(action_types.DEC_LOADING).then()
          this.research_open_history = pk;
        })
      },
      hide_results() {
        this.research_history = [];
        this.research_open_history = null;
      },
      r(research) {
        if (research.confirmed) {
          return true;
        }

        for (const g of research.research.groups) {
          for (const f of g.fields) {
            if (f.required && (f.value === '' || !f.value)) {
              return false;
            }
          }
        }
        return true;
      },
      r_list(research) {
        const l = [];
        if (research.confirmed) {
          return [];
        }

        for (const g of research.research.groups) {
          let n = 0;
          for (const f of g.fields) {
            n++;
            if (f.required && (f.value === '' || !f.value)) {
              l.push((g.title !== '' ? g.title + ' ' : '') + (f.title === '' ? 'поле ' + n : f.title));
            }
          }
        }
        return l.slice(0, 2);
      },
      r_list_pk(research) {
        const l = [];
        if (research.confirmed) {
          return [];
        }

        for (const g of research.research.groups) {
          let n = 0;
          for (const f of g.fields) {
            n++;
            if (f.required && (f.value === '' || !f.value)) {
              l.push(f.pk);
            }
          }
        }
        return l;
      },
      hide_modal_anamnesis_edit() {
        this.$refs.modalAnamnesisEdit.$el.style.display = 'none';
        this.anamnesis_edit = false;
      },
      save_anamnesis() {
        let vm = this
        vm.$store.dispatch(action_types.INC_LOADING).then()
        patients_point.saveAnamnesis(vm.data.patient.card_pk, this.anamnesis_data.text).then().finally(() => {
          this.$store.dispatch(action_types.DEC_LOADING).then()
          this.new_anamnesis = this.anamnesis_data.text;
          this.hide_modal_anamnesis_edit();
        })
      },
      edit_anamnesis() {
        let vm = this
        vm.$store.dispatch(action_types.INC_LOADING).then()
        patients_point.loadAnamnesis(vm.data.patient.card_pk).then(data => {
          vm.anamnesis_data = data
        }).finally(() => {
          this.$store.dispatch(action_types.DEC_LOADING).then()
          this.anamnesis_edit = true;
        })
      },
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
            this.dreg_rows_loading = false;
            this.dreg_rows = [];
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
        this.hide_results();
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
        this.hide_results();
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
        this.hide_results();
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
        this.hide_results();
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
        this.anamnesis_edit = false
        this.new_anamnesis = null
        this.data = {ok: false}
        this.research_open_history = null;
        this.dreg_rows_loading = false;
        this.dreg_rows = [];
      },
      print_direction(pk) {
        this.$root.$emit('print:directions', [pk])
      },
      print_results(pk) {
        this.$root.$emit('print:results', [pk])
      },
      copy_results(row, pk) {
        let vm = this
        vm.$store.dispatch(action_types.INC_LOADING).then()
        directions_point.paraclinicDataByFields(pk).then(({data}) => {
          this.hide_results();
          this.replace_fields_values(row, data);
        }).finally(() => {
          vm.$store.dispatch(action_types.DEC_LOADING).then()
        })
      },
      load_template(row, pk) {
        let vm = this
        vm.$store.dispatch(action_types.INC_LOADING).then()
        researches_point.getTemplateData(parseInt(pk)).then(({data: {fields: data, title}}) => {
          this.template_fields_values(row, data, title);
        }).finally(() => {
          vm.$store.dispatch(action_types.DEC_LOADING).then()
        })
      },
      template_fields_values(row, dataTemplate, title) {
        this.$dialog.alert(title, {
          view: 'replace-append-modal',
        }).then(({data}) => {
          if (data === 'append') {
            this.append_fields_values(row, dataTemplate);
          }  else {
            this.replace_fields_values(row, dataTemplate);
          }
        });
      },
      replace_fields_values(row, data) {
        for (const g of row.research.groups) {
          for (const f of g.fields) {
            if (![3].includes(f.field_type)) {
              f.value = data[f.pk] || '';
            }
          }
        }
      },
      append_fields_values(row, data) {
        for (const g of row.research.groups) {
          for (const f of g.fields) {
            if (![3, 1].includes(f.field_type) && data[f.pk]) {
              this.append_value(f, data[f.pk]);
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
                this.clear_val(f);
              }
            }
          }
        });
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
      date_to_form() {
        const date = this.date.split('.');
        return date.join('');
      },
      ca() {
        if (this.new_anamnesis !== null) {
          return this.new_anamnesis;
        }
        return this.data.anamnesis;
      },
      fte() {
        return this.$store.getters.modules.l2_fast_templates;
      },
      stat_btn() {
        return this.$store.getters.modules.l2_stat_btn;
      },
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
      },
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
      width: 199px !important;
      flex: 2 199px;
    }

    button {
      flex: 3 94px;
      width: 94px
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
    width: calc(100% - 380px);
  }

  .research-right {
    text-align: right;
    width: 380px;
    margin-top: -5px;
    margin-right: -5px;
    margin-bottom: -5px;
    button {
      border-radius: 0;
      padding: 5px 4px;
    }
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

  .results-history {
    margin-top: -95px;
    margin-left: -295px;
    margin-right: -100px;
    padding: 8px;
    background: #fff;
    border-radius: 4px;
    box-shadow: 0 14px 28px rgba(0,0,0,0.25), 0 10px 10px rgba(0,0,0,0.22);
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

  .results-editor {
    height: calc(100% - 68px);
    overflow-y: auto;
    overflow-x: hidden;
  }

  .group {
    margin: 5px;
    border: 1px solid #c1c1c1;
    background: #fff;
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
    flex: 0 0 34px;
    display: flex;
    justify-content: flex-start;
    align-items: center;

    /deep/ .form-control {
      border-radius: 0;
      border-top: none;
      border-left: none;
      border-right: none;
    }

    span {
      display: inline-block;
      white-space: nowrap;
      padding-left: 5px;
      width: 130px;
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
      &.required {
        background-color: #e3e3e3;
      }
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

    &.required {
      background-color: #e6e6e6;
      border-right: 3px solid #00a1cb;
      &.empty {
        input, textarea, /deep/ input {
          border-color: #f00;
        }
        border-right: 3px solid #f00;
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
    select {
      width: 100%;
      max-width: 370px;
    }
    input[type="checkbox"] {
      margin-top: 8px;
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

  .anamnesis {
    padding: 10px;
  }

  .status-list {
    display: flex;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .mkb10 {
    margin-right: -1px;
    z-index: 0;
  }

  .mkb10 /deep/ .input-group {
    border-radius: 0;
    width: 100%;
  }

  .mkb10 /deep/ input {
    border-radius: 0!important;
  }

  .mkb10 /deep/ ul {
    position: relative;
    width: auto;
    right: -250px;
    font-size: 13px;
    z-index: 1000;
  }

  .mkb10 /deep/ ul li {
    overflow: hidden;
    text-overflow: ellipsis;
    padding: 2px .25rem;
    margin: 0 .2rem;
    a {
      padding: 2px 10px;
    }
  }

  .directions {
    position: relative;
    height: calc(100% - 68px);
    padding-bottom: 34px;
    &.noStat {
      padding-bottom: 0;
    }
    .inner {
      height: 100%;
      overflow-y: auto;
      overflow-x:hidden;
    }
    .stat {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      border-radius: 0;
    }
  }

  .dreg_nex {
    color: #687282;
  }
  .dreg_ex {
    color: #da3b6c;
    text-shadow: 0 0 4px rgba(#da3b6c, .6);
  }
</style>
