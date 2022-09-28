<template>
  <Modal
    ref="modal"
    show-footer="true"
    white-bg="true"
    max-width="900px"
    width="100%"
    margin-left-right="auto"
    margin-top
    @close="hide_modal"
  >
    <span
      slot="header"
    >Диспансерный учёт пациента
      <span
        v-if="!card_data.fio_age"
      >{{ card_data.family }} {{ card_data.name }} {{ card_data.twoname }}, {{ card_data.age }}, карта {{ card_data.num }}</span>
      <span v-else>{{ card_data.fio_age }}</span>
    </span>
    <div
      slot="body"
      class="registry-body"
    >
      <table class="table table-bordered table-condensed table-sm-pd dreg-table">
        <colgroup>
          <col width="70">
          <col width="98">
          <col>
          <col width="70">
          <col>
          <col width="90">
        </colgroup>
        <thead>
          <tr>
            <th>Дата начала</th>
            <th>Дата прекращения</th>
            <th>Диагноз</th>
            <th>Код по МКБ-10</th>
            <th>Врач</th>
            <th>
              <button
                class="btn btn-primary-nb btn-blue-nb pl4"
                type="button"
                @click="edit(-1)"
              >
                Добавить
              </button>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="r in rows"
            :key="r.pk"
            :class="{ stop: !!r.date_end }"
          >
            <td>{{ r.date_start }}</td>
            <td>{{ r.date_end }}</td>
            <td>{{ r.illnes }}</td>
            <td>{{ r.diagnos }}</td>
            <td>{{ r.spec_reg }} {{ r.doc_start_reg }}</td>
            <td>
              <button
                v-tippy="{ placement: 'bottom', arrow: true }"
                class="btn last btn-blue-nb nbr ml-1"
                type="button"
                title="030/у"
                @click="print_form_030(r.pk)"
              >
                <i class="fa fa-print" />
              </button>
              <button
                v-tippy="{ placement: 'bottom', arrow: true }"
                class="btn last btn-blue-nb nbr ml-1"
                type="button"
                title="Редактирование"
                @click="edit(r.pk)"
              >
                <i class="glyphicon glyphicon-pencil" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <template v-if="researches_data && researches_data.length > 0">
        <table class="table table-bordered table-condensed table-sm-pd dreg-table">
          <colgroup>
            <col>
            <col width="110">
            <col
              v-for="m in monthes"
              :key="m"
              width="40"
            >
            <col width="30">
          </colgroup>
          <thead>
            <tr>
              <th
                :colspan="3 + monthes.length"
                class="text-center"
              >
                План диспансерного учёта
              </th>
            </tr>
            <tr>
              <td :colspan="3 + monthes.length">
                <div class="years">
                  <div
                    v-for="y in years"
                    :key="y"
                    class="year"
                    :class="{ active: y === year }"
                    @click="load_data(false, y)"
                  >
                    {{ y }}
                  </div>
                </div>
              </td>
            </tr>
            <tr>
              <th>Обследование (прием)</th>
              <th>МКБ-10<br>кол-во в год</th>
              <th
                v-for="(m, i) in monthes"
                :key="`th-${m}`"
                class="text-center"
              >
                {{ m }}<br>
                <a
                  v-if="researches_data && researches_data.length > 1"
                  v-tippy="{ placement: 'top', arrow: true }"
                  href="#"
                  class="a-under"
                  title="Заполнить столбец по первой строке"
                  @click.prevent="fill_column(i)"
                >
                  <i class="fa fa-arrow-circle-down" />
                </a>
              </th>
              <th
                v-tippy="{ placement: 'top', arrow: true }"
                title="Результатов в году"
                class="text-center fs14"
              >
                <i class="fa fa-times-circle-o" />
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="k in researches_data"
              :key="`${k.research_pk}`"
            >
              <td>
                <ResearchPickById
                  :pk="k.research_pk"
                  :selected-researches="selectedResearchesLocal"
                  :kk="kk"
                />
              </td>
              <td>
                <div
                  v-for="d in k.diagnoses_time"
                  :key="`${d.diagnos}_${d.times}`"
                  class="mkb-year"
                >
                  <span>{{ d.diagnos }}</span> <span class="year-times">{{ d.times }} р. в год</span>
                </div>
              </td>
              <td
                v-for="(m, i) in monthes"
                :key="`td-${k.research_pk}-${m}`"
              >
                <input
                  v-model="k.plans[i]"
                  v-tippy="{ placement: 'left', arrow: true, reactive: true, trigger: 'mouseenter focus input' }"
                  type="text"
                  class="form-control nbr input-cell"
                  maxlength="3"
                  :title="get_date_string(year, i, k.plans[i])"
                >
                <div
                  v-if="k.results[i]"
                  class="text-center"
                >
                  <a
                    v-tippy
                    href="#"
                    class="a-under"
                    title="Печать результата"
                    @click.prevent="print_results(k.results[i].pk)"
                  >
                    {{ k.results[i].date }}
                  </a>
                </div>
                <div v-else>
