<template>
  <Treeselect
    v-model="departId"
    :multiple="false"
    :disable-branch-nodes="true"
    :options="props.departments"
    placeholder="Отделение не выбрано"
    :append-to-body="true"
    :class="{'treeselect-noborder': props.noBorder}"
    @input="$emit('input', departId)"
  />
</template>

<script setup lang="ts">

import Treeselect from '@riophae/vue-treeselect';
import { defineProps, ref } from 'vue';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

const props = defineProps({
  departments: {
    type: Array,
    required: true,
  },
  noBorder: {
    type: Boolean,
    required: false,
  },
});
const departId = ref(null);

</script>
