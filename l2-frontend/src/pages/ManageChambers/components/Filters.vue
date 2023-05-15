<template>
  <Treeselect
    v-model="/* eslint-disable-line vue/no-mutating-props */ departId"
    :multiple="false"
    :disable-branch-nodes="true"
    :options="departments"
    placeholder="Отделение не выбрано"
    :append-to-body="true"
    @input="$emit('input', departId)"
  />
</template>

<script setup lang="ts">

import Treeselect from '@riophae/vue-treeselect';
import { defineProps, ref } from 'vue';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

const props = defineProps(['departments']);
const departId = ref(-1);

</script>
