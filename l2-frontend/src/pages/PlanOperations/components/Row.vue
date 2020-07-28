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
    <td>
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
      />
    </td>
  </tr>
</template>

<script>
  import Treeselect from "@riophae/vue-treeselect";
  import '@riophae/vue-treeselect/dist/vue-treeselect.css'
  import * as action_types from "../../../store/action-types";
  import plans_point from "../../../api/plans-point";

  export default {
    name: "Row",
    components: {Treeselect},
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
    computed: {
      anestesiologId() {
        return this.data.doc_anesthetist_id;
      },
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

</style>
