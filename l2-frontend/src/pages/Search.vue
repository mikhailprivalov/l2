<template>
  <div class="root">
    <div class="left-bar">
      <div class="inner">
        <h5>Фильтры</h5>

        <table class="table table-bordered table-condensed">
          <colgroup>
            <col style="width: 140px">
            <col>
          </colgroup>
          <tbody>
            <tr>
              <th>Год</th>
              <td class="x-cell">
                <input
                  v-model="year"
                  type="number"
                  class="form-control"
                  min="2018"
                  max="2100"
                  placeholder="год"
                >
              </td>
            </tr>
            <tr>
              <th>Услуга</th>
              <td class="cl-td">
                <Treeselect
                  v-model="research"
                  :multiple="false"
                  :disable-branch-nodes="true"
                  :options="researches"
                  placeholder="Услуга не выбрана"
                  :append-to-body="true"
                  class="treeselect-noborder"
                  :clearable="false"
                />
              </td>
            </tr>
            <tr>
              <th>Номер случая</th>
              <td class="x-cell">
                <input
                  v-model.trim="caseNumber"
                  type="text"
                  class="form-control"
                  placeholder="номер"
                >
              </td>
            </tr>
            <tr>
              <th>
                Номер истории
              </th>
              <td class="x-cell">
                <input
                  v-model.trim="hospNumber"
                  type="text"
                  class="form-control"
                  placeholder="номер"
                >
              </td>
            </tr>
            <tr>
              <th class="cl-td text-left">
                <label class="mh-34">
                  Дата выписки
                  <input
                    v-model="hospCheck"
                    type="checkbox"
                    class="ml-5"
                  >
                </label>
              </th>
              <td class="cl-td">
                <DateRange
                  v-if="hospCheck"
                  v-model="dateExaminationRange"
                />
              </td>
            </tr>
            <tr>
              <th class="cl-td text-left">
                <label class="mh-34">
                  Регистрация
                  <input
                    v-model="registerCheck"
                    type="checkbox"
                    class="ml-5"
                  >
                </label>
              </th>
              <td class="cl-td">
                <DateRange
                  v-if="registerCheck"
                  v-model="dateRegisteredRange"
                />
              </td>
            </tr>
            <tr>
              <th>
                <div class="mh-34">
                  Исполнитель
                </div>
              </th>
              <td class="cl-td">
                <Treeselect
                  v-model="docConfirm"
                  class="treeselect-noborder"
                  :multiple="false"
                  :disable-branch-nodes="true"
                  :options="usersConfirm"
                  placeholder="Пользователь не выбран"
                  :clearable="true"
                />
              </td>
            </tr>
            <tr>
              <th>
                Дата забора
              </th>
              <td class="cl-td">
                <div
                  class="input-group"
                >
                  <input
                    v-model="dateGet"
                    type="date"
                    class="form-control nba"
                  >
                  <span class="input-group-btn">
                    <button
                      class="btn btn-blue-nb"
                      type="button"
                      @click="dateGet = ''"
                    ><i class="fa fa-times" /></button>
                  </span>
                </div>
              </td>
            </tr>
            <tr>
              <th>
                Дата получения
              </th>
              <td class="cl-td">
                <div
                  class="input-group"
                >
                  <input
                    v-model="dateReceive"
                    type="date"
                    class="form-control nba"
                  >
                  <span class="input-group-btn">
                    <button
                      class="btn btn-blue-nb"
                      type="button"
                      @click="dateReceive = ''"
                    ><i class="fa fa-times" /></button>
                  </span>
                </div>
              </td>
            </tr>
            <tr>
              <th>
                Текст
              </th>
              <td class="x-cell">
                <input
                  v-model="text"
                  type="text"
                  class="form-control"
                  placeholder="текст в протоколе"
                >
              </td>
            </tr>
          </tbody>
        </table>

        <button
          class="btn btn-blue-nb btn-block"
          :disabled="!isValid"
          type="button"
          @click="search"
        >
          Поиск
        </button>
      </div>
    </div>
    <div class="right-content">
      <div class="inner">
        <table
          class="table-bordered table table-hover"
          style="table-layout: fixed"
        >
          <colgroup>
            <col style="width: 80px">
            <col style="width: 200px">
            <col style="width: 300px">
            <col>
            <col style="width: 200px">
          </colgroup>
          <thead>
            <tr>
              <th>Номер</th>
              <th>Организция</th>
              <th>Пациент</th>
              <th>Текст</th>
              <th>Исполнитель</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in results"
              :key="r.direction_number"
              class="cursor-pointer"
              @click="print(r.direction_number)"
            >
              <td>
                {{ r.direction_number }}
              </td>
              <td>
                {{ r.hosp_title }}
              </td>
              <td>
                {{ r.patient_fio }}, {{ r.patient_sex }}, {{ r.patient_birthday }}, {{ r.patient_age }}
              </td>
              <td>
                {{ r.field_value }}
              </td>
              <td>
                {{ r.doc_fio }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import moment from 'moment';
import Vue from 'vue';
import Component from 'vue-class-component';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import Paginate from 'vuejs-paginate';

import * as actions from '@/store/action-types';
import usersPoint from '@/api/user-point';
import RadioFieldById from '@/fields/RadioFieldById.vue';
import DateFieldNav2 from '@/fields/DateFieldNav2.vue';
import DoctorProfileTreeselectField from '@/fields/DoctorProfileTreeselectField.vue';
import DateRange from '@/ui-cards/DateRange.vue';

const formatDate = (d: string) => moment(d, 'DD.MM.YYYY').format('YYYY-MM-DD');

@Component({
  components: {
    Treeselect,
    RadioFieldById,
    DateFieldNav2,
    DateRange,
    DoctorProfileTreeselectField,
    Paginate,
  },
  data() {
    return {
      year: moment().year(),
      research: -1,
      researches: [],
      caseNumber: '',
      hospNumber: '',
      hospCheck: false,
      dateExaminationRange: [moment().subtract(2, 'month').format('DD.MM.YYYY'), moment().format('DD.MM.YYYY')],
      registerCheck: false,
      dateRegisteredRange: [moment().subtract(2, 'month').format('DD.MM.YYYY'), moment().format('DD.MM.YYYY')],
      docConfirm: null,
      usersConfirm: [],
      text: '',
      results: [],
      dateReceive: '',
      dateGet: '',
    };
  },
  async mounted() {
    await this.$store.dispatch(actions.INC_LOADING);
    await this.$api('researches/descriptive-research').then(rows => {
      this.researches = rows;
    });
    const { users } = await usersPoint.loadUsersByGroup({
      group: [
        'Врач параклиники', 'Врач консультаций', 'Заполнение мониторингов', 'Свидетельство о смерти-доступ',
      ],
    });
    this.usersConfirm = users;
    await this.$store.dispatch(actions.DEC_LOADING);
  },
})
export default class SearchPage extends Vue {
  year: number;

  research: number;

  researches: any[];

  caseNumber: string;

  hospNumber: string;

  hospCheck: boolean;

  dateExaminationRange: string[];

  registerCheck: boolean;

  dateRegisteredRange: string[];

  docConfirm: null | number;

  text: string;

  results: any[];

  dateGet: string | null;

  dateReceive: string | null;

  get isValid() {
    return !!this.year && !!this.research && this.research !== -1;
  }

  async search() {
    await this.$store.dispatch(actions.INC_LOADING);
    const data = {
      year_period: this.year,
      research_id: this.research,
      case_number: this.caseNumber,
      hospital_id: this.hospNumber,
      dateExaminationStart: this.hospCheck ? formatDate(this.dateExaminationRange[0]) : null,
      dateExaminationEnd: this.hospCheck ? formatDate(this.dateExaminationRange[1]) : null,
      docConfirm: this.docConfirm,
      dateRegistredStart: this.registerCheck ? formatDate(this.dateRegisteredRange[0]) : null,
      dateRegistredEnd: this.registerCheck ? formatDate(this.dateRegisteredRange[1]) : null,
      dateGet: this.dateGet,
      dateReceive: this.dateReceive,
      finalText: this.text,
    };
    const { rows } = await this.$api('/search-param', data);
    this.results = rows || [];

    await this.$store.dispatch(actions.DEC_LOADING);
  }

  print(pk) {
    this.$root.$emit('print:results', [pk]);
  }
}
</script>

<style lang="scss" scoped>
$sidebar-width: 400px;

.root {
  position: absolute;
  top: 36px;
  left: 0;
  right: 0;
  bottom: 0;

  overflow-x: hidden;
  overflow-y: hidden;
}

.left-bar, .right-content {
  position: absolute;
  top: 0;
  bottom: 0;

  overflow-x: visible;
  overflow-y: auto;

  .inner {
    padding: 10px;
  }
}

.left-bar {
  left: 0;
  right: calc(100% - #{$sidebar-width});

  background: #f2f2f2;

  h5 {
    margin-top: 0;
  }

  table {
    table-layout: fixed;

    .x-cell {
      .form-control {
        border: none;
      }
    }
  }
}

.right-content {
  right: 0;
  left: $sidebar-width;

  border-left: 1px solid #b1b1b1;
  background: #fff;
}

.mh-34 {
  min-height: 24px;
}

.ml-5 {
  margin-left: 5px !important;
}

.cl-td.text-left {
  text-align: left !important;

  label {
    justify-content: start;
    padding: 5px;
  }
}
</style>

<style>
.pagination {
  margin-top: 0 !important;
}
</style>
