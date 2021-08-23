<template>
  <div class="root">
    <div class="categories">
      <div class="col-header">Разделы статистики</div>
      <div class="col-inner">
        <div
          class="col-picker"
          :class="selectedCategory === c.id && 'col-active'"
          @click="selectedCategory = c.id"
          v-for="c in categories"
          :key="c.id"
        >
          {{ c.label }}
        </div>
      </div>
    </div>
    <div class="reports">
      <div class="col-header">Отчёты</div>
      <div class="col-inner text-center" v-if="!currentCategory">не выбрано</div>
      <div class="col-inner" v-else>
        <div
          class="col-picker"
          :class="selectedReport === id && 'col-active'"
          @click="selectedReport = id"
          v-for="(r, id) in currentCategory.reports"
          :key="id"
        >
          {{ r.title }}
        </div>
      </div>
    </div>
    <div class="settings" :key="selectedReport">
      <div class="col-header">Настройка</div>
      <div class="col-inner text-center" v-if="!currentReport">не выбрано</div>
      <div class="col-inner" v-else>
        <div class="col-form">
          <LaboratoryPicker
            v-model="values.lab"
            :with-all="checkReportParam(PARAMS_TYPES.LABORATORY_WITH_ALL)"
            v-if="checkReportParam(PARAMS_TYPES.LABORATORY, PARAMS_TYPES.LABORATORY_WITH_ALL)"
            :key="PARAMS_TYPES.LABORATORY_WITH_ALL"
          />

          <div class="input-group" v-if="checkReportParam(PARAMS_TYPES.USERS)" :key="PARAMS_TYPES.USERS">
            <span class="input-group-addon">Пользователи:</span>
            <treeselect
              class="treeselect-noborder treeselect-wide"
              :multiple="true"
              :disable-branch-nodes="true"
              :options="users"
              placeholder="Пользователи не выбраны"
              v-model="values.users"
            />
          </div>

          <div class="input-group" v-if="checkReportParam(PARAMS_TYPES.USER_OR_DEP)" :key="`${PARAMS_TYPES.USER_OR_DEP}_user`">
            <span class="input-group-addon">Пользователь:</span>
            <treeselect
              class="treeselect-noborder treeselect-wide"
              :multiple="false"
              :disable-branch-nodes="true"
              :options="users"
              :clearable="true"
              placeholder="Пользователь не выбан"
              :disabled="values.dep"
              v-model="values.user"
            />
          </div>

          <div class="row-v" v-if="checkReportParam(PARAMS_TYPES.USER_OR_DEP)">или</div>

          <div class="input-group" v-if="checkReportParam(PARAMS_TYPES.USER_OR_DEP)" :key="`${PARAMS_TYPES.USER_OR_DEP}_dep`">
            <span class="input-group-addon">Подразделение:</span>
            <treeselect
              class="treeselect-noborder treeselect-wide"
              :multiple="false"
              :disable-branch-nodes="true"
              :options="deps"
              :clearable="true"
              placeholder="Подразделение не выбано"
              :disabled="values.user"
              v-model="values.dep"
            />
          </div>

          <div class="row-v" v-if="checkReportParam(PARAMS_TYPES.RESEARCH)" :key="PARAMS_TYPES.RESEARCH">
            <div class="row-v-header">Услуга:</div>
            <div class="researches-wrapper">
              <ResearchesPicker
                v-model="values.research"
                autoselect="none"
                :just_search="true"
                :hidetemplates="true"
                :oneselect="true"
                :filter_types="[2]"
              />
            </div>
          </div>

          <div class="input-group" v-if="checkReportParam(PARAMS_TYPES.COMPANY)" :key="PARAMS_TYPES.COMPANY">
            <span class="input-group-addon">Компания:</span>
            <treeselect
              class="treeselect-noborder treeselect-wide"
              :multiple="false"
              :disable-branch-nodes="true"
              :options="companies"
              :clearable="true"
              placeholder="Компания не выбана"
              v-model="values.company"
            />
          </div>

          <div class="input-group" v-if="checkReportParam(PARAMS_TYPES.FIN_SOURCE)" :key="PARAMS_TYPES.FIN_SOURCE">
            <span class="input-group-addon">Источник финансирования:</span>
            <select v-model="values.finSource" class="form-control">
              <option :value="-1">не выбрано</option>
              <optgroup :label="b.title" v-for="b in bases" :key="b.pk">
                <option v-for="f in b.fin_sources.filter(x => !x.hide)" :key="f.pk" :value="f.pk">
                  {{ b.title }} – {{ f.title }}
                </option>
              </optgroup>
            </select>
          </div>

          <div class="input-group" v-if="checkReportParam(PARAMS_TYPES.MONTH_YEAR)" :key="PARAMS_TYPES.MONTH_YEAR">
            <span class="input-group-addon">Год</span>
            <input v-model.number="values.year" type="number" min="2020" max="3000" class="form-control" />
            <span class="input-group-addon">Месяц</span>
            <select v-model="values.month" class="form-control">
              <option :value="1">Январь</option>
              <option :value="2">Февраль</option>
              <option :value="3">Март</option>
              <option :value="4">Апрель</option>
              <option :value="5">Май</option>
              <option :value="6">Июнь</option>
              <option :value="7">Июль</option>
              <option :value="8">Август</option>
              <option :value="9">Сентябрь</option>
              <option :value="10">Октябрь</option>
              <option :value="11">Ноябрь</option>
              <option :value="12">Декабрь</option>
            </select>
          </div>

          <DatePicker
            v-model="values.dateRange"
            mode="date"
            :masks="masks"
            is-range
            :max-date="new Date()"
            v-if="checkReportParam(PARAMS_TYPES.DATE_RANGE)"
            :rows="2"
            :step="1"
            :key="PARAMS_TYPES.DATE_RANGE"
          >
            <template v-slot="{ inputValue, inputEvents }">
              <div class="input-group">
                <span class="input-group-addon">Дата:</span>
                <input class="form-control" :value="inputValue.start" v-on="inputEvents.start" />
                <span class="input-group-addon" style="background-color: #fff;color: #000; height: 34px">&mdash;</span>
                <input class="form-control" :value="inputValue.end" v-on="inputEvents.end" />
              </div>
            </template>
          </DatePicker>

          <div class="row-v" v-if="checkReportParam(PARAMS_TYPES.PERIOD_DATE)" :key="PARAMS_TYPES.PERIOD_DATE">
            <DateSelector :date_type.sync="values.dateType" :values.sync="values.dateValues" />
          </div>

          <a class="btn btn-blue-nb" type="button" v-if="reportUrl" :href="reportUrl" target="_blank">
            Сформировать отчёт
          </a>
          <div v-else-if="dateRangeInvalid">
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
import DatePicker from 'v-calendar/lib/components/date-picker.umd';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import LaboratoryPicker from '@/fields/LaboratoryPicker.vue';
import DateSelector from '@/fields/DateSelector.vue';
import * as actions from '@/store/action-types';
import usersPoint from '@/api/user-point';
import ResearchesPicker from '@/ui-cards/ResearchesPicker.vue';

