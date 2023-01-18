<template>
  <TwoSidedLayout>
    <template #left>
      <DataList
        v-model="selectedDepartmentId"
        source="employees/departments/list"
      />
    </template>
    <template #right>
      TODO
    </template>
  </TwoSidedLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue';

import TwoSidedLayout from '@/layouts/TwoSidedLayout.vue';
import DataList from '@/components/DataList.vue';

const selectedDepartmentId = ref<number | string | null>(null);
</script>

<style lang="scss" scoped>
</style>
