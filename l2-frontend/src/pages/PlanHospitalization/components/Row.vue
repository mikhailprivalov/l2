<template>
  <tr :class="{'cancel-row': data.canceled && !edit_plan_operation}">
    <td>
      {{data.date}}
    </td>
    <td>
        {{data.fio_patient}}
    </td>
    <td>
      {{data.phone}}
    </td>
    <td>
      {{data.research_title}}
    </td>
    <td>
      {{data.depart_title}}
    </td>
    <td>
      {{data.diagnos}}
    </td>
    <td>{{data.comment}}}</td>
  </tr>
</template>

<script lang="ts">
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

export default {
  name: 'Row',
  props: {
    data: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      edit_plan_operation: false,
    };
  },

  mounted() {
    this.$root.$on('hide_plan_operations', () => {
      this.edit_plan_operation = false;
    });
  },
};
</script>

<style scoped lang="scss">
  .cancel-row {
    td, th {
      opacity: .6;
      text-decoration: line-through;
    }

    &:hover {
      td, th {
        opacity: 1;
        text-decoration: none;
      }
    }
  }
</style>
