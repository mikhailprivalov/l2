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
              <th>Профиль</th>
              <td class="cl-td">
                <Treeselect
                  v-model="profileResearch"
                  :multiple="false"
                  :disable-branch-nodes="true"
                  :options="profilesResearch"
                  placeholder="Профиль не выбран"
                  :append-to-body="true"
                  class="treeselect-noborder"
                  :clearable="false"
                  :disabled="isSearchStationar"
                />
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
                  :disabled="isSearchStationar || isProfileResearch"
                />
              </td>
            </tr>
            <tr>
              <th>
                № направления
              </th>
              <td class="x-cell">
                <input
                  v-model.trim="directionNumber"
                  type="text"
                  class="form-control"
                  placeholder="номер"
                  :disabled="isSearchStationar"
                >
              </td>
            </tr>
            <tr>
              <th class="cl-td text-left">
                <label class="mh-34">
                  Дата направления
                  <input
                    v-model="directionCreatedDate"
                    type="checkbox"
                    class="ml-5"
                    :disabled="isSearchStationar || hospCheck"
                  >
                </label>
              </th>
              <td class="cl-td">
                <DateRange
                  v-if="directionCreatedDate"
                  v-model="dateCreateRange"
                  :disabled="isSearchStationar || hospCheck"
                />
              </td>
            </tr>
            <tr>
              <th class="cl-td text-left">
                <label class="mh-34">
                  Дата результата
                  <input
                    v-model="hospCheck"
                    type="checkbox"
                    class="ml-5"
                    :disabled="isSearchStationar || directionCreatedDate"
                  >
                </label>
              </th>
              <td class="cl-td">
                <DateRange
                  v-if="hospCheck"
                  v-model="dateExaminationRange"
                  :disabled="isSearchStationar || directionCreatedDate"
                />
              </td>
            </tr>
            <tr v-if="canSelectHospitals">
              <th class="cl-td text-left">
                <label class="mh-34">
                  Регистрация
                  <input
                    v-model="registerCheck"
                    :disabled="isSearchStationar"
                    type="checkbox"
                    class="ml-5"
                  >
                </label>
              </th>
              <td class="cl-td">
                <DateRange
                  v-if="registerCheck"
                  v-model="dateRegisteredRange"
                  :disabled="isSearchStationar"
                />
              </td>
            </tr>
            <tr v-if="canSelectHospitals">
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
                  :disabled="isSearchStationar"
                />
              </td>
            </tr>
            <tr v-if="canSelectHospitals">
              <th>
                Дата забора
              </th>
              <td class="cl-td">
                <div
                  class="input-group"
                >
                  <input
                    v-model="dateGet"
                    :disabled="isSearchStationar"
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
            <tr v-if="canSelectHospitals">
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
                    :disabled="isSearchStationar"
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
              <th>№ случая</th>
              <td class="x-cell">
                <input
                  v-model.trim="caseNumber"
                  type="text"
                  class="form-control"
                  placeholder="номер"
                  :disabled="isSearchStationar"
                >
              </td>
            </tr>
            <tr>
              <th>
                <label class="mh-34">
                  Текст (и/б)
                  <input
                    v-model="searchStationar"
                    type="checkbox"
                    class="ml-5"
                  >
                </label>
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
            <tr v-if="canSelectHospitals">
              <th>Организация:</th>
              <td class="cl-td">
                <Treeselect
                  v-model="hospitalId"
                  :multiple="false"
                  :disable-branch-nodes="true"
                  class="treeselect-noborder treeselect-wide"
                  :options="hospital_ids"
                  :append-to-body="true"
                  placeholder="По умолчанию"
                  :clearable="false"
                />
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

        <div
          v-if="count > 0"
          class="top-padding"
        >
          <span class="badge badge-primary fons-style">
            Получено строк &mdash; {{ count }}
          </span>
        </div>
      </div>
      <div
        v-if="hasParam && count > 0"
        class="inner"
      >
        <h5>Параметры статистики</h5>
        <Treeselect
          v-model="statisticParam"
          :multiple="false"
          :disable-branch-nodes="true"
          class="treeselect-noborder treeselect-wide"
          :options="statisticParams"
          :append-to-body="true"
          placeholder="Не выбрано"
          :clearable="false"
        />
        <button
          v-if="statisticParam !== -1"
          class="btn btn-blue-nb btn-block"
          type="button"
          @click="genReport"
        >
          Сформировать отчёт
        </button>
      </div>
      <div
        v-if="hasParam && count > 0"
        class="inner"
      >
        <h5>Модель отчета</h5>
        <Treeselect
          v-model="statisticPattern"
          :multiple="false"
          :disable-branch-nodes="true"
          class="treeselect-noborder treeselect-wide"
          :options="statisticPatterns"
          :append-to-body="true"
          placeholder="Не выбрано"
          :clearable="false"
        />
        <button
          v-if="statisticPattern !== -1"
          class="btn btn-blue-nb btn-block"
          type="button"
          @click="genPatternReport"
        >
          Сформировать модель
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
            <col style="width: 120px">
            <col style="width: 160px">
            <col style="width: 300px">
            <col>
            <col style="width: 200px">
          </colgroup>
          <thead>
            <tr>
              <th>Номер</th>
              <th v-if="!isSearchStationar">
                Организация
              </th>
              <th v-else>
                История болезни
              </th>
              <th>Пациент</th>
              <th>Текст</th>
              <th>Статус</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in results"
              :key="r.direction_number"
            >
              <td>
                <a
                  v-if="r.date_confirm"
                  href="#"
                  class="a-under"
                  @click="print(r.direction_number)"
                >
                  {{ r.direction_number }}
                </a>
                <div v-else>
                  {{ r.direction_number }}
                </div>
                <div
                  v-if="r.additional_number"
                  class="additional-number"
                >
                  <i class="fas fa-registered" />{{ r.additional_number }}
                  <br>
                  {{ r.registered_date }}
                </div>
              </td>
              <td v-if="!isSearchStationar">
                {{ r.hosp_title }}
              </td>
              <td v-else>
                <a
                  href="#"
                  class="a-under"
                  @click="load(r.history_num)"
                >
                  И/б {{ r.history_num }}
                </a>
              </td>
              <td>
                {{ r.patient_fio }}, {{ r.patient_sex }}, {{ r.patient_birthday }}, {{ r.patient_age }}
              </td>
              <td>
                {{ r.field_value }}
              </td>
              <td>
                <div v-if="r.date_confirm">
                  <strong class="approved">Утвержден</strong>
                  <br>
                  {{ r.doc_fio }}
                </div>
                <div v-else-if="r.registered_date">
                  <strong class="registered">В работе</strong>
                  <br>
                  {{ r.doc_plan_fio }}
                </div>
                <div v-else-if="r.time_gistology_receive">
                  <span class="received">Материал поступил</span>
                </div>
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
import axios from 'axios';
import * as Cookies from 'es-cookie';

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
      profileResearch: -1,
      profilesResearch: [],
      caseNumber: '',
      directionNumber: '',
      hospCheck: false,
      directionCreatedDate: false,
      dateExaminationRange: [moment().subtract(2, 'month').format('DD.MM.YYYY'), moment().format('DD.MM.YYYY')],
      dateCreateRange: [moment().subtract(2, 'month').format('DD.MM.YYYY'), moment().format('DD.MM.YYYY')],
      registerCheck: false,
      searchStationar: false,
      dateRegisteredRange: [moment().subtract(2, 'month').format('DD.MM.YYYY'), moment().format('DD.MM.YYYY')],
      docConfirm: null,
      usersConfirm: [],
      text: '',
      results: [],
      dateReceive: '',
      dateGet: '',
      count: 0,
      hospital_ids: [{ id: -1, label: 'По умолчанию' }],
      hospitalId: -1,
      statisticParams: [{ id: -1, label: 'Не выбрано' }],
      statisticPatterns: [{ id: -1, label: 'Не выбрано' }],
      statisticParam: -1,
      statisticPattern: -1,
      hasParam: false,
      directionsReport: [],
      link: null,
    };
  },
  async mounted() {
    await this.$store.dispatch(actions.INC_LOADING);
    await this.$api('researches/descriptive-research').then(rows => {
      this.researches = rows;
    });
    await this.$api('researches/profiles-research').then(rows => {
      this.profilesResearch = rows;
    });
    const { users } = await usersPoint.loadUsersByGroup({
      group: [
        'Врач параклиники', 'Врач консультаций', 'Заполнение мониторингов', 'Свидетельство о смерти-доступ',
      ],
    });
    this.usersConfirm = users;

    const { hospitals } = await this.$api('get-all-hospitals');
    this.hospital_ids = [{ id: -1, label: 'По умолчанию' }, ...hospitals];
    await this.$store.dispatch(actions.DEC_LOADING);
  },
  watch: {
    searchStationar() {
      if (this.searchStationar) {
        this.research = -1;
        this.profileResearch = -1;
        this.caseNumber = '';
        this.directionNumber = '';
        this.hospCheck = false;
        this.directionCreatedDate = false;
        this.registerCheck = false;
        this.docConfirm = null;
        this.dateReceive = '';
        this.dateGet = '';
      }
    },
    profileResearch() {
      if (this.profileResearch > 0) {
        this.research = -1;
      }
    },
  },
})
export default class SearchPage extends Vue {
  year: number;

