<template>
  <div>
    <h3>{{title}}</h3>
    <Filters :filters="filters" :hirurgs="hirurgsWithEmpty" :anestesiologs="anestesiologsWithEmpty"
             :departments="departments"/>
    <div class="buttons">
      <button class="btn btn-blue-nb" @click="load_data">
        Обновить
      </button>
      <button @click="open_form_planOperations" class="btn btn-blue-nb" type="button">
        Печать
      </button>
    </div>
    <table class="table table-bordered" style="table-layout: fixed">
      <colgroup>
        <col width='85'/>
        <col width='90'/>
        <col/>
        <col width='155'/>
        <col width='155'/>
        <col width='155'/>
        <col width='320'/>
        <col width='55'/>
      </colgroup>
      <thead>
      <tr>
        <th>Дата</th>
        <th>История</th>
        <th>Пациент</th>
        <th>Вид операции</th>
        <th>Врач-хирург</th>
        <th>Отделение</th>
        <th>Анестезиолог</th>
        <th></th>
      </tr>
      </thead>
      <tbody>
      <Row :data="row" :key="row.pk_plan" v-for="row in data" :hirurgs="hirurgsReversed"
           :anestesiologs="anestesiologsWithEmpty"
           v-tippy="{ placement: 'top', arrow: true, interactive: true, theme: 'dark longread'}"
           :title="row.tooltip_data"/>
      <tr v-if="data.length === 0"><td colspan="8" style="text-align: center">нет данных</td></tr>
      </tbody>
    </table>
  </div>

</template>

<script>
import moment from 'moment';
import flatten from 'lodash/flatten';
import plansPoint from '../../api/plans-point';
import Filters from './components/Filters.vue';
import Row from './components/Row.vue';
import * as actions from '../../store/action-types';
import usersPoint from '../../api/user-point';
import { planOperations } from '../../forms';

export default {
  components: {
    Filters,
    Row,
  },
  name: 'PlanOperations',
  data() {
    return {
      title: 'План операций',
      pk_plan: '',
      data: [],
      hirurgs: [],
      anestesiologs: [],
      departments: [],
      filters: {
        date: [moment().format('DD.MM.YYYY'), moment().add(7, 'days').format('DD.MM.YYYY')],
        doc_anesthetist_pk: -1,
        doc_operate_pk: -1,
        department_pk: -1,
      },
    };
  },
  mounted() {
    this.init();
    this.$root.$on('reload-plans', () => {
      this.load_data();
    });
  },
  computed: {
    dateRange() {
      let [d1, d2] = this.filters.date;
      d1 = d1.split('.');
      d1 = `${d1[2]}-${d1[1]}-${d1[0]}`;
      d2 = d2.split('.');
      d2 = `${d2[2]}-${d2[1]}-${d2[0]}`;

      return `${d1}x${d2}`;
    },
    hirurgsWithEmpty() {
      return [{ id: -1, label: 'Хирург не выбран' }, ...this.hirurgs];
    },
    anestesiologsWithEmpty() {
      return [{ id: -1, label: 'Анестезиолог не выбран' }, ...this.anestesiologs];
    },
    hirurgsReversed() {
      return flatten(this.hirurgsWithEmpty.map((x) => x.children).filter(Boolean))
        .reduce((a, b) => ({ ...a, [b.id]: b }), {});
    },
    forms() {
      return planOperations.map((f) => ({
        ...f,
        url: f.url.kwf({
          pks_plan: this.pks_plan,
        }),
      }));
    },
    pks_plan() {
      const pksPlanData = [];
      for (const i of this.data) {
        pksPlanData.push(i.pk_plan);
      }
      return pksPlanData;
    },
  },
  watch: {
    filters: {
      handler() {
        if (this.departments.length > 0) {
          this.load_data();
        }
      },
      deep: true,
    },
  },
  methods: {
    async open_form_planOperations() {
      window.open(this.forms[0].url);
    },
    async init() {
      if (this.hirurgs.length === 0) {
        const { users } = await usersPoint.loadUsersByGroup({ group: ['Оперирует'] });
        this.hirurgs = users;
      }
      if (this.anestesiologs.length === 0) {
        const { users } = await usersPoint.loadUsersByGroup({ group: ['Анестезиолог'] });
        this.anestesiologs = users;
      }
      const { data } = await plansPoint.getDepartmentsOperate();
      this.departments = [{ id: -1, label: 'Отделение не выбрано' }, ...data];
      await this.load_data();
    },
    async load_data() {
      await this.$store.dispatch(actions.INC_LOADING);
      const [d1, d2] = this.dateRange.split('x');
      const { result } = await plansPoint.getPlansByParams({
        start_date: d1,
        end_date: d2,
        doc_operate_pk: this.filters.doc_operate_pk || -1,
        doc_anesthetist_pk: this.filters.doc_anesthetist_pk || -1,
        department_pk: this.filters.department_pk || -1,
      });
      this.data = result;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
};
</script>

<style scoped lang="scss">
  .buttons {
    margin-bottom: 5px;
    color: #cacfd2;
  }

</style>
