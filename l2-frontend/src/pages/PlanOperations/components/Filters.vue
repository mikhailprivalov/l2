<template>
  <table class="table" style="table-layout: fixed">
    <colgroup>
      <col width='201'/>
      <col/>
      <col width='310'/>
      <col width='310'/>
      <col width='310'/>
    </colgroup>
    <tbody>
    <tr>
      <td>
        <date-range v-model="filters.date"/>
      </td>
      <td></td>
      <td>
        <treeselect :multiple="false" :disable-branch-nodes="true" :options="hirurgs"
                    placeholder="Хирург не выбран" v-model="filters.doc_operate_pk"
                    :append-to-body="true"
        />
      </td>
      <td>
        <treeselect :multiple="false" :disable-branch-nodes="true" :options="departments"
                    placeholder="Отделение не выбрано" v-model="filters.department_pk"
                    :append-to-body="true"
        />
      </td>
      <td>
        <treeselect :multiple="false" :disable-branch-nodes="true" :options="anestesiologs"
                    placeholder="Анестезиолог не выбран" v-model="filters.doc_anesthetist_pk"
                    :append-to-body="true"
        />
      </td>
    </tr>
    </tbody>
  </table>
</template>
<script>
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
