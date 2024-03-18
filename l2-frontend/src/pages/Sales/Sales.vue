<template>
  <div>
    <div class="flex">
      <h4>Фильтры</h4>
      <Treeselect v-model="selectedMode" :options="modes" />
    </div>
    <div>
      <h4>Таблица</h4>
      <p>fdsfds</p>
      <VeTable />
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  VeLocale,
  VeTable,
} from 'vue-easytable';
import 'vue-easytable/libs/theme-default/index.css';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import { getCurrentInstance } from 'vue';

import ruRu from '@/locales/ve';
import * as actions from '@/store/action-types';
import { useStore } from '@/store';

VeLocale.use(ruRu);

const root = getCurrentInstance().proxy.$root;
const store = useStore();

const modes = {
  0: 'days',
  1: 'month',
};

const selectedMode = ref(0);

</script>

<style scoped lang="scss">
.flex {
  display: flex;
}
</style>
