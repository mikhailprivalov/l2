<template>
  <div>
    <div class="main">
      <div class="customer-type">
        <RadioFieldById
          v-model="selectedCustomer"
          :variants="typesCustomer"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

import RadioFieldById from '@/fields/RadioFieldById.vue';

const typesCustomer = ref([
  { id: 1, label: 'Заказчик' },
  { id: 2, label: 'Внешний исполнитель' },
  { id: 3, label: 'Работодатель' },
]);

const selectedCustomer = ref('');
</script>

<style scoped lang="scss">
.main {
  margin: 0 20px;
}
.customer-type {
  width: 500px;
  margin: 0 auto;
}
</style>
