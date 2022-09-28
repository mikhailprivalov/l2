<template>
  <div>
    <h3>{{ title }}</h3>
    <Filters
      :filters="filters"
      :departments="departments"
    />
    <div class="buttons">
      <button
        class="btn btn-blue-nb"
        @click="load_data"
      >
        Обновить
      </button>
    </div>
    <table
      class="table table-bordered"
      style="table-layout: fixed"
    >
      <colgroup>
        <col width="115">
        <col>
        <col width="180">
        <col width="260">
        <col width="140">
        <col width="170">
      </colgroup>
      <thead>
        <tr>
          <th>Дата</th>
          <th>Пациент</th>
          <th>Профиль, отделение</th>
          <th>Диагноз</th>
          <th>Примечания</th>
          <th>Статус</th>
        </tr>
      </thead>
      <tbody>
        <Row
          v-for="row in data"
          :key="row.pk_plan"
          :data="row"
        />
        <tr v-if="data.length === 0">
          <td
            colspan="7"
            style="text-align: center"
          >
            нет данных
          </td>
        </tr>
      </tbody>
    </table>
    <MessagesData
      v-if="messages_data && plan_pk !== -1"
      :plan_pk="plan_pk"
      :card_pk="card_pk"
    />
  </div>
</template>

<script lang="ts">
import moment from 'moment';
import Component from 'vue-class-component';
import Vue from 'vue';

import MessagesData from '@/pages/PlanHospitalization/components/MessagesData.vue';
import plansPoint from '@/api/plans-point';
import * as actions from '@/store/action-types';

import Filters from './components/Filters.vue';
import Row from './components/Row.vue';

@Component({
  components: {
    MessagesData,
    Filters,
    Row,
  },
  data() {
    return {
      title: 'План госпитализации',
      plan_pk: -1,
      card_pk: -1,
      data: [],
      departments: [],
      filters: {
        date: [moment().format('DD.MM.YYYY'), moment().add(7, 'days').format('DD.MM.YYYY')],
        department_pk: -1,
      },
      messages_data: false,
    };
  },
  async mounted() {
    this.init();
    this.$root.$on('reload-hospplans', () => {
      this.load_data();
    });
    this.$root.$on('hide_messages_data', () => {
      this.messages_data = false;
      this.plan_pk = -1;
      this.card_pk = -1;
    });
    this.$root.$on('open_messages_data', (data) => {
      this.messages_data = true;
      this.plan_pk = data.pk;
      this.card_pk = data.card;
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
    const resultData = await plansPoint.getPlansHospitalizationByParams({
      start_date: d1,
      end_date: d2,
      department_pk: this.filters.department_pk || -1,
    });
    this.data = resultData.result;
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
