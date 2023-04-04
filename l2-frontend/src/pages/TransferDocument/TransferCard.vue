<template>
  <PageInnerLayout>
    <ThreeSidedLayout>
      <template #left>
        <SelectedNumbersCards addText="Принять" />
      </template>
      <template #center>
        <SelectedNumbersCards addText="Перенести" />
      </template>
      <template #right>
        <SelectedNumbersCards addText="Отправить" />
      </template>
    </ThreeSidedLayout>
  </PageInnerLayout>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';

import ThreeSidedLayout from '@/layouts/ThreeSidedLayout.vue';
import PageInnerLayout from '@/layouts/PageInnerLayout.vue';
import SelectedNumbersCards from '@/pages/TransferDocument/SelectedNumbersCards.vue';

</script>

<style lang="scss" module>
.notSelected {
  color: gray;
}

.departmentHeader {
  padding: 5px;
  overflow-x: hidden;
}
</style>
