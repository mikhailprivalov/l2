<template>
  <modal ref="modal" @close="hide_modal" show-footer="true" white-bg="true"
         max-width="900px" width="100%" marginLeftRight="auto" margin-top>
    <span slot="header">Диспансерный учёт пациента
      <span v-if="!card_data.fio_age">{{card_data.family}} {{card_data.name}} {{card_data.twoname}},
      {{card_data.age}}, карта {{card_data.num}}</span>
      <span v-else>{{card_data.fio_age}}</span>
    </span>
    <div slot="body" style="min-height: 200px;" class="registry-body">
      <table class="table table-bordered table-condensed table-sm-pd"
             style="table-layout: fixed; font-size: 12px; margin-bottom: 0;">
        <colgroup>
          <col width="70" />
          <col width="98" />
          <col />
          <col width="70" />
          <col />
          <col width="90" />
        </colgroup>
        <thead>
          <tr>
            <th>Дата начала</th>
            <th>Дата прекращения</th>
            <th>Диагноз</th>
            <th>Код по МКБ-10</th>
            <th>Врач</th>
            <th>
              <button class="btn btn-primary-nb btn-blue-nb" style="padding-left: 4px"
                      @click="edit(-1)"
                      type="button">Добавить</button>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rows" :class="{stop: !!r.date_end}" :key="r.pk">
            <td>{{r.date_start}}</td>
            <td>{{r.date_end}}</td>
            <td>{{r.illnes}}</td>
            <td>{{r.diagnos}}</td>
            <td>{{r.spec_reg}} {{r.doc_start_reg}}</td>
            <td>
                <button class="btn last btn-blue-nb nbr" type="button"
                        v-tippy="{ placement : 'bottom', arrow: true }"
                        title="030/у" style="margin-left: -1px" @click="print_form_030(r.pk)">
                  <i class="fa fa-print"></i>
                </button>
                <button class="btn last btn-blue-nb nbr" type="button"
                        v-tippy="{ placement : 'bottom', arrow: true }"
                        title="Редактирование" style="margin-left: -1px" @click="edit(r.pk)">
                  <i class="glyphicon glyphicon-pencil"></i>
                </button>
            </td>
          </tr>
        </tbody>
      </table>
      <template v-if="researches_data && researches_data.length > 0">
        <div class="years">
          <div class="year"
               @click="year = y; load_data()"
               :class="{active: y === year}" v-for="y in years" :key="y">
            {{y}}
          </div>
        </div>
        <table class="table table-bordered table-condensed table-sm-pd"
               style="table-layout: fixed; font-size: 12px; margin-top: 0;">
          <colgroup>
            <col width="30" />
            <col />
            <col width="110" />
            <col width="40" v-for="m in monthes" :key="m" />
            <col width="30" />
          </colgroup>
          <thead>
            <tr>
              <th class="cl-td">
                <label v-if="has_assignments" title="Выбор всех назначений" v-tippy="{ placement : 'top', arrow: true }">
                  <input type="checkbox" v-model="all_selected">
                </label>
              </th>
              <th>Обследование (прием)</th>
              <th>МКБ-10<br>кол-во в год</th>
              <th v-for="(m, i) in monthes" :key="`th-${m}`" class="text-center">
                {{m}}<br />
                <a href="#" class="a-under" @click.prevent="fill_column(i)"
                   v-if="researches_data && researches_data.length > 1"
                   title="Заполнить столбец по первой строке" v-tippy="{ placement : 'top', arrow: true }">
                  <i class="fa fa-arrow-circle-down"></i>
                </a>
              </th>
              <th title="Результатов в году" v-tippy="{ placement : 'top', arrow: true }"
                  class="text-center" style="font-size: 14px">
                <i class="fa fa-times-circle-o"></i>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="k in researches_data" :key="`${k.research_pk}`">
              <td class="cl-td">
                <label v-if="k.assign_research_pk" title="Выбор для назначения" v-tippy="{ placement : 'top', arrow: true }">
                  <input type="checkbox" v-model="k.assignment">
                </label>
              </td>
              <td>{{k.research_title}}</td>
              <td>
                <div v-for="d in k.diagnoses_time" :key="`${d.diagnos}_${d.times}`" class="mkb-year">
                  <span>{{d.diagnos}}</span> <span class="year-times">{{d.times}} р. в год</span>
                </div>
              </td>
              <td v-for="(m, i) in monthes" :key="`td-${k.research_pk}-${m}`">
                <input v-model="k.plans[i]" type="text" class="form-control nbr input-cell" maxlength="3"
                       :title="get_date_string(year, i, k.plans[i])"
                       v-tippy="{ placement : 'left', arrow: true, reactive: true, trigger: 'mouseenter focus input' }">
                <div v-if="k.results[i]" class="text-center">
                  <a href="#" @click.prevent="print_results(k.results[i].pk)" class="a-under"
                     title="Печать результата" v-tippy>
                    {{k.results[i].date}}
                  </a>
                </div>
                <div v-else>&nbsp;</div>
              </td>
              <td class="text-center">
                <div style="height: 22px;">&nbsp;</div>
                x{{k.times}}
              </td>
            </tr>
            <tr v-if="assignments.length > 0">
              <td :colspan="4 + monthes.length">
                <button @click="create_directions" class="btn btn-primary-nb btn-blue-nb" type="button">
                  Создать направления по выбранным назначениям
                </button>
              </td>
            </tr>
          </tbody>
        </table>

        <div style="margin: 0 auto 20px auto; width: 200px">
          <button @click="save_plan" class="btn btn-primary-nb btn-blue-nb" type="button">
            Сохранить план
          </button>
        </div>
      </template>
      <div v-else class="text-center">
        <br/>
        <br/>
        Нет данных для построения плана
        <br/>
      </div>

      <modal v-if="edit_pk > -2" ref="modalEdit" @close="hide_edit" show-footer="true" white-bg="true" max-width="710px"
             width="100%" marginLeftRight="auto" margin-top>
        <span slot="header" v-if="edit_pk > -1">Редактор диспансерного учёта</span>
        <span slot="header" v-else>Создание записи диспансерного учёта</span>
        <div slot="body" style="min-height: 200px;padding: 10px" class="registry-body">
          <div class="form-group">
            <label for="de-f3">Дата начала:</label>
            <input class="form-control" type="date" id="de-f3" v-model="edit_data.date_start" :max="td"
                   :readonly="edit_data.close">
          </div>
          <div class="form-group mkb10" style="width: 100%">
            <label>Диагноз в полной форме (код по МКБ и название):</label>
            <MKBFieldForm v-model="edit_data.diagnos" v-if="!edit_data.close" :short="false" />
            <input class="form-control" v-model="edit_data.diagnos" v-else readonly>
          </div>
          <div class="radio-button-object radio-button-groups">
            <label>Диагноз установлен</label>
              <radio-field v-model="is_first_time" :variants="variant_is_first_time" @modified="change_index" fullWidth/>
          </div>
          <div class="radio-button-object radio-button-groups" style="margin-top: 15px; margin-bottom: 15px;">
            <label>Заболевание выявлено при:</label>
            <radio-field v-model="how_identified" :variants="variant_identified" @modified="change_index" fullWidth/>
          </div>
          <div class="checkbox" style="padding-left: 15px;">
            <label>
              <input type="checkbox" v-model="edit_data.close"> прекращён
            </label>
          </div>
          <div class="form-group" v-if="edit_data.close">
            <label for="de-f5">Дата прекращения:</label>
            <input class="form-control" type="date" id="de-f5" v-model="edit_data.date_end" :min="td">
          </div>
          <div class="form-group" v-if="edit_data.close">
            <label for="de-f6">Причина прекращения:</label>
            <input class="form-control" id="de-f6" v-model="edit_data.why_stop">
          </div>

          <div class="checkbox" style="padding-left: 15px;">
            <label>
              <input type="checkbox" v-model="enable_construct"> настройка обследований для диагноза:
            </label>
          </div>
          <div class="form-group">
            <ConfigureDispenseryResearch v-if="enable_construct && edit_data.diagnos" :diagnos_code="edit_data.diagnos"/>
          </div>
        </div>
        <div slot="footer">
          <div class="row">
            <div class="col-xs-4">
              <button @click="hide_edit" class="btn btn-primary-nb btn-blue-nb" type="button">
                Отмена
              </button>
            </div>
            <div class="col-xs-4">
              <button :disabled="!valid_reg" @click="save()" class="btn btn-primary-nb btn-blue-nb" type="button">
                Сохранить
              </button>
            </div>
          </div>
        </div>
      </modal>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-6">
        </div>
        <div class="col-xs-4">
        </div>
        <div class="col-xs-2">
          <button @click="hide_modal" class="btn btn-primary-nb btn-blue-nb" type="button">
            Закрыть
          </button>
        </div>
      </div>
    </div>
  </modal>
