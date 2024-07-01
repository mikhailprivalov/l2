<template>
  <div class="two-col">
      <Explorer class="sidebar" />
    <div class="viewer">
      <h4>Просмотрщик</h4>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  ref,
} from 'vue';

import Explorer from '@/pages/DocumentManagement/Explorer.vue';

</script>

<style scoped lang="scss">
.two-col {
  display: grid;
  grid-template-columns: minmax(200px, 380px) minmax(150px, auto);
  height: calc(100vh - 36px);
}
.sidebar {
  display: flex;
  flex-direction: column;
  background-color: #f8f7f7;
  border-right: 1px solid #b1b1b1;

  .form-control {
    border-radius: 0;
    padding-left: 10px;
  }
}

</style>
