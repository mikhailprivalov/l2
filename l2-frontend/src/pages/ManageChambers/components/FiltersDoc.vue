<template>
  <div>
    <Treeselect
      v-model="/* eslint-disable-line vue/no-mutating-props */ filters.doctor_pk"
      :multiple="false"
      :disable-branch-nodes="true"
      :options="doctors"
      :z-index="10001"
      placeholder="Лечащий врач не выбран"
      :append-to-body="true"
    />
  </div>
</template>

<script lang="ts">
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

export default {
  name: 'FiltersDoc',
  components: { Treeselect },
  props: {
    filters: {
      type: Object,
      required: true,
    },
    doctors: {
      type: Object,
      required: true,
    },
  },
};
</script>