</template>

<script>
import api from '@/api';
import moment from 'moment';
import { cloneDeep } from 'lodash';
import ConfigureDispenseryResearch from '@/fields/ConfigureDispenseryResearch.vue';
import Modal from '../ui-cards/Modal.vue';
import * as actions from '../store/action-types';
import MKBFieldForm from '../fields/MKBFieldForm.vue';
import RadioField from '../fields/RadioField.vue';

const years = [];

for (let i = 2020; i <= Number(moment().format('YYYY')) + 2; i++) {
  years.push(i);
}

const monthes = [
  'янв',
  'фев',
  'мар',
  'апр',
  'май',
  'июн',
  'июл',
  'авг',
  'сент',
  'окт',
  'ноя',
  'дек',
];

const weekDays = [
  'понедельник',
  'вторник',
  'среда',
  'четверг',
  'пятница',
  'суббота',
  'воскресенье',
];

export default {
  name: 'd-reg',
  components: {
    Modal, MKBFieldForm, RadioField, ConfigureDispenseryResearch,
  },
  props: {
    card_pk: {
      type: Number,
      required: true,
    },
    card_data: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      td: moment().format('YYYY-MM-DD'),
      message: '<br>',
      rows: [],
      researches_data: [],
      researches_data_def: [],
      year: Number(moment().format('YYYY')),
      monthes,
      years,
      edit_data: {
        date_start: '',
        date_end: '',
        why_stop: '',
        close: false,
        diagnos: '',
        illnes: '',
        time_index: 0,
        identified_index: 0,
      },
      edit_pk: -2,
      all_selected: false,
      lock_changes: false,
      is_first_time: '',
      how_identified: '',
      variant_is_first_time: ['не указано', 'впервые', 'повторно'],
      variant_identified: ['не указано', 'обращении за лечением', 'профилактическом осмотре'],
      enable_construct: false,
    };
  },
  created() {
    this.load_data();
  },
  computed: {
    valid_reg() {
      return this.edit_pk > -2
          && this.edit_data.diagnos.match(/^[A-Z]\d{1,2}(\.\d{1,2})?.*/gm)
          && this.edit_data.date_start !== ''
          && (!this.edit_data.close || this.edit_data.date_end !== '');
    },
    assignments() {
      return this.researches_data.filter(({ assignment }) => assignment).map((rd) => rd.assign_research_pk);
    },
    assignments_diagnoses() {
      return Object.keys(this.researches_data
        .filter(({ assignment }) => assignment)
        .reduce((a, rd) => ({ ...a, ...rd.diagnoses_time.reduce((b, dt) => ({ ...b, [dt.diagnos]: true }), {}) }), {}));
    },
    has_assignments() {
      return this.count_assignments_available > 0;
    },
    count_assignments_available() {
      return this.researches_data.filter((rd) => rd.assign_research_pk).length;
    },
    count_assignments() {
      return this.assignments.length;
    },
    has_all_selected() {
      return this.count_assignments === this.count_assignments_available;
    },
    not_selected() {
      return this.count_assignments === 0;
    },
  },
  watch: {
    count_assignments() {
      this.lock_changes = true;
      if (this.has_all_selected) {
        this.all_selected = true;
      } else if (this.not_selected) {
        this.all_selected = false;
      }
      setTimeout(() => {
        this.lock_changes = false;
      }, 0);
    },
    all_selected() {
      if (!this.lock_changes) {
        for (const row of this.researches_data) {
          if (row.assign_research_pk) {
            row.assignment = this.all_selected;
          }
        }
      }
    },
  },
  methods: {
    get_date_string(year, month, dayOrig) {
      const day = dayOrig.trim();
      if (!day) {
        return 'Нет даты в плане';
      }

      try {
        const dateString = `${year}-${month + 1}-${day}`;
        const date = moment(dateString, 'YYYY-MM-DD');

        if (!Number.isNaN(day) && day < 32 && day > 0 && date.isValid()) {
          return `План: ${day} ${monthes[month]} ${year}, ${weekDays[date.isoWeekday() - 1]}`;
        }
      } catch (e) {
        // pass
      }

      return 'Некорректная дата';
    },
    async edit(pk) {
      if (pk === -1) {
        this.edit_data = {
          date_start: this.td,
          date_end: this.td,
          why_stop: '',
          close: false,
          diagnos: '',
          illnes: '',
          time_index: 0,
          identified_index: 0,
        };
      } else {
        const d = await api('patients/individuals/load-dreg-detail', { pk });
        this.edit_data = {
          ...this.edit_data,
          ...d,
          date_end: d.date_end || this.td,
        };
        this.is_first_time = this.variant_is_first_time[d.time_index];
        this.how_identified = this.variant_identified[d.identified_index];
      }
      this.edit_pk = pk;
    },
    hide_edit() {
      if (this.$refs.modalEdit) {
        this.$refs.modalEdit.$el.style.display = 'none';
      }
      this.edit_pk = -2;
    },
    hide_modal() {
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
      this.$root.$emit('hide_dreg');
    },
    async save_plan() {
      await this.$store.dispatch(actions.INC_LOADING);
      await api('patients/individuals/save-plan-dreg', this, ['card_pk', 'researches_data', 'researches_data_def', 'year']);
      await this.$store.dispatch(actions.DEC_LOADING);
      window.okmessage('План сохранён');
    },
    change_index() {
      this.edit_data.time_index = this.variant_is_first_time.indexOf(this.is_first_time);
      this.edit_data.identified_index = this.variant_identified.indexOf(this.how_identified);
    },
    async save() {
      await this.$store.dispatch(actions.INC_LOADING);
      await api('patients/individuals/save-dreg', { card_pk: this.card_pk, pk: this.edit_pk, data: this.edit_data });
      await this.$store.dispatch(actions.DEC_LOADING);
      window.okmessage('Сохранено');
      this.hide_edit();
      this.load_data();
    },
    load_data() {
      this.$store.dispatch(actions.INC_LOADING);
      api('patients/individuals/load-dreg', this, ['card_pk', 'year']).then(({ rows, researches_data, year }) => {
        this.rows = rows;
        this.researches_data = researches_data;
        this.researches_data_def = cloneDeep(researches_data);
        this.all_selected = false;
        if (researches_data && researches_data.length > 0) {
          window.okmessage(`Загружен ${year} год`);
        }
        this.year = year;
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
      });
    },
    print_form_030(pk) {
      window.open(`/forms/pdf?type=100.04&reg_pk=${pk}&year=2020`);
    },
    print_results(pk) {
      this.$root.$emit('print:results', [pk]);
    },
    fill_column(i) {
      const orig = this.researches_data[0].plans[i];
      for (let j = 1; j < this.researches_data.length; j++) {
        this.researches_data[j].plans[i] = orig;
        this.researches_data[j].plans = [...this.researches_data[j].plans]; // Принудительно делаем перерендер
      }
      window.okmessage(`Столбец "${this.monthes[i]}" заполнен значением "${orig}"`);
    },
    create_directions() {
      this.$root.$emit('generate-directions', {
        type: 'direction',
        card_pk: this.card_pk,
        fin_source_pk: 'ОМС',
        researches: { '-1': this.assignments },
        diagnos: this.assignments_diagnoses.join('; '),
        counts: {},
        comments: {},
        localizations: {},
        service_locations: {},
      });

      for (const row of this.researches_data) {
        if (row.assign_research_pk) {
          row.assignment = false;
        }
      }
      this.all_selected = false;
    },
  },
};
</script>

