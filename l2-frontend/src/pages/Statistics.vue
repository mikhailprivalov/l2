<template>
  <div class="root">
    <div class="categories">
      <div class="col-header">
        Разделы статистики
      </div>
      <div class="col-inner">
        <div
          v-for="c in categories"
          :key="c.id"
          class="col-picker"
          :class="selectedCategory === c.id && 'col-active'"
          @click="selectedCategory = c.id"
        >
          {{ c.label }}
        </div>
      </div>
    </div>
    <div class="reports">
      <div class="col-header">
        Отчёты
      </div>
      <div
        v-if="!currentCategory"
        class="col-inner text-center"
      >
        не выбрано
      </div>
      <div
        v-else
        class="col-inner"
      >
        <div
          v-for="(r, id) in categoryReport"
          :key="id"
          class="col-picker"
          :class="selectedReport === id && 'col-active'"
          @click="selectedReport = id"
        >
          {{ r.title }}
        </div>
      </div>
    </div>
    <div
      :key="selectedReport"
      class="settings"
    >
      <div class="col-header">
        Настройка
      </div>
      <div
        v-if="!currentReport"
        class="col-inner text-center"
      >
        не выбрано
      </div>
      <div
        v-else
        class="col-inner"
      >
        <div class="col-form">
          <LaboratoryPicker
            v-if="checkReportParam(PARAMS_TYPES.LABORATORY, PARAMS_TYPES.LABORATORY_WITH_ALL)"
            :key="PARAMS_TYPES.LABORATORY_WITH_ALL"
            v-model="values.lab"
            :with-all="checkReportParam(PARAMS_TYPES.LABORATORY_WITH_ALL)"
          />

          <div
            v-if="checkReportParam(PARAMS_TYPES.USERS)"
            :key="PARAMS_TYPES.USERS"
            class="input-group"
          >
            <span class="input-group-addon">Пользователи:</span>
            <treeselect
              v-model="values.users"
              class="treeselect-noborder treeselect-wide"
              :multiple="false"
              :disable-branch-nodes="true"
              :options="users"
              placeholder="Пользователи не выбраны"
            />
          </div>

          <div
            v-if="checkReportParam(PARAMS_TYPES.USER_OR_DEP)"
            :key="`${PARAMS_TYPES.USER_OR_DEP}_user`"
            class="input-group"
          >
            <span class="input-group-addon">Пользователь:</span>
            <treeselect
              v-model="values.user"
              class="treeselect-noborder treeselect-wide"
              :multiple="false"
              :disable-branch-nodes="true"
              :options="users"
              :clearable="true"
              placeholder="Пользователь не выбан"
              :disabled="values.dep"
            />
          </div>

          <div
            v-if="checkReportParam(PARAMS_TYPES.USER_OR_DEP)"
            class="row-v"
          >
            или
          </div>

          <div
            v-if="checkReportParam(PARAMS_TYPES.USER_OR_DEP)"
            :key="`${PARAMS_TYPES.USER_OR_DEP}_dep`"
            class="input-group"
          >
            <span class="input-group-addon">Подразделение:</span>
            <treeselect
              v-model="values.dep"
              class="treeselect-noborder treeselect-wide"
              :multiple="false"
              :disable-branch-nodes="true"
              :options="deps"
              :clearable="true"
              placeholder="Подразделение не выбано"
              :disabled="values.user"
            />
          </div>

          <div
            v-if="checkReportParam(PARAMS_TYPES.RESEARCH)"
            :key="PARAMS_TYPES.RESEARCH"
            class="row-v"
          >
            <div class="row-v-header">
              Услуга:
            </div>
            <div class="researches-wrapper">
              <ResearchesPicker
                v-model="values.research"
                autoselect="none"
                :just_search="true"
                :hidetemplates="true"
                :oneselect="true"
              />
            </div>
          </div>
          <div
            v-if="checkReportParam(PARAMS_TYPES.RESEARCH_CREATE)"
            :key="PARAMS_TYPES.RESEARCH_CREATE"
            class="row-v"
          >
            <div class="row-v-header">
              Услуга:
            </div>
            <div class="researches-wrapper">
              <ResearchesPicker
                v-model="values.research"
                autoselect="none"
                :just_search="true"
                :hidetemplates="true"
                :oneselect="false"
              />
            </div>
          </div>
          <div
            v-if="checkReportParam(PARAMS_TYPES.FIN_SOURCE)"
            :key="PARAMS_TYPES.FIN_SOURCE"
            class="input-group"
          >
            <span class="input-group-addon">Источник финансирования:</span>
            <select
              v-model="values.finSource"
              class="form-control"
            >
              <option :value="-1">
                не выбрано
              </option>
              <optgroup
                v-for="b in bases"
                :key="b.pk"
                :label="b.title"
              >
                <option
                  v-for="f in b.fin_sources.filter(x => !x.hide)"
                  :key="f.pk"
                  :value="f.pk"
                >
                  {{ b.title }} – {{ f.title }}
                </option>
              </optgroup>
            </select>
          </div>
          <div
            v-if="checkReportParam(PARAMS_TYPES.COMPANY)"
            :key="PARAMS_TYPES.COMPANY"
            class="input-group"
          >
            <span class="input-group-addon">Контрагент:</span>
            <treeselect
              v-if="!l2_company_statistic_async_search"
              v-model="values.company"
              class="treeselect-noborder treeselect-wide"
              :multiple="false"
              :disable-branch-nodes="true"
              :options="companies"
              :clearable="true"
              placeholder="Компания не выбана"
            />
            <Treeselect
              v-else
              v-model="values.company"
              :multiple="false"
              :disable-branch-nodes="true"
              class="treeselect-wide treeselect-nbr"
              :async="true"
              :append-to-body="true"
              :clearable="true"
              :z-index="10001"
              placeholder="Укажите организацию"
              :load-options="loadCompaniesAsyncSearch"
              loading-text="Загрузка"
              no-results-text="Не найдено"
              search-prompt-text="Начните писать для поиска"
              :cache-options="false"
              open-direction="top"
              :open-on-focus="true"
            >
              <div
                slot="value-label"
                slot-scope="{ node }"
              >
                {{ node.raw.label || card.work_place_db_title }}
              </div>
            </Treeselect>
          </div>
          <div
            v-if="checkReportParam(PARAMS_TYPES.RESEARCH_SETS)"
            :key="PARAMS_TYPES.RESEARCH_SETS"
            class="input-group"
          >
            <span class="input-group-addon">Набор услуг:</span>
            <treeselect
              v-model="values.researchSet"
              class="treeselect-noborder treeselect-wide"
              :multiple="false"
              :disable-branch-nodes="true"
              :options="researchSets"
              :clearable="true"
              placeholder="Набор услуг для отчета"
            />
          </div>
          <div
            v-if="checkReportParam(PARAMS_TYPES.TYPE_DEPARTMENT)"
            :key="PARAMS_TYPES.TYPE_DEPARTMENT"
            class="input-group"
          >
            <span class="input-group-addon">Тип подразделения:</span>
            <treeselect
              v-model="values.typeDepartment"
              class="treeselect-noborder treeselect-wide"
              :multiple="false"
              :disable-branch-nodes="true"
              :options="typeDepartments"
              :clearable="true"
              placeholder="Тип подразделения"
            />
          </div>
          <div
            v-if="checkReportParam(PARAMS_TYPES.MONTH_YEAR)"
            :key="PARAMS_TYPES.MONTH_YEAR"
            class="input-group"
          >
            <span class="input-group-addon">Год</span>
            <input
              v-model.number="values.year"
              type="number"
              min="2020"
              max="3000"
              class="form-control"
            >
            <span class="input-group-addon">Месяц</span>
            <select
              v-model="values.month"
              class="form-control"
            >
              <option :value="1">
                Январь
              </option>
              <option :value="2">
                Февраль
              </option>
              <option :value="3">
                Март
              </option>
              <option :value="4">
                Апрель
              </option>
              <option :value="5">
                Май
              </option>
              <option :value="6">
                Июнь
              </option>
              <option :value="7">
                Июль
              </option>
              <option :value="8">
                Август
              </option>
              <option :value="9">
                Сентябрь
              </option>
              <option :value="10">
                Октябрь
              </option>
              <option :value="11">
                Ноябрь
              </option>
              <option :value="12">
                Декабрь
              </option>
            </select>
          </div>

          <DatePicker
            v-if="checkReportParam(PARAMS_TYPES.DATE_RANGE)"
            :key="PARAMS_TYPES.DATE_RANGE"
            v-model="values.dateRange"
            mode="date"
            :masks="masks"
            is-range
            :max-date="new Date()"
            :rows="2"
            :step="1"
          >
            <template #default="{ inputValue, inputEvents }">
              <div class="input-group">
                <span class="input-group-addon">Дата:</span>
                <input
                  class="form-control"
                  :value="inputValue.start"
                  v-on="inputEvents.start"
                >
                <span
                  class="input-group-addon"
                  style="background-color: #fff;color: #000; height: 34px"
                >&mdash;</span>
                <input
                  class="form-control"
                  :value="inputValue.end"
                  v-on="inputEvents.end"
                >
              </div>
            </template>
          </DatePicker>

          <div
            v-if="checkReportParam(PARAMS_TYPES.PERIOD_DATE)"
            :key="PARAMS_TYPES.PERIOD_DATE"
            class="row-v"
          >
            <DateSelector
              :date_type.sync="values.dateType"
              :values.sync="values.dateValues"
            />
          </div>
          <div v-if="checkReportParam(PARAMS_TYPES.LOAD_FILE)">
            <LoadFile
              title-button="Загрузить из файла"
              file-filter="XLSX"
              :research-set="values.researchSet"
              tag="div"
            />
          </div>
          <div
            v-if="titleReportStattalonFields.includes(currentReport.title)"
            class="input-group"
          >
            <span class="input-group-addon">Цель:</span>
            <treeselect
              v-model="values.purposes"
              class="treeselect-noborder treeselect-wide"
              :multiple="true"
              :disable-branch-nodes="true"
              :options="purposes"
              placeholder="Цели не выбраны"
            />
          </div>
          <div
            v-if="titleReportStattalonFields.includes(currentReport.title)"
            class="input-group"
          >
            <span class="input-group-addon">Результат:</span>
            <treeselect
              v-model="values.resultTreatment"
              class="treeselect-noborder treeselect-wide"
              :multiple="true"
              :disable-branch-nodes="true"
              :options="resultTreatment"
              placeholder="Результат обращения"
            />
          </div>
          <div
            v-if="checkReportParam(PARAMS_TYPES.SPECIAL_FIELDS)"
            class="checkbox"
          >
            <label>
              <input
                v-model="values.specialFields"
                type="checkbox"
              > Настройки из протокола
            </label>
            <span class="mediacl-exam-padding">
              <label>
                <input
                  v-model="values.medicalExam"
                  type="checkbox"
                > По дате осмотра
              </label>
            </span>
            <span class="mediacl-exam-padding">
              <label>
                <input
                  v-model="values.isLabResult"
                  type="checkbox"
                > Результаты лаборатории
              </label>
            </span>
          </div>
          <div
            v-if="checkReportParam(PARAMS_TYPES.BY_CREATE_DIRECTION)"
            class="checkbox"
          >
            <label>
              <input
                v-model="values.byCreateDirection"
                type="checkbox"
              > По дате создания
            </label>
          </div>
          <a
            v-if="reportUrl && !checkReportParam(PARAMS_TYPES.LOAD_FILE)"
            class="btn btn-blue-nb"
            type="button"
            :href="reportUrl"
            target="_blank"
          >
            Сформировать отчёт
          </a>
          <div v-else-if="dateRangeInvalid && !unlimitPeridStatistic ">
            <strong>Диапазон дат должен быть не больше двух месяцев</strong>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import moment from 'moment';
