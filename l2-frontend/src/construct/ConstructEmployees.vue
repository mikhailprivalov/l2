<template>
  <TwoSidedLayout>
    <template #left>
      <DataList
        v-model="selectedDepartmentId"
        base-source="employees/departments"
        :list-request-params="DEPARTMENTS_REQUEST_PARAMS"
        loading-text="загрузка отделов..."
        with-creating
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

const DEPARTMENTS_REQUEST_PARAMS = {
  onlyActive: false,
};
</script>

<style lang="scss" scoped>
</style>
