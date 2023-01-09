<template>
  <TwoSidedLayout>
    <template #left>
      <div class="counter__title">
        <h2>Counter</h2>
      </div>
      <div class="counter__value">
        <h2>{{ count }}</h2>
      </div>
    </template>
    <template #right>
      <div class="counter__buttons">
        <button @click="increment">
          Increment
        </button>
        <button @click="decrement">
          Decrement
        </button>
      </div>
    </template>
  </TwoSidedLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue';

import TwoSidedLayout from '@/layouts/TwoSidedLayout.vue';

const count = ref(0);

const increment = () => {
  count.value++;
};

const decrement = () => {
  count.value--;
};
</script>

<style lang="scss" scoped>
</style>
