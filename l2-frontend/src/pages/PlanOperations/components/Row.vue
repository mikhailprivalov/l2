<template>
  <tr>
    <td>
      {{data.date}}
    </td>
    <td>
      {{data.direction}}
    </td>
    <td>
      {{data.fio_patient}} {{data.birthday}}
    </td>
    <td :class="{delRow: data.canceled}">
      {{data.type_operation}}
    </td>
    <td>
      {{hirurgs[data.doc_operate_id].label}}
    </td>
    <td>
      {{hirurgs[data.doc_operate_id].podr}}
    </td>
    <td>
      <treeselect :multiple="false" :disable-branch-nodes="true" :options="anestesiologs"
                  placeholder="Анестезиолог не выбран" v-model="data.doc_anesthetist_id"
                  :append-to-body="true"
      />
    </td>
    <td>
      <button title="Редактирование" class="btn btn-blue-nb" type="button" v-tippy
              tabindex="-1"
              @click="edit_plan_operation = true">
        <i class="fa fa-pencil"></i>
      </button>
      <plan-operation-edit
        v-if="edit_plan_operation" :pk_plan="data.pk_plan"
        :pk_hirurg="data.doc_operate_id"
        :date="data.date_raw"
        :operation="data.type_operation"
        :direction="data.direction"
        :patient_fio="`${data.fio_patient}, ${data.birthday}`"
        :card_pk="data.patient_card"
        :cancel_operation="data.canceled"
      />
    </td>
  </tr>
</template>

<script>
  import Treeselect from "@riophae/vue-treeselect";
  import '@riophae/vue-treeselect/dist/vue-treeselect.css'
  import * as action_types from "../../../store/action-types";
  import plans_point from "../../../api/plans-point";
  import PlanOperationEdit from "../../../modals/PlanOperationEdit";

  export default {
    name: "Row",
    components: {PlanOperationEdit, Treeselect},
    props: {
      data: {
        type: Object,
        required: true,
      },
      hirurgs: {
        type: Object,
        required: true,
      },
      anestesiologs: {
        type: Array,
        required: true,
      },
    },
    data() {
      return {
        edit_plan_operation: false
      };
    },
    computed: {
      anestesiologId() {
        return this.data.doc_anesthetist_id;
      },
    },
    mounted() {
      this.$root.$on('hide_plan_operations', () => this.edit_plan_operation = false)
    },
    watch: {
      async anestesiologId() {
        await this.$store.dispatch(action_types.INC_LOADING)
        await plans_point.changeAnestesiolog({
          'plan_pk': this.data.pk_plan,
          'doc_anesthetist_pk': this.anestesiologId,
        })
        okmessage('Анестезиолог изменён');
        await this.$store.dispatch(action_types.DEC_LOADING)
      },
    },
  }
</script>

<style scoped>
  .delRow{
    color: red;
	  text-decoration: line-through;
  }

</style>