import _ from 'lodash';
// @ts-ignore
import DatePicker from 'v-calendar/src/components/DatePicker.vue';
import Treeselect, { ASYNC_SEARCH } from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import LaboratoryPicker from '@/fields/LaboratoryPicker.vue';
import * as actions from '@/store/action-types';
import usersPoint from '@/api/user-point';
import ResearchesPicker from '@/ui-cards/ResearchesPicker.vue';
import LoadFile from '@/ui-cards/LoadFile.vue';
import DateSelector from '@/fields/DateSelector.vue';

const PARAMS_TYPES = {
  DATE_RANGE: 'DATE_RANGE',
  LABORATORY: 'LABORATORY',
  LABORATORY_WITH_ALL: 'LABORATORY_WITH_ALL',
  PERIOD_DATE: 'PERIOD_DATE',
  USERS: 'USERS',
  USER_OR_DEP: 'USER_OR_DEP',
  FIN_SOURCE: 'FIN_SOURCE',
  RESEARCH_SETS: 'RESEARCH_SETS',
  LOAD_FILE: 'LOAD_FILE',
  RESEARCH: 'RESEARCH',
  RESEARCH_CREATE: 'RESEARCH_CREATE',
  COMPANY: 'COMPANY',
  MONTH_YEAR: 'MONTH_YEAR',
  SPECIAL_FIELDS: 'SPECIAL_FIELDS',
  TYPE_DEPARTMENT: 'TYPE_DEPARTMENT',
  BY_CREATE_DIRECTION: 'BY_CREATE_DIRECTION',
};

