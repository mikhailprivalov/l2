<template>
  <div>
    <Treeselect
      v-model="/* eslint-disable-line vue/no-mutating-props */ filters.department_pk"
      :multiple="false"
      :disable-branch-nodes="true"
      :options="departments"
      placeholder="Отделение не выбрано"
      :append-to-body="true"
    />
  </div>
</template>

<script lang="ts">
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

export default {
  name: 'Filters',
  components: { Treeselect },
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
