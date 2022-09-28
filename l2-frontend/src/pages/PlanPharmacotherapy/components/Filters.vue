<template>
  <table
    class="table"
    style="table-layout: fixed"
  >
    <colgroup>
      <col width="201">
      <col width="20">
      <col width="310">
      <col>
    </colgroup>
    <tbody>
      <tr>
        <td>
          <DateRange v-model="/* eslint-disable-line vue/no-mutating-props */ filters.date" />
        </td>
        <td />
        <td>
          <Treeselect
            v-model="/* eslint-disable-line vue/no-mutating-props */ filters.department_pk"
            :multiple="false"
            :disable-branch-nodes="true"
            :options="departments"
            placeholder="Отделение не выбрано"
            :append-to-body="true"
          />
        </td>
        <td />
      </tr>
    </tbody>
  </table>
</template>

<script lang="ts">
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import DateRange from '@/ui-cards/DateRange.vue';

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