const STATS_CATEGORIES = {
  labs: {
    title: 'Лаборатории',
    groups: ['Просмотр статистики', 'Врач-лаборант'],
    reports: {
      researches: {
        groups: ['Просмотр статистики', 'Врач-лаборант'],
        title: 'Выполнено исследований',
        params: [PARAMS_TYPES.DATE_RANGE, PARAMS_TYPES.LABORATORY_WITH_ALL],
        url: '/statistic/xls?type=lab&pk=<lab>&date-start=<date-start>&date-end=<date-end>',
      },
      executors: {
        groups: ['Просмотр статистики', 'Врач-лаборант'],
        title: 'Исполнители',
        params: [PARAMS_TYPES.DATE_RANGE, PARAMS_TYPES.LABORATORY],
        url: '/statistic/xls?type=lab-staff&pk=<lab>&date-start=<date-start>&date-end=<date-end>',
      },
      tubes: {
        groups: ['Просмотр статистики', 'Врач-лаборант'],
        title: 'Принято ёмкостей',
        params: [PARAMS_TYPES.DATE_RANGE, PARAMS_TYPES.LABORATORY],
        url: '/statistic/xls?type=lab-receive&pk=<lab>&date-start=<date-start>&date-end=<date-end>',
      },
    },
  },
  materialGet: {
    title: 'Забор биоматериала',
    groups: ['Статистика-забор биоматериала'],
    reports: {
      executors: {
        groups: ['Статистика-забор биоматериала'],
        title: 'Заборщики биоматериала',
        params: [PARAMS_TYPES.PERIOD_DATE, PARAMS_TYPES.USERS],
        url: '/statistic/xls?type=journal-get-material&users=<users>&date_type=<date-type>&values=<date-values>',
      },
    },
  },
  researches: {
    title: 'Оказанные услуги',
    groups: ['Просмотр статистики', 'Свидетельство о смерти-доступ', 'Статистика-статталоны', 'Статистика-посещения',
      'Статистика-по услуге'],
    reports: {
      executors: {
        title: 'По врачу (нагрузка) – статталоны',
        groups: ['Статистика-статталоны'],
        params: [PARAMS_TYPES.PERIOD_DATE, PARAMS_TYPES.USER_OR_DEP, PARAMS_TYPES.FIN_SOURCE],
        url: [
          '/statistic/xls?type=statistics-tickets-print&user=<user>',
          '&department=<dep>&date_type=<date-type>&date_values=<date-values>&fin=<fin-source>',
        ].join(''),
      },
      visits: {
        groups: ['Статистика-посещения'],
        title: 'Посещения',
        params: [PARAMS_TYPES.DATE_RANGE],
        url: '/statistic/xls?type=statistics-passed&date-start=<date-start>&date-end=<date-end>',
      },
      research: {
        groups: ['Статистика-по услуге', 'Свидетельство о смерти-доступ'],
        title: 'По услуге (результаты)',
        params: [PARAMS_TYPES.PERIOD_DATE, PARAMS_TYPES.RESEARCH, PARAMS_TYPES.SPECIAL_FIELDS, PARAMS_TYPES.DATE_RANGE],
        url: '/statistic/xls?type=statistics-research&date_type=<date-type>&date_values=<date-values>&research=<research>&'
          + 'purposes=<purposes>&special-fields=<special-fields>&medical-exam=<medical-exam>'
          + '&date-start=<date-start>&date-end=<date-end>'
          + '&is-lab-result=<is-lab-result>',
      },
      researchCreate: {
        groups: ['Статистика-по услуге', 'Свидетельство о смерти-доступ'],
        title: 'По услуге (выписано)',
        params: [PARAMS_TYPES.RESEARCH_CREATE, PARAMS_TYPES.DATE_RANGE, PARAMS_TYPES.USERS],
        url: '/statistic/xls?type=statistics-create-research&research=<research>&date-start=<date-start>&date-end=<date-end>'
            + '&users=<users>',
      },
      dispanserization: {
        groups: ['Статистика-по услуге', 'Свидетельство о смерти-доступ'],
        title: 'Диспансеризация',
        params: [PARAMS_TYPES.DATE_RANGE],
        url: '/statistic/xls?type=statistics-dispanserization&date-start=<date-start>&date-end=<date-end>',
      },
      expertise: {
        groups: ['Статистика-экспертиза'],
        title: 'Экспертиза стационара',
        params: [PARAMS_TYPES.DATE_RANGE],
        url: '/statistic/xls?type=statistics-hosp-expertise&date-start=<date-start>&date-end=<date-end>',
      },
    },
  },
  prof: {
    title: 'Профосмотры (своды)',
    groups: ['Статистика-профосмотры'],
    reports: {
      contragents: {
        groups: ['Статистика-профосмотры'],
        title: 'Контрагенты',
        params: [PARAMS_TYPES.DATE_RANGE, PARAMS_TYPES.COMPANY],
        url: '/forms/pdf?type=200.01&company=<company>&date1=<date-start>&date2=<date-end>',
      },
      consolidate: {
        groups: ['Статистика-профосмотры'],
        title: 'Сводный',
        params: [PARAMS_TYPES.COMPANY, PARAMS_TYPES.FIN_SOURCE, PARAMS_TYPES.RESEARCH_SETS, PARAMS_TYPES.DATE_RANGE],
        url: '/statistic/xls?type=statistics-consolidate&fin=<fin-source>&date-start=<date-start>&date-end=<date-end>&'
            + 'company=<company>&research-set=<research-set>',
      },
      registryProfit: {
        groups: ['Статистика-реестр начислений'],
        title: 'Реестр начислений',
        params: [PARAMS_TYPES.FIN_SOURCE, PARAMS_TYPES.DATE_RANGE],
        url: '/statistic/xls?type=statistics-registry-profit&fin=<fin-source>&date-start=<date-start>&date-end=<date-end>',
      },
      typeDepartments: {
        groups: ['Статистика-профосмотры'],
        title: 'По подразделениям',
        params: [PARAMS_TYPES.FIN_SOURCE, PARAMS_TYPES.TYPE_DEPARTMENT, PARAMS_TYPES.DATE_RANGE],
        url: '/statistic/xls?type=consolidate-type-department&fin=<fin-source>&date-start=<date-start>&date-end=<date-end>&'
            + 'type-department=<type-department>',
      },
      patinetExamSetResearch: {
        groups: ['Статистика-профосмотры'],
        title: 'По пациентам из Excel',
        params: [PARAMS_TYPES.RESEARCH_SETS, PARAMS_TYPES.LOAD_FILE],
        url: '/statistic/xls?type=consolidate-type-department&fin=<fin-source>&date-start=<date-start>&date-end=<date-end>&'
            + 'type-department=<type-department>',
      },
    },
  },
  screening: {
    title: 'Скрининг',
    groups: ['Статистика скрининга'],
    reports: {
      screening: {
        groups: ['Статистика-скрининг'],
        title: 'Отчёт по скринингу',
        params: [PARAMS_TYPES.MONTH_YEAR],
        url: '/statistic/screening?month=<month>&year=<year>',
      },
    },
  },
  common: {
    title: 'Общая статистика',
    groups: ['Статистика-вакцинация', 'Статистика-онкоподозрение'],
    reports: {
      vac: {
        groups: ['Статистика-вакцинация'],
        title: 'Вакцинация',
        params: [PARAMS_TYPES.DATE_RANGE],
        url: '/statistic/xls?type=vac&pk=0&date-start=<date-start>&date-end=<date-end>',
      },
      onco: {
        groups: ['Статистика-онкоподозрение'],
        title: 'Онкоподозрение',
        params: [PARAMS_TYPES.DATE_RANGE],
        url: '/statistic/xls?type=statistics-onco&date-start=<date-start>&date-end=<date-end>',
      },
    },
  },
  covid19: {
    title: 'covid19',
    groups: ['Врач консультаций', 'Просмотр статистики', 'Свидетельство о смерти-доступ', 'Статистика-статталоны',
      'Статистика-посещения', 'Статистика-по услуге'],
    reports: {
      who_call: {
        title: 'Позвонить пациенту',
        groups: ['Врач консультаций', 'Просмотр статистики'],
        params: [PARAMS_TYPES.PERIOD_DATE],
        url: '/statistic/xls?type=call-patient&date_type=<date-type>&date_values=<date-values>',
      },
      get_biomaterial: {
        groups: ['Врач консультаций', 'Просмотр статистики'],
        title: 'Мазок взять',
        params: [PARAMS_TYPES.PERIOD_DATE],
        url: '/statistic/xls?type=swab-covidt&date_type=<date-type>&date_values=<date-values>',
      },
      cert_not_work: {
        groups: ['Врач консультаций', 'Просмотр статистики'],
        title: 'Больничный оформить',
        params: [PARAMS_TYPES.PERIOD_DATE],
        url: '/statistic/xls?type=cert-not-workt&date_type=<date-type>&date_values=<date-values>',
      },
    },
  },
  dispensary: {
    title: 'Д-учет',
    groups: ['Врач консультаций', 'Просмотр статистики'],
    reports: {
      disp: {
        groups: ['Врач консультаций', 'Просмотр статистики'],
        title: 'План помесячно',
        params: [PARAMS_TYPES.MONTH_YEAR],
        url: '/statistic/xls?type=disp-plan&month=<month>&year=<year>',
      },
      registered: {
        groups: ['Врач консультаций', 'Просмотр статистики'],
        title: 'Стоит на учете',
        params: [PARAMS_TYPES.PERIOD_DATE],
        url: '/statistic/xls?type=disp-registered&date_type=<date-type>&date_values=<date-values>',
      },
    },
  },
  partners: {
    title: 'Контрагенты',
    groups: ['Статистика-контрагент-заказы'],
    reports: {
      partnerCreateDirection: {
        groups: ['Статистика-контрагент-заказы'],
        title: 'Заказы',
        params: [PARAMS_TYPES.DATE_RANGE, PARAMS_TYPES.PERIOD_DATE, PARAMS_TYPES.BY_CREATE_DIRECTION],
        url: '/statistic/xls?type=statistics-corp-create&date_type=<date-type>&date_values=<date-values>'
            + '&date-start=<date-start>&date-end=<date-end>&by-create-direction=<by-create-direction>',
      },
    },
  },
};

