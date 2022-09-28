<template>
  <table
    class="table"
    style="table-layout: fixed"
  >
    <colgroup>
      <col width="201">
      <col>
      <col width="310">
      <col width="310">
      <col width="310">
    </colgroup>
    <tbody>
      <tr>
        <td>
          <DateRange v-model="/* eslint-disable-line vue/no-mutating-props */ filters.date" />
        </td>
        <td />
        <td>
          <Treeselect
            v-model="/* eslint-disable-line vue/no-mutating-props */ filters.doc_operate_pk"
            :multiple="false"
            :disable-branch-nodes="true"
            :options="hirurgs"
            placeholder="Хирург не выбран"
            :append-to-body="true"
          />
        </td>
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
        <td>
          <Treeselect
            v-model="/* eslint-disable-line vue/no-mutating-props */ filters.doc_anesthetist_pk"
            :multiple="false"
            :disable-branch-nodes="true"
            :options="anestesiologs"
            placeholder="Анестезиолог не выбран"
            :append-to-body="true"
          />
        </td>
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
    anestesiologs: {
      type: Array,
      required: true,
    },
    hirurgs: {
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
