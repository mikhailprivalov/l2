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

  export default {
    components: {
      PlanOperationEdit,
    },
    name: "PlanOperations",
    data() {
      return {
        title: 'План операций',
        edit_plan_operations: false,
        pk_plan: ''
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
      }
    }
  }
</script>

<style scoped>

</style>
