<template>
  <div>
    <h3>{{title}}</h3>
    <table class="table">
      <colgroup>
        <col width='70'/>
        <col width='70'/>
        <col width='100'/>
        <col width='100'/>
        <col width='100'/>
      </colgroup>
      <thead>
      <tr>
        <th><input class="form-control" type="date"></th>
        <th><input class="form-control" type="date"></th>
        <th><input class="form-control"></th>
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
  import PlanOperationEdit from '../modals/PlanOperationEdit'
  import plans_point from '../api/plans-point'

  export default {
    components: {
      PlanOperationEdit,
    },
    name: "PlanOperations",
    data() {
      return {
        title: 'План операций',
        edit_plan_operations: false,
        pk_plan: '',
        data_plans: ''
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
        const {result} = await plans_point.getPlansByParams({
          'start_date': '2020-07-17',
          'end_date': '2020-07-19',
          'doc_operate_pk': 1940,
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
