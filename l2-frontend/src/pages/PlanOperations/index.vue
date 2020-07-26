<template>
  <div>
    <h3>{{title}}</h3>
    <Filters :filters="filters"/>
    <button class="btn btn-blue-nb add-row" @click="add_data">
      Добавить
    </button>
    <button class="btn btn-blue-nb add-row" @click="load_data">
      Обновить
    </button>
    <table class="table table-bordered" style="table-layout: fixed">
      <colgroup>
        <col width='85'/>
        <col width='100'/>
        <col/>
        <col width='170'/>
        <col width='180'/>
        <col width='180'/>
        <col width='180'/>
      </colgroup>
      <thead>
      <tr>
        <th>Дата</th>
        <th>№ истории</th>
        <th>Пациент</th>
        <th>Вид операции</th>
        <th>Врач-хирург</th>
        <th>Отделение</th>
        <th>Анестезиолог</th>
      </tr>
      </thead>
      <tbody>
      <Row :data="row" :key="row.pk_plan" v-for="row in data" :hirurgs="hirurgs" :anestesiologs="anestesiologs" />
      <tr v-if="data.length === 0"><td colspan="7" style="text-align: center">нет данных</td></tr>
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
        filters: {
          date: [moment().format('DD.MM.YYYY'), moment().add(7, 'days').format('DD.MM.YYYY')]
        },
      }
    },
    mounted() {
      this.$root.$on('hide_plan_operations', () => {
        this.edit_plan_operations = false
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
    },
    watch: {
      dateRange: {
        handler() {
          this.load_data();
        },
        immediate: true,
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
          'doc_anesthetist_pk': -1,
          'department_pk': -1
        })
        this.data = result
        await this.$store.dispatch(action_types.DEC_LOADING)
      }
    }
  }
</script>