  research: number;

  profileResearch: number;

  hospitalId: number;

  statisticParam: number;

  statisticPattern: number;

  count: number;

  researches: any[];

  directionsReport: any[];

  caseNumber: string;

  directionNumber: string;

  hospCheck: boolean;

  directionCreatedDate: boolean;

  dateExaminationRange: string[];

  dateCreateRange: string[];

  registerCheck: boolean;

  searchStationar: boolean;

  hasParam: boolean;

  dateRegisteredRange: string[];

  docConfirm: null | number;

  text: string;

  results: any[];

  dateGet: string | null;

  dateReceive: string | null;

  statisticParams: any[];

  statisticPatterns: any[];

  link: string | null;

  get isValid() {
    return this.searchStationar || (!!this.year && !!this.research && this.research !== -1)
        || (!!this.year && this.profileResearch !== -1);
  }

  get isSearchStationar() {
    return this.searchStationar;
  }

  get isProfileResearch() {
    return this.profileResearch !== -1;
  }

  get userGroups() {
    return this.$store.getters.user_data.groups || [];
  }

  get canSelectHospitals() {
    const groups = this.userGroups;
    return groups.includes('Направления-все МО');
  }

  async search() {
    await this.$store.dispatch(actions.INC_LOADING);
    const data = {
      year_period: this.year,
      research_id: this.research,
      profile_research_id: this.profileResearch,
      case_number: this.caseNumber,
      directionNumber: this.directionNumber,
      hospitalId: this.hospitalId,
      dateExaminationStart: this.hospCheck ? formatDate(this.dateExaminationRange[0]) : null,
      dateExaminationEnd: this.hospCheck ? formatDate(this.dateExaminationRange[1]) : null,
      dateCreateStart: this.directionCreatedDate ? formatDate(this.dateCreateRange[0]) : null,
      dateCreateEnd: this.directionCreatedDate ? formatDate(this.dateCreateRange[1]) : null,
      docConfirm: this.docConfirm,
      dateRegistredStart: this.registerCheck ? formatDate(this.dateRegisteredRange[0]) : null,
      dateRegistredEnd: this.registerCheck ? formatDate(this.dateRegisteredRange[1]) : null,
      dateGet: this.dateGet,
      dateReceive: this.dateReceive,
      finalText: this.text,
      searchStationar: this.searchStationar,
    };
    const dataRows = await this.$api('/search-param', data);
    this.results = dataRows.rows || [];
    this.count = dataRows.count || 0;
    if (this.count > 0) {
      this.statisticParamsSerch();
      this.statisticPatternsSearch();
      this.directionsReport = [];
      for (const element of this.results) {
        this.directionsReport.push(element.direction_number);
      }
    }
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  async statisticParamsSerch() {
    await this.$store.dispatch(actions.INC_LOADING);
    const dataRows = await this.$api('/statistic-params-search');
    this.statisticParams = [{ id: -1, label: 'Не выбрано' }, ...dataRows.rows];
    this.hasParam = dataRows.hasParam;
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  async statisticPatternsSearch() {
    await this.$store.dispatch(actions.INC_LOADING);
    const dataRows = await this.$api('/statistic-pattern-search');
    this.statisticPatterns = [{ id: -1, label: 'Не выбрано' }, ...dataRows.rows];
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  genReport() {
    axios({
      method: 'post',
      url: '/api/reports/statistic-params-search',
      data: {
        directions: this.directionsReport,
        param: this.statisticParam,
        researchId: this.research,
      },
      responseType: 'blob',
      headers: {
        'X-CSRFToken': Cookies.get('csrftoken'),
      },
    })
      .then((response) => {
        const blob = new Blob([response.data], { type: 'application/ms-excel' });
        const downloadUrl = window.URL.createObjectURL(blob);
        let filename = '';
        const disposition = response.headers['content-disposition'];
        if (disposition && disposition.indexOf('attachment') !== -1) {
          const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
          const matches = filenameRegex.exec(disposition);
          filename = matches?.[1].replace(/['"]/g, '') || '';
        }
        const a = document.createElement('a');
        if (typeof a.download === 'undefined') {
          window.location.href = downloadUrl;
        } else {
          a.href = downloadUrl;
          a.download = filename;
          document.body.appendChild(a);
          a.click();
        }
      })
      .catch((error) => {
        // eslint-disable-next-line no-console
        console.error(error);
        this.$root.$emit('msg', 'error', 'Сохранить данные в виде XLSX не удалось');
      });
  }

  async genPatternReport() {
    await this.$store.dispatch(actions.INC_LOADING);
    const directions = this.results.map(el => (el.direction_number));
    const data = await this.$api('reports/xlsx-model', { directions, idModel: this.statisticPattern });
    this.link = data.link;
    if (this.link) {
      window.open(`/statistic/${this.link}?file=${encodeURIComponent(JSON.stringify(data.results))}`, '_blank');
    }
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  print(pk) {
    this.$root.$emit('print:results', [pk]);
  }

  // eslint-disable-next-line class-methods-use-this
  load(historyNum) {
    window.open(`/ui/stationar#{%22pk%22:${historyNum},%22every%22:false}`, '_blank');
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

.top-padding {
  padding-top: 15px;
}

.fons-style {
  font-size: 16px;
  font-weight: normal;
}

.approved {
  color: #049372;
}

.registered {
  color: #3BAFDA;
}

.received {
  color: #932a04
}

.additional-number {
  color: #046d93;
  font-size: 15px;
}

</style>

<style>
.pagination {
  margin-top: 0 !important;
}
</style>