<style scoped lang="scss">
  .input-cell {
    padding: 3px;
    margin: 0;
    height: 25px;
  }
  select.form-control {
    padding: 0;
    overflow: visible;
  }

  .nonPrior {
    opacity: .7;
    &:hover {
      opacity: 1;
    }
  }

  .prior {
    background-color: rgba(#000, .05);
  }

  .modal-mask {
    align-items: stretch !important;
    justify-content: stretch !important;
  }

  ::v-deep .panel-flt {
    margin: 41px;
    align-self: stretch !important;
    width: 100%;
    display: flex;
    flex-direction: column;
  }

  ::v-deep .panel-body {
    flex: 1;
    padding: 0;
    height: calc(100% - 91px);
    min-height: 200px;
  }

  .form-row {
    width: 100%;
    display: flex;
    border-bottom: 1px solid #434a54;
    &:first-child:not(.nbt-i) {
      border-top: 1px solid #434a54;
    }
    justify-content: stretch;
    .row-t {
      background-color: #AAB2BD;
      padding: 7px 0 0 10px;
      width: 35%;
      flex: 0 35%;
      color: #fff;
    }

    .input-group {
      flex: 0 65%;
    }

    input, .row-v, ::v-deep input {
      background: #fff;
      border: none;
      border-radius: 0 !important;
      width: 65%;
      flex: 0 65%;
      height: 34px;
    }

    &.sm-f {
      .row-t {
        padding: 2px 0 0 10px;
      }
      input, .row-v, ::v-deep input {
        height: 26px;
      }
    }

    ::v-deep input {
      width: 100% !important;
    }
    .row-v {
      padding: 7px 0 0 10px;
    }

    ::v-deep .input-group {
      border-radius: 0;
    }

    ::v-deep ul {
      width: auto;
      font-size: 13px;
    }

    ::v-deep ul li {
      overflow: hidden;
      text-overflow: ellipsis;
      padding: 2px .25rem;
      margin: 0 .2rem;

      a {
        padding: 2px 10px;
      }
    }
  }
  .col-form {
    &.left {
      padding-right: 0!important;

      .row-t, input, .row-v, ::v-deep input {
        border-right: 1px solid #434a54 !important;
      }
    }
    &:not(.left):not(.mid) {
      padding-left: 0!important;
      .row-t {
        border-right: 1px solid #434a54;
      }
    }
  }
  .info-row {
    padding: 7px;
  }

  .individual {
    cursor: pointer;

    &:hover {
      background-color: rgba(0, 0, 0, .15);
    }
  }
  .str ::v-deep .input-group {
    width: 100%;
  }

  .lst {
    margin: 0;
    line-height: 1;
  }

  .mkb10 {
    z-index: 0;
  }

  .mkb10 ::v-deep .input-group {
    width: 100%;
  }

  .mkb10 ::v-deep ul {
    font-size: 13px;
    z-index: 1000;
  }

  .mkb10 ::v-deep ul li {
    overflow: hidden;
    text-overflow: ellipsis;
    padding: 2px .25rem;
    margin: 0 .2rem;
    a {
      padding: 2px 10px;
    }
  }

  tr.stop {
    opacity: .7;
    text-decoration: line-through;
    &:hover {
      opacity: 1;
      text-decoration: none;
    }
  }

  .year-times {
    font-weight: 700;
    font-size: 90%;
    white-space: nowrap;
  }

  .mkb-year {
    color: #000;
    padding: .2em .3em;
    line-height: 1;
    margin-bottom: 2px;
    background-color: rgba(#000, .08);
    border-radius: .25em;
    display: flex;
    justify-content: space-between;
    align-content: center;
    white-space: nowrap;
  }

  .years {
    padding: 18px 10px 9px 10px;
    overflow-x: auto;

    .year {
      cursor: pointer;
      display: inline-block;
      margin-right: 7px;
      padding: 3px;
      border-radius: 3px;
      color: #049372;
      background-color: rgba(#049372, .3);
      transition: all .2s cubic-bezier(.25, .8, .25, 1);

      &.active {
        font-weight: bold;
        background-color: #049372;
        color: #fff;
      }

      &:not(.active):hover {
        box-shadow: 0 7px 14px rgba(#049372, 0.15), 0 5px 5px rgba(#049372, 0.11);
        z-index: 1;
        transform: scale(1.02);
        background-color: rgba(#049372, .4);
      }
    }
  }
</style>