&nbsp;
                </div>
              </td>
              <td class="text-center">
                <div class="nbsp-height">
&nbsp;
                </div>
                x{{ k.times }}
              </td>
            </tr>
            <tr>
              <td :colspan="3 + monthes.length">
                <button
                  class="btn btn-primary-nb btn-blue-nb btn-sm"
                  type="button"
                  @click="save_plan"
                >
                  Сохранить план
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </template>
      <div
        v-else
        class="text-center empty-dreg"
      >
        Нет данных для построения плана по диагнозам
      </div>

      <ScreeningDisplay
        :selected-researches="selectedResearchesLocal"
        :card-pk="card_pk"
        :kk="kk"
      />

      <div
        v-if="extendedResearches && card_pk && parent_iss"
        class="selected-researches"
      >
        <SelectedResearches
          :kk="kk"
          :researches="selectedResearchesLocal"
          :base="bases_obj[card_data.base]"
          :main_diagnosis="card_data.main_diagnosis"
          :card_pk="card_pk"
          :selected_card="card_data"
          :initial_fin="finId"
          :parent_iss="parent_iss"
          style="border-top: 1px solid #eaeaea"
        />
      </div>

      <div class="dreg-flt">
        <Modal
          v-if="edit_pk > -2"
          ref="modalEdit"
          show-footer="true"
          white-bg="true"
          max-width="710px"
          width="100%"
          margin-left-right="auto"
          margin-top
          @close="hide_edit"
        >
          <span
            v-if="edit_pk > -1"
            slot="header"
          >Редактор диспансерного учёта</span>
          <span
            v-else
            slot="header"
          >Создание записи диспансерного учёта</span>
          <div
            slot="body"
            class="registry-body p10"
          >
            <div class="form-group">
              <label for="de-f3">Дата начала:</label>
              <input
                id="de-f3"
                v-model="edit_data.date_start"
                class="form-control"
                type="date"
                :max="td"
                :readonly="edit_data.close"
              >
            </div>
            <div class="form-group mkb10 w100">
              <label>Диагноз в полной форме (код по МКБ и название):</label>
              <MKBFieldForm
                v-if="!edit_data.close"
                v-model="edit_data.diagnos"
                :short="false"
              />
              <input
                v-else
                v-model="edit_data.diagnos"
                class="form-control"
                readonly
              >
            </div>
            <div class="radio-button-object radio-button-groups">
              <label>Диагноз установлен</label>
              <RadioField
                v-model="is_first_time"
                :variants="variant_is_first_time"
                full-width
                @modified="change_index"
              />
            </div>
            <div class="radio-button-object radio-button-groups mtb15">
              <label>Заболевание выявлено при:</label>
              <RadioField
                v-model="how_identified"
                :variants="variant_identified"
                full-width
                @modified="change_index"
              />
            </div>
            <div class="checkbox pl15">
              <label> <input
                v-model="edit_data.close"
                type="checkbox"
              > прекращён </label>
            </div>
            <div
              v-if="edit_data.close"
              class="form-group"
            >
              <label for="de-f5">Дата прекращения:</label>
              <input
                id="de-f5"
                v-model="edit_data.date_end"
                class="form-control"
                type="date"
                :min="td"
              >
            </div>
            <div
              v-if="edit_data.close"
              class="form-group"
            >
              <label for="de-f6">Причина прекращения:</label>
              <input
                id="de-f6"
                v-model="edit_data.why_stop"
                class="form-control"
              >
            </div>
            <div class="radio-button-object radio-button-groups">
              <label>Настройка плана обследования</label>
              <RadioField
                v-model="typePlan"
                :variants="variant_construct"
                full-width
                @modified="change_index"
              />
            </div>
            <div class="form-group">
              <ConfigureDispenseryResearch
                v-if="typePlan === 'Глобальный план' && edit_data.diagnos || typePlan === 'Индивидуальный план'"
                :diagnos_code="edit_data.diagnos"
                :card_pk="card_pk"
                :type_plan="typePlan"
                :unique_research_pks="uniqueResearchPks"
              />
            </div>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-4">
                <button
                  class="btn btn-primary-nb btn-blue-nb"
                  type="button"
                  @click="hide_edit"
                >
                  Отмена
                </button>
              </div>
              <div class="col-xs-4">
                <button
                  :disabled="!valid_reg"
                  class="btn btn-primary-nb btn-blue-nb"
                  type="button"
                  @click="save()"
                >
                  Сохранить
                </button>
              </div>
            </div>
          </div>
        </Modal>
      </div>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-6" />
        <div class="col-xs-4" />
        <div class="col-xs-2">
          <button
            class="btn btn-primary-nb btn-blue-nb"
            type="button"
            @click="hide_modal"
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script lang="ts">
import moment from 'moment';
import { cloneDeep } from 'lodash';
import { mapGetters } from 'vuex';

