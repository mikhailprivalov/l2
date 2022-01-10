<template>
  <tr :class="{'cancel-row': data.canceled}">
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
    <td>{{data.comment}}</td>
    <td>
      <button class="btn btn-blue-nb" type="button"
        tabindex="-1"
        @click="cancel_plan_hospitalization">
        Отмена
      </button>
    </td>
  </tr>
</template>

<script lang="ts">
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import plansPoint from '@/api/plans-point';

export default {
  name: 'Row',
  props: {
    data: {
      type: Object,
      required: true,
    },
  },

  methods: {
    async cancel_plan_hospitalization() {
      await plansPoint.cancelPlansHospitalization({
        pk_plan: this.data.pk_plan,
        status: 2,
      });
      this.$root.$emit('reload-hospplans');
    },
  },
};
</script>

<style scoped lang="scss">
  .cancel-row {
    td, th {
      opacity: .6;
      text-decoration: line-through;
      background-color: linen;
    }

    &:hover {
      td, th {
        opacity: 1;
        text-decoration: none;
      }
    }
  }
</style>
