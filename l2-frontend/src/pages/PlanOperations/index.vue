<template>
  <div>
    <h3>{{title}}</h3>
    <Filters :filters="filters" :hirurgs="hirurgsWithEmpty" :anestesiologs="anestesiologsWithEmpty"
             :departments="departments"/>
    <div class="buttons">
      <button class="btn btn-blue-nb" @click="add_data">
        Добавить запись
      </button>
      <button class="btn btn-blue-nb" @click="load_data">
        Обновить
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
           :anestesiologs="anestesiologsWithEmpty" />
      <tr v-if="data.length === 0"><td colspan="8" style="text-align: center">нет данных</td></tr>
      </tbody>
    </table>
    <plan-operation-edit v-if="edit_plan_operations" :pk_plan="pk_plan"/>
  </div>

</template>


<script>
  import PlanOperationEdit from '../../modals/PlanOperationEdit'
  import plans_point from '../../api/plans-point'
  import moment from "moment";
  import Filters from "./components/Filters";
  import Row from "./components/Row";
  import * as action_types from "../../store/action-types";
  import users_point from "../../api/user-point";
  import flatten from 'lodash/flatten';

  export default {
    components: {
      Filters,
      PlanOperationEdit,
      Row,
    },
    name: "PlanOperations",
    data() {
      return {
        title: 'План операций',
        edit_plan_operations: false,
        pk_plan: '',
        data: [],
        hirurgs: [],
        anestesiologs: [],
        departments: [],
        filters: {
          date: [moment().format('DD.MM.YYYY'), moment().add(7, 'days').format('DD.MM.YYYY')],
          doc_anesthetist_pk: -1,
          department_pk: -1,
        },
      }
    },
    mounted() {
      this.$root.$on('hide_plan_operations', () => {
        this.edit_plan_operations = false
      });
      this.$root.$on('reload-plans', () => {
        this.load_data();
      });
      plans_point.getDepartmentsOperate().then(({data}) => {
        this.departments = [{id: -1, label: 'Отделение не выбрано'}, ...data];
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
        return [{id: -1, label: 'Хирург не выбран'}, ...this.hirurgs]
      },
      anestesiologsWithEmpty() {
        return [{id: -1, label: 'Анестезиолог не выбран'}, ...this.anestesiologs]
      },
      hirurgsReversed() {
        return flatten(this.hirurgsWithEmpty.map(x => x.children).filter(Boolean))
          .reduce((a, b) => ({...a, [b.id]: b}), {});
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
      add_data() {
        this.edit_plan_operations = true
        this.pk_plan = -1
      },
      async load_data() {
        await this.$store.dispatch(action_types.INC_LOADING)
        const [d1, d2] = this.dateRange.split('x');
        if (this.hirurgs.length === 0) {
          const {users} = await users_point.loadUsersByGroup({'group': ['Оперирует']})
          this.hirurgs = users
        }
        if (this.anestesiologs.length === 0) {
          const {users} = await users_point.loadUsersByGroup({'group': ['Анестезиолог']})
          this.anestesiologs = users
        }
        const {result} = await plans_point.getPlansByParams({
          'start_date': d1,
          'end_date': d2,
          'doc_operate_pk': -1,
          'doc_anesthetist_pk': this.filters.doc_anesthetist_pk || -1,
          'department_pk': this.filters.department_pk || -1,
        })
        this.data = result
        await this.$store.dispatch(action_types.DEC_LOADING)
      }
    }
  }
</script>

<style scoped lang="scss">
  .buttons {
    margin-bottom: 5px;
  }
</style>