import * as actions from '@/store/action-types';
import ConfigureDispenseryResearch from '@/fields/ConfigureDispenseryResearch.vue';
import ResearchPickById from '@/ui-cards/ResearchPickById.vue';
import Modal from '@/ui-cards/Modal.vue';
import MKBFieldForm from '@/fields/MKBFieldForm.vue';
import RadioField from '@/fields/RadioField.vue';

const years = [];

for (let i = 2020; i <= Number(moment().format('YYYY')) + 2; i++) {
  years.push(i);
}

const monthes = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сент', 'окт', 'ноя', 'дек'];

const weekDays = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье'];

const KK = '-dreg';

export default {
  name: 'DReg',
  components: {
    ResearchPickById,
    Modal,
    MKBFieldForm,
    RadioField,
    ConfigureDispenseryResearch,
    ScreeningDisplay: () => import('@/ui-cards/ScreeningDisplay.vue'),
    SelectedResearches: () => import('@/ui-cards/SelectedResearches.vue'),
  },
  props: {
    card_pk: {
      type: Number,
      required: true,
    },
    parent_iss: {
      type: Number,
      required: false,
    },
    finId: {
      type: Number,
      required: false,
    },
    card_data: {
      type: Object,
      required: true,
    },
    selectedResearches: {
      type: Array,
      required: false,
    },
  },
  data() {
    return {
      td: moment().format('YYYY-MM-DD'),
      message: '<br>',
      rows: [],
      uniqueResearchPks: [],
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
      variant_construct: ['не указано', 'Глобальный план', 'Индивидуальный план'],
      typePlan: '',
      enable_construct: false,
      enableIndividualConstruct: false,
      selectedResearchesDReg: [],
    };
  },
  computed: {
    ...mapGetters({
      bases: 'bases',
    }),
    bases_obj() {
      return this.bases.reduce(
        (a, b) => ({
          ...a,
          [b.pk]: b,
        }),
        {},
      );
    },
    selectedResearchesLocal() {
      return this.selectedResearches || this.selectedResearchesDReg;
    },
    extendedResearches() {
      return !this.selectedResearches;
    },
    kk() {
      return this.extendedResearches ? KK : '';
    },
    valid_reg() {
      return (
        this.edit_pk > -2
        && this.edit_data.diagnos.match(/^[A-Z]\d{1,2}(\.\d{1,2})?.*/gm)
        && this.edit_data.date_start !== ''
        && (!this.edit_data.close || this.edit_data.date_end !== '')
      );
    },
    assignments() {
      return this.researches_data.filter(({ assignment }) => assignment).map((rd) => rd.assign_research_pk);
    },
    assignments_diagnoses() {
      return Object.keys(
        this.researches_data
          .filter(({ assignment }) => assignment)
          .reduce((a, rd) => ({ ...a, ...rd.diagnoses_time.reduce((b, dt) => ({ ...b, [dt.diagnos]: true }), {}) }), {}),
      );
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
  created() {
    this.load_data(true);
  },
  mounted() {
    this.$root.$on(`researches-picker:deselect${KK}`, (pk) => {
      this.selectedResearchesDReg = this.selectedResearchesDReg.filter((k) => k !== pk);
    });
    this.$root.$on(`researches-picker:deselect_department${KK}`, (_, pks) => {
      this.selectedResearchesDReg = this.selectedResearchesDReg.filter((k) => !pks.includes(k));
    });
    this.$root.$on(`researches-picker:deselect_all${KK}`, () => {
      this.selectedResearchesDReg = [];
    });
    this.$root.$on(`researches-picker:directions_created${KK}`, () => {
      this.$root.$emit('researches-picker:directions_createdcd');
    });
    this.$root.$on(`researches-picker:add_research${KK}`, (pk) => {
      this.selectedResearchesDReg = !this.selectedResearchesDReg.includes(pk)
        ? [...this.selectedResearchesDReg, pk]
        : this.selectedResearchesDReg;
    });
  },
  methods: {
    get_date_string(year, month, dayOrig) {
      if (!dayOrig.trim()) {
        return 'Нет даты в плане';
      }

      const day = Number(dayOrig.trim());

      try {
        const dateString = `${year}-${month + 1}-${day}`;
        const date = moment(dateString, 'YYYY-MM-DD');

        if (day < 32 && day > 0 && date.isValid()) {
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
        const d = await this.$api('patients/individuals/load-dreg-detail', { pk });
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
      await this.$api('patients/individuals/save-plan-dreg', this, ['card_pk', 'researches_data', 'researches_data_def', 'year']);
      await this.$store.dispatch(actions.DEC_LOADING);
      this.$root.$emit('msg', 'ok', 'План сохранён');
    },
    change_index() {
      this.edit_data.time_index = this.variant_is_first_time.indexOf(this.is_first_time);
      this.edit_data.identified_index = this.variant_identified.indexOf(this.how_identified);
    },
    async save() {
      await this.$store.dispatch(actions.INC_LOADING);
      await this.$api('patients/individuals/save-dreg', { card_pk: this.card_pk, pk: this.edit_pk, data: this.edit_data });
      await this.$store.dispatch(actions.DEC_LOADING);
      this.$root.$emit('msg', 'ok', 'Сохранено');
      this.hide_edit();
      this.load_data(true);
    },
    load_data(isInitial = false, newYear = null) {
      if (newYear) {
        this.year = newYear;
      }
      this.$store.dispatch(actions.INC_LOADING);
      this.$api('patients/individuals/load-dreg', this, ['card_pk', 'year'])
        .then(({
          rows, researches_data: researchesData, year, unique_research_pk: uniqueResearchPks,
        }) => {
          this.rows = rows;
          this.researches_data = researchesData;
          this.researches_data_def = cloneDeep(researchesData);
          this.all_selected = false;
          if (researchesData && researchesData.length > 0 && !isInitial) {
            this.$root.$emit('msg', 'ok', `Загружен ${year} год`);
          }
          this.year = year;
          this.uniqueResearchPks = uniqueResearchPks;
        })
        .finally(() => {
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
      this.$root.$emit('msg', 'ok', `Столбец "${this.monthes[i]}" заполнен значением "${orig}"`);
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
  opacity: 0.7;

  &:hover {
    opacity: 1;
  }
}

.prior {
  background-color: rgba(#000, 0.05);
}

.modal-mask {
  align-items: stretch !important;
  justify-content: stretch !important;
}

.dreg-flt ::v-deep .panel-flt {
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
    background-color: #aab2bd;
    padding: 7px 0 0 10px;
    width: 35%;
    flex: 0 35%;
    color: #fff;
  }

  .input-group {
    flex: 0 65%;
  }

  input,
  .row-v,
  ::v-deep input {
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

    input,
    .row-v,
    ::v-deep input {
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
    padding: 2px 0.25rem;
    margin: 0 0.2rem;

    a {
      padding: 2px 10px;
    }
  }
}

.col-form {
  &.left {
    padding-right: 0 !important;

    .row-t,
    input,
    .row-v,
    ::v-deep input {
      border-right: 1px solid #434a54 !important;
    }
  }

  &:not(.left):not(.mid) {
    padding-left: 0 !important;

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
    background-color: rgba(0, 0, 0, 0.15);
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
  padding: 2px 0.25rem;
  margin: 0 0.2rem;

  a {
    padding: 2px 10px;
  }
}

tr.stop {
  opacity: 0.7;
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
  padding: 0.2em 0.3em;
  line-height: 1;
  margin-bottom: 2px;
  background-color: rgba(#000, 0.08);
  border-radius: 0.25em;
  display: flex;
  justify-content: space-between;
  align-content: center;
  white-space: nowrap;
}

.years {
  overflow-x: auto;

  .year {
    cursor: pointer;
    display: inline-block;
    margin-right: 7px;
    padding: 3px;
    border-radius: 3px;
    color: #049372;
    background-color: rgba(#049372, 0.3);
    transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);

    &.active {
      font-weight: bold;
      background-color: #049372;
      color: #fff;
    }

    &:not(.active):hover {
      box-shadow: 0 7px 14px rgba(#049372, 0.15), 0 5px 5px rgba(#049372, 0.11);
      z-index: 1;
      transform: scale(1.02);
      background-color: rgba(#049372, 0.4);
    }
  }
}

.dreg-table {
  table-layout: fixed;
  font-size: 12px;
  margin-top: 0;
}

.nbsp-height {
  height: 22px;
}

.registry-body {
  min-height: 200px;
}

.pl4 {
  padding-left: 4px;
}

.ml-1 {
  margin-left: -1px;
}

.fs14 {
  font-size: 14px;
}

.p10 {
  padding: 10px;
}

.w100 {
  width: 100%;
}

.pl15 {
  padding-left: 15px;
}

.mtb15 {
  margin-top: 15px;
  margin-bottom: 15px;
}

.selected-researches {
  height: 350px;
}
</style>