const getVaues = () => ({
  lab: null,
  dateRange: {
    start: new Date(),
    end: new Date(),
  },
  dateType: null,
  dateValues: null,
  users: [],
  finSource: -1,
  researchSet: null,
  typeDepartment: null,
  depByType: null,
  user: null,
  dep: null,
  research: null,
  company: null,
  month: moment().month() + 1,
  year: moment().year(),
  purposes: [],
  resultTreatment: [],
  specialFields: false,
  medicalExam: false,
  isLabResult: false,
  byCreateDirection: false,
});

const formatDate = (date: Date) => moment(date).format('DD.MM.YYYY');
const jsonv = data => encodeURIComponent(JSON.stringify(data));

@Component({
  components: {
    LoadFile,
    LaboratoryPicker,
    DatePicker,
    Treeselect,
    DateSelector,
    ResearchesPicker,
  },
  data() {
    return {
      STATS_CATEGORIES,
      PARAMS_TYPES,
      selectedCategory: null,
      selectedReport: null,
      values: getVaues(),
      masks: {
        iso: 'DD.MM.YYYY',
        data: ['DD.MM.YYYY'],
        input: ['DD.MM.YYYY'],
      },
      users: [],
      companies: [],
      researchSets: [],
      typeDepartments: [],
      disabled_categories: [],
      disabled_reports: [],
      unlimit_period_statistic_groups: [],
      purposes: [],
      specialFields: false,
      medicalExam: false,
      isLabResult: false,
      byCreateDirection: false,
      resultTreatment: [],
      titleReportStattalonFields: [],
      titleReportAllFinSourceNeed: [],
    };
  },
  watch: {
    selectedCategory() {
      this.selectedReport = null;
      if (Object.keys(this.currentCategory?.reports || {}).length === 1) {
        // eslint-disable-next-line prefer-destructuring
        this.selectedReport = Object.keys(this.currentCategory.reports)[0];
      }
    },
    selectedReport() {
      this.values = getVaues();
      setTimeout(() => window.$('.col-form .selectpicker').selectpicker(), 10);
    },
  },
  mounted() {
    this.loadUsers();
    this.loadCompanies();
    this.loadResearchSets();
    this.loadTypeDepartments();
    this.loadPurposes();
    this.loadResultTreatment();
    this.loadTitleReportStattalonFields();
    this.get_disabled_categories();
    this.get_disabled_reports();
    this.getUnlimitPeriodStatisticGroups();
  },
})
export default class Statistics extends Vue {
  STATS_CATEGORIES: typeof STATS_CATEGORIES;

