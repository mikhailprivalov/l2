<template>
  <table class="table" style="table-layout: fixed">
    <colgroup>
      <col width='201'/>
      <col />
      <col width='510'/>
      <col width='410'/>
    </colgroup>
    <tbody>
    <tr>
      <td>
        <date-range v-model="filters.date"/>
      </td>
      <td/>
      <td>
        <treeselect
          :multiple="false"
          :disable-branch-nodes="true"
          :options="departments"
          placeholder="Отделение не выбрано"
          v-model="filters.department_pk"
          :append-to-body="true"
          class="treeselect-wide"
          :clearable="false"
        />
      </td>
      <td>
        <h6 style="vertical-align: middle; float: right">Выбытие </h6>
      </td>
    </tr>
    </tbody>
  </table>
</template>
<script lang="ts">
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import DateRange from '../../../ui-cards/DateRange.vue';

export default {
  name: 'Filters',
  components: { DateRange, Treeselect },
  props: {
    filters: {
      type: Object,
      required: true,
    },
    departments: {
      type: Array,
      required: true,
    },
  },
};
</script>
