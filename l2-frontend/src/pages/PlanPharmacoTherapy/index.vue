<template>
  <div>
    <h3>{{title}}</h3>
    <Filters :filters="filters" :departments="departments"/>
    <div class="buttons">
      <button class="btn btn-blue-nb" @click="load_data">
        Обновить
      </button>
      <button class="btn btn-blue-nb" type="button">
        Печать
      </button>
    </div>
    <aggregate-pharmaco-therapy-department :direction="226131" :start_date="start_date" :end_date="end_date"/>

  </div>

</template>


<script>
  import plans_point from '../../api/plans-point'
  import moment from "moment";
  import Filters from "./components/Filters";
  import AggregatePharmacoTherapyDepartment from "./components/AggregatePharmacoTherapyDepartment";
  import api from '@/api';
  import * as action_types from "../../store/action-types";

  export default {
    components: {
      Filters, AggregatePharmacoTherapyDepartment,
    },
    name: "PlanPharmacoTherapy",
    data() {
      return {
        title: 'Процедурный лист',
        pk_plan: '',
        data: [],
        departments: [],
        filters: {
          date: [moment().format('DD.MM.YYYY'), moment().add(7, 'days').format('DD.MM.YYYY')],
          department_pk: -1,
        },
        start_date: '',
        end_date: ''

      }
    },
    mounted() {
      this.init();
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
    },
    watch: {
      filters: {
        handler() {
          if (this.departments.length > 0) {
            this.load_data();
          }
        },
        deep: true,
      }
    },
    methods: {
      async init() {
        const {data} = await plans_point.getDepartmentsOperate()
        this.departments = [{id: -1, label: 'Отделение не выбрано'}, ...data];
        await this.load_data();
      },
      async load_data(){
        [this.start_date, this.end_date] = this.dateRange.split('x');
      }
    }
  }
</script>

<style scoped lang="scss">
  .buttons {
    margin-bottom: 5px;
    color: #cacfd2;
  }

</style>

