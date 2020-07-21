<template>
  <div>
    <h3>{{title}}</h3>
    <table class="table" style="table-layout: fixed">
      <colgroup>
        <col width='201'/>
        <col />
        <col width='180'/>
        <col width='180'/>
      </colgroup>
      <thead>
      <tr>
        <th><date-range v-model="filter_date"/></th>
        <th></th>
        <th>Отделение</th>
        <th>Анестезиолог</th>
      </tr>
      </thead>
    </table>
    <button class="btn btn-blue-nb add-row" @click="add_data">
      Добавить
    </button>
    <button class="btn btn-blue-nb add-row" @click="load_data">
      Обновить
    </button>
    <table class="table table-bordered">
      <colgroup>
        <col width='30'/>
        <col width='70'/>
        <col width='100'/>
        <col width='170'/>
        <col width='100'/>
        <col width='100'/>
        <col width='100'/>
      </colgroup>
      <thead>
      <tr>
        <th>Дата</th>
        <th>№ истории</th>
        <th>ФИО пациента</th>
        <th>Вид операции</th>
        <th>Врач-хирург</th>
        <th>Отделение</th>
        <th>Анестезиолог</th>
      </tr>
      </thead>
    </table>
    <plan-operation-edit v-if="edit_plan_operations" :pk_plan="pk_plan"/>
  </div>

</template>


<script>
  import DateRange from "../ui-cards/DateRange";
  import PlanOperationEdit from '../modals/PlanOperationEdit'
  import plans_point from '../api/plans-point'
  import moment from "moment";

  export default {
    components: {
      PlanOperationEdit,
      DateRange,
    },
    name: "PlanOperations",
    data() {
      return {
        title: 'План операций',
        edit_plan_operations: false,
        pk_plan: '',
        data_plans: '',
        filter_date: [moment().format('DD.MM.YYYY'), moment().add(7, 'days').format('DD.MM.YYYY')],
      }
    },
    mounted() {
      this.$root.$on('hide_plan_operations', () => {
        this.edit_plan_operations = false
      });
    },
    methods:{
      add_data() {
        this.edit_plan_operations = true
        this.pk_plan = -1
      },
      async load_data(){
        let [d1, d2] = this.filter_date;
        d1 = d1.split('.');
        d1 = `${d1[2]}-${d1[1]}-${d1[0]}`;
        d2 = d2.split('.');
        d2 = `${d2[2]}-${d2[1]}-${d2[0]}`;
        const {result} = await plans_point.getPlansByParams({
          'start_date': d1,
          'end_date': d2,
          'doc_operate_pk': -1,
          'doc_anesthetist_pk': -1,
          'department': -1
        })
        this.data_plans = result
      }
    }
  }
</script>

<style scoped>

</style>
