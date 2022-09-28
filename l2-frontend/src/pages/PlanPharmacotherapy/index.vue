<template>
  <div style="min-height: 500px;margin: 25px">
    <Filters
      :filters="filters"
      :departments="departments"
    />
    <AggregatePharmacoTherapyDepartment
      :date-range="dateRange"
      :department_pk="deapartment"
    />
  </div>
</template>

<script lang="ts">
import moment from 'moment';

import Filters from './components/Filters.vue';
import AggregatePharmacoTherapyDepartment from './components/AggregatePharmacoTherapyDepartment.vue';

export default {
  name: 'PlanPharmacotherapy',
  components: {
    Filters,
    AggregatePharmacoTherapyDepartment,
  },
  data() {
    return {
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
  computed: {
    dateRange() {
      let [d1, d2] = this.filters.date;
      d1 = d1.split('.');
      d1 = `${d1[2]}-${d1[1]}-${d1[0]}`;
      d2 = d2.split('.');
      d2 = `${d2[2]}-${d2[1]}-${d2[0]}`;
      return `${d1}x${d2}`;
    },
    deapartment() {
      return this.filters.department_pk;
    },
  },
  mounted() {
    this.init();
  },
  methods: {
    async init() {
      const { data } = await this.$api('procedural-list/suitable-departments');
      this.departments = [{ id: -1, label: 'Отделение не выбрано' }, ...data];
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