const PARAMS_TYPES = {
  DATE_RANGE: 'DATE_RANGE',
  LABORATORY: 'LABORATORY',
  LABORATORY_WITH_ALL: 'LABORATORY_WITH_ALL',
  PERIOD_DATE: 'PERIOD_DATE',
  USERS: 'USERS',
  USER_OR_DEP: 'USER_OR_DEP',
  FIN_SOURCE: 'FIN_SOURCE',
  RESEARCH: 'RESEARCH',
  COMPANY: 'COMPANY',
  MONTH_YEAR: 'MONTH_YEAR',
};

const STATS_CATEGORIES = {
  labs: {
    title: 'Лаборатории',
    groups: ['Просмотр статистики', 'Врач-лаборант'],
    reports: {
      researches: {
        title: 'Выполнено исследований',
        params: [PARAMS_TYPES.DATE_RANGE, PARAMS_TYPES.LABORATORY_WITH_ALL],
        url: '/statistic/xls?type=lab&pk=<lab>&date-start=<date-start>&date-end=<date-end>',
      },
      executors: {
        title: 'Исполнители',
        params: [PARAMS_TYPES.DATE_RANGE, PARAMS_TYPES.LABORATORY],
        url: '/statistic/xls?type=lab-staff&pk=<lab>&date-start=<date-start>&date-end=<date-end>',
      },
      tubes: {
        title: 'Принято ёмкостей',
        params: [PARAMS_TYPES.DATE_RANGE, PARAMS_TYPES.LABORATORY],
        url: '/statistic/xls?type=lab-receive&pk=<lab>&date-start=<date-start>&date-end=<date-end>',
      },
    },
  },
  materialGet: {
    title: 'Забор биоматериала',
    groups: ['Просмотр статистики'],
    reports: {
      executors: {
        title: 'Заборщики биоматериала',
        params: [PARAMS_TYPES.PERIOD_DATE, PARAMS_TYPES.USERS],
        url: '/statistic/xls?type=journal-get-material&users=<users>&date_type=<date-type>&values=<date-values>',
      },
    },
  },
  researches: {
    title: 'Оказанные услуги',
    groups: ['Просмотр статистики'],
    reports: {
      executors: {
        title: 'По врачу (нагрузка) – статталоны',
        params: [PARAMS_TYPES.PERIOD_DATE, PARAMS_TYPES.USER_OR_DEP, PARAMS_TYPES.FIN_SOURCE],
        url: [
          '/statistic/xls?type=statistics-tickets-print&user=<user>',
          '&department=<dep>&date_type=<date-type>&date_values=<date-values>&fin=<fin-source>',
        ].join(''),
      },
      visits: {
        title: 'Посещения',
        params: [PARAMS_TYPES.DATE_RANGE],
        url: '/statistic/xls?type=statistics-passed&date-start=<date-start>&date-end=<date-end>',
      },
      research: {
        title: 'По услуге',
        params: [PARAMS_TYPES.PERIOD_DATE, PARAMS_TYPES.RESEARCH],
        url: '/statistic/xls?type=statistics-research&date_type=<date-type>&date_values=<date-values>&research=<research>',
      },
    },
  },
  prof: {
    title: 'Профосмотры',
    groups: ['Просмотр статистики'],
    reports: {
      contragents: {
        title: 'Контрагенты',
        params: [PARAMS_TYPES.DATE_RANGE, PARAMS_TYPES.COMPANY],
        url: '/forms/pdf?type=200.01&company=<company>&date1=<date-start>&date2=<date-end>',
      },
    },
  },
  screening: {
    title: 'Скрининг',
    groups: ['Статистика скрининга'],
    reports: {
      screening: {
        title: 'Отчёт по скринингу',
        params: [PARAMS_TYPES.MONTH_YEAR],
        url: '/statistic/screening?month=<month>&year=<year>',
      },
    },
  },
  common: {
    title: 'Общая статистика',
    groups: ['Просмотр статистики'],
    reports: {
      vac: {
        title: 'Вакцинация',
        params: [PARAMS_TYPES.DATE_RANGE],
        url: '/statistic/xls?type=vac&pk=0&date-start=<date-start>&date-end=<date-end>',
      },
      onco: {
        title: 'Онкоподозрение',
        params: [PARAMS_TYPES.DATE_RANGE],
        url: '/statistic/xls?type=statistics-onco&date-start=<date-start>&date-end=<date-end>',
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
  user: null,
  dep: null,
  research: null,
  company: null,
  month: moment().month() + 1,
  year: moment().year(),
});

const formatDate = (date: Date) => moment(date).format('DD.MM.YYYY');
const jsonv = data => encodeURIComponent(JSON.stringify(data));

@Component({
  components: {
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

  research: number | null;

  get userGroups() {
    return this.$store.getters.user_data.groups || [];
  }

  async loadUsers() {
    await this.$store.dispatch(actions.INC_LOADING);
    const { users } = await usersPoint.loadUsersByGroup({ group: '*' });
    this.users = users;
    await this.$store.dispatch(actions.DEC_LOADING);
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

  get categories() {
    return Object.keys(this.STATS_CATEGORIES)
      .filter(id => this.STATS_CATEGORIES[id].groups.some(g => this.userGroups.includes(g)))
      .map(id => ({ id, label: this.STATS_CATEGORIES[id].title }));
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

  get bases() {
    return (this.$store.getters.bases || []).filter(b => !b.hide);
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

      if (this.PARAMS_TYPES.RESEARCH === p) {
        if (_.isNil(this.values.research)) {
          return null;
        }

        url = url.replace('<research>', this.values.research);
      }

      if (this.PARAMS_TYPES.COMPANY === p) {
        if (_.isNil(this.values.company)) {
          return null;
        }

        url = url.replace('<company>', this.values.company);
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
</style>