  PARAMS_TYPES: typeof PARAMS_TYPES;

  selectedCategory: string | null;

  selectedReport: string | number | null;

  values: any;

  masks: any;

  users: any[];

  companies: any[];

  researchSets: any[];

  typeDepartments: any[];

  purposes: any[];

  specialFields: boolean;

  medicalExam: boolean;

  byCreateDirection: boolean;

  isLabResult: boolean;

  resultTreatment: any[];

  titleReportStattalonFields: any[];

  disabled_categories: any[];

  disabled_reports: any[];

  unlimit_period_statistic_groups: any[];

  research: number | null;

  titleReportAllFinSourceNeed: any[];

  get userGroups() {
    return this.$store.getters.user_data.groups || [];
  }

  get unlimitPeridStatistic() {
    for (const g of this.$store.getters.user_data.groups || []) {
      if (this.unlimit_period_statistic_groups.includes(g)) {
        return true;
      }
    }
    return false;
  }

  async loadUsers() {
    await this.$store.dispatch(actions.INC_LOADING);
    const { users } = await usersPoint.loadUsersByGroup({ group: '*' });
    this.users = users;
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  async loadCompaniesAsyncSearch({ action, searchQuery, callback }) {
    if (action === ASYNC_SEARCH) {
      const { data } = await this.$api(`/companies-find?query=${searchQuery}`);
      callback(
        null,
        data.map(d => ({ id: `${d.id}`, label: `${d.title}` })),
      );
    }
  }

  get deps() {
    return this.users.map(d => ({ id: d.id, label: d.label }));
  }

  async loadCompanies() {
    await this.$store.dispatch(actions.INC_LOADING);
    const { rows } = await this.$api('companies');
    this.companies = rows;
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  async loadResearchSets() {
    await this.$store.dispatch(actions.INC_LOADING);
    const { data } = await this.$api('/get-research-sets');
    this.researchSets = data;
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  async loadTypeDepartments() {
    await this.$store.dispatch(actions.INC_LOADING);
    const { data } = await this.$api('/get-type-departments');
    this.typeDepartments = data;
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  async loadPurposes() {
    await this.$store.dispatch(actions.INC_LOADING);
    const { rows } = await this.$api('purposes');
    this.purposes = rows;
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  async loadResultTreatment() {
    await this.$store.dispatch(actions.INC_LOADING);
    const { rows } = await this.$api('result-treatment');
    this.resultTreatment = rows;
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  async loadTitleReportStattalonFields() {
    await this.$store.dispatch(actions.INC_LOADING);
    const rows = await this.$api('title-report-filter-stattalon-fields');
    this.titleReportStattalonFields = rows.hasStattalonFilter;
    this.titleReportAllFinSourceNeed = rows.allFinSource;
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  get categories() {
    return Object.keys(this.STATS_CATEGORIES)
      .filter(id => this.STATS_CATEGORIES[id].groups.some(g => this.userGroups.includes(g)
        && !this.disabled_categories.includes(this.STATS_CATEGORIES[id].title)))
      .map(id => ({ id, label: this.STATS_CATEGORIES[id].title }));
  }

  get l2_company_statistic_async_search() {
    return this.$store.getters.modules.l2_company_statistic_async_search;
  }

  get categoryReport() {
    return Object.fromEntries(
      Object.keys(this.currentCategory.reports)
        .filter(id => this.currentCategory.reports[id].groups.some(g => this.userGroups.includes(g))
          && !this.disabled_reports.includes(`${this.currentCategory.title}-${this.currentCategory.reports[id].title}`))
        .map(id => [id, this.currentCategory.reports[id]]),
    );
  }

  get currentCategory() {
    if (!this.selectedCategory || !this.STATS_CATEGORIES[this.selectedCategory]) {
      return null;
    }

    return this.STATS_CATEGORIES[this.selectedCategory];
  }

  get currentReport() {
    if (!this.selectedReport || !this.currentCategory?.reports[this.selectedReport]) {
      return null;
    }

    return this.currentCategory.reports[this.selectedReport];
  }

  makeBaseWithAllSource(base) {
    if (this.titleReportAllFinSourceNeed.includes(this.currentReport.title)) {
      return { ...base, fin_sources: [...base.fin_sources, { pk: -100, title: 'Все', default_diagnos: '' }] };
    }
    return { ...base };
  }

  get bases() {
    const basesUpdate = this.$store.getters.bases.map(base => this.makeBaseWithAllSource(base));
    return (basesUpdate || []).filter(b => !b.hide && b.internal_type);
  }

  checkReportParam(...params) {
    return this.currentReport?.params.some(p => params.includes(p));
  }

  get reportUrl() {
    if (this.dateRangeInvalid) {
      return null;
    }

    let { url } = this.currentReport;

    for (const p of this.currentReport.params) {
      if ([this.PARAMS_TYPES.LABORATORY, this.PARAMS_TYPES.LABORATORY_WITH_ALL].includes(p)) {
        if (_.isNil(this.values.lab)) {
          return null;
        }

        url = url.replace('<lab>', this.values.lab);
      }

      if (this.PARAMS_TYPES.DATE_RANGE === p) {
        if (!this.values.dateRange?.start || !this.values.dateRange?.end) {
          return null;
        }

        url = url.replace('<date-start>', formatDate(this.values.dateRange.start));
        url = url.replace('<date-end>', formatDate(this.values.dateRange.end));
      }

      if (this.PARAMS_TYPES.USERS === p) {
        if (this.values.users?.length === 0) {
          return null;
        }

        url = url.replace('<users>', jsonv(this.values.users));
      }

      if (this.PARAMS_TYPES.PERIOD_DATE === p) {
        if (!this.values.dateType || !this.values.dateValues) {
          return null;
        }

        url = url.replace('<date-type>', this.values.dateType);
        url = url.replace('<date-values>', jsonv(this.values.dateValues));
      }

      if (this.PARAMS_TYPES.USER_OR_DEP === p) {
        if (!this.values.user && !this.values.dep) {
          return null;
        }

        url = url.replace('<user>', this.values.user || -1);
        url = url.replace('<dep>', this.values.dep || -1);
      }

      if (this.PARAMS_TYPES.FIN_SOURCE === p) {
        if (this.values.finSource === -1) {
          return null;
        }
        url = url.replace('<fin-source>', this.values.finSource);
      }

      if (this.PARAMS_TYPES.RESEARCH_SETS === p) {
        if (_.isNil(this.values.researchSet)) {
          url = url.replace('<research-set>', -1);
        }
        url = url.replace('<research-set>', this.values.researchSet);
      }

      if (this.PARAMS_TYPES.TYPE_DEPARTMENT === p) {
        url = url.replace('<type-department>', this.values.typeDepartment);
      }

      if (this.PARAMS_TYPES.RESEARCH === p) {
        if (_.isNil(this.values.research)) {
          return null;
        }

        url = url.replace('<research>', this.values.research);
        url = url.replace('<special-fields>', this.values.specialFields);
        url = url.replace('<medical-exam>', this.values.medicalExam);
        url = url.replace('<is-lab-result>', this.values.isLabResult);
        if (this.values.purposes.length > 0) {
          url = url.replace('<purposes>', this.values.purposes);
        } else {
          url = url.replace('<purposes>', -1);
        }
      }

      if (this.PARAMS_TYPES.RESEARCH_CREATE === p) {
        if (_.isNil(this.values.research)) {
          return null;
        }

        url = url.replace('<research>', this.values.research);
        url = url.replace('<special-fields>', this.values.specialFields);
        url = url.replace('<medical-exam>', this.values.medicalExam);
        url = url.replace('<is-lab-result>', this.values.isLabResult);
        if (this.values.purposes.length > 0) {
          url = url.replace('<purposes>', this.values.purposes);
        } else {
          url = url.replace('<purposes>', -1);
        }
      }

      if (this.PARAMS_TYPES.COMPANY === p) {
        if (_.isNil(this.values.company)) {
          url = url.replace('<company>', -1);
        }

        url = url.replace('<company>', this.values.company);
      }

      if (this.PARAMS_TYPES.BY_CREATE_DIRECTION === p) {
        if (_.isNil(this.values.byCreateDirection)) {
          url = url.replace('<by-create-direction>', false);
        }
        url = url.replace('<by-create-direction>', this.values.byCreateDirection);
      }

      if (this.PARAMS_TYPES.MONTH_YEAR === p) {
        if (!this.values.year) {
          return null;
        }

        url = url.replace('<month>', this.values.month);
        url = url.replace('<year>', this.values.year);
      }
    }

    return url;
  }

  get dateRangeInvalid() {
    if (this.unlimitPeridStatistic) {
      return false;
    }
    if (
      this.currentReport?.params.includes(this.PARAMS_TYPES.DATE_RANGE)
      && this.values.dateRange.start
      && this.values.dateRange.end
    ) {
      const a = moment(this.values.dateRange.start);
      const b = moment(this.values.dateRange.end);
      const diff = b.diff(a, 'months', true);

      if (diff > 2) {
        return true;
      }
    }
    return false;
  }

  async get_disabled_categories() {
    const resultData = await this.$api('disabled-categories');
    this.disabled_categories = resultData.rows;
  }

  async get_disabled_reports() {
    const resultData = await this.$api('disabled-reports');
    this.disabled_reports = resultData.rows;
  }

  async getUnlimitPeriodStatisticGroups() {
    const resultData = await this.$api('unlimit-period-statistic-groups');
    this.unlimit_period_statistic_groups = resultData.rows;
  }
}
</script>

<style lang="scss" scoped>
$colwidths: 300px;

.root {
  position: absolute;
  top: 36px;
  left: 0;
  right: 0;
  bottom: 0;

  overflow-x: hidden;
  overflow-y: hidden;

  .categories,
  .reports,
  .settings {
    position: absolute;
    top: 0;
    bottom: 0;

    .col-header {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 34px;
      line-height: 33px;
      border-bottom: 1px solid #ccc;
      text-align: center;
      background: linear-gradient(to bottom, rgba(0, 0, 0, 0.001) 0%, rgba(0, 0, 0, 0.1) 100%);
    }

    .col-inner {
      position: absolute;
      top: 34px;
      left: 0;
      right: 0;
      bottom: 0;
      overflow-x: hidden;
      overflow-y: auto;
      padding: 5px;
    }
  }

  .categories,
  .reports {
    width: $colwidths;

    .col-header::after {
      content: '';
      top: 0;
      bottom: 0;
      right: -16px;
      width: 0;
      height: 0;
      border-top: 17px solid transparent;
      border-bottom: 17px solid transparent;
      border-left: 17px solid rgba(0, 0, 0, 0.1);
      position: absolute;
    }

    .col-inner {
      border-right: 1px solid #bbb;
    }
  }

  .col-picker {
    background-color: #fff;
    padding: 5px;
    margin-bottom: 10px;
    border-radius: 4px;
    cursor: pointer;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
    transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
    position: relative;

    &.col-active {
      background-image: linear-gradient(#6c7a89, #56616c);
      color: #fff;
    }

    &:hover {
      box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
      z-index: 1;
      transform: scale(1.008);
    }
  }

  .col-form {
    max-width: 600px;

    ::v-deep .input-group,
    .row-v {
      margin-bottom: 10px;
    }
  }

  .categories {
    left: 0;
  }

  .reports {
    left: $colwidths;
  }

  .settings {
    left: $colwidths * 2;
    right: 0;
  }
}

.researches-wrapper {
  position: relative;
  height: 345px;
  background: #fff;
  border-bottom: 1px solid #aaa;
}

.row-v-header {
  font-weight: bold;
  margin-bottom: 3px;
}

.mediacl-exam-padding {
  padding-left: 30px;
}
</style>
