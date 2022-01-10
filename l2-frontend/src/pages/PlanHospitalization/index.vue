<template>
  <div>
    <h3>{{ title }}</h3>
    <Filters :filters="filters" :departments="departments" />
    <div class="buttons">
      <button class="btn btn-blue-nb" @click="load_data">
        Обновить
      </button>
    </div>
    <table class="table table-bordered" style="table-layout: fixed">
      <colgroup>
        <col width="85" />
        <col />
        <col width="135" />
        <col width="115" />
        <col width="170" />
        <col width="170" />
        <col width="150" />
        <col width="95"  />
      </colgroup>
      <thead>
        <tr>
          <th>Дата</th>
          <th>Пациент</th>
          <th>Телефон</th>
          <th>Профиль</th>
          <th>Отделение</th>
          <th>Диагноз</th>
          <th>Прим</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <Row
          :data="row"
          :key="row.pk_plan"
          v-for="row in data"
          v-tippy="{ placement: 'top', arrow: true, interactive: true, theme: 'dark longread' }"
          :title="row.tooltip_data"
        />
        <tr v-if="data.length === 0">
          <td colspan="8" style="text-align: center">нет данных</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script lang="ts">
import moment from 'moment';
import Component from 'vue-class-component';
import Vue from 'vue';
import plansPoint from '../../api/plans-point';
import Filters from './components/Filters.vue';
import Row from './components/Row.vue';
import * as actions from '../../store/action-types';

@Component({
  components: {
    Filters,
    Row,
  },
  data() {
    return {
      title: 'План госпитализации',
      pk_plan: '',
      data: [],
      departments: [],
      filters: {
        date: [
          moment().format('DD.MM.YYYY'),
          moment()
            .add(7, 'days')
            .format('DD.MM.YYYY'),
        ],
        department_pk: -1,
      },
    };
  },
  async mounted() {
    this.init();
    this.$root.$on('reload-hospplans', () => {
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
})
export default class PlanHospitalization extends Vue {
  departments: any[];

  data: any[];

  filters: any;

  dateRange: any;

  async init() {
    const { data } = await this.$api('procedural-list/suitable-departments');
    this.departments = [{ id: -1, label: 'Отделение не выбрано' }, ...data];
    await this.load_data();
  }

  async load_data() {
    await this.$store.dispatch(actions.INC_LOADING);
    const [d1, d2] = this.dateRange.split('x');
    const result_data = await plansPoint.getPlansHospitalizationByParams({
      start_date: d1,
      end_date: d2,
      department_pk: this.filters.department_pk || -1,
    });
    this.data = result_data.result;
    await this.$store.dispatch(actions.DEC_LOADING);
  }
}
</script>

<style scoped lang="scss">
.buttons {
  margin-bottom: 5px;
  color: #cacfd2;
}
</style>
