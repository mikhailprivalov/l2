<template>
  <div
    class="tube-item"
  >
    <div
      class="sq"
    >
      <div
        class="color-sq"
        :style="'background-color: ' + props.tube.color"
      />
    </div>
    <div> {{ props.tube.title }}</div>
  </div>
</template>

<script setup lang="ts">

import { PropType } from 'vue';

interface tube {
  pk: number,
  title: string,
  color: string,
}
const props = defineProps({
  tube: {
    type: Object as PropType<tube>,
    required: true,
  },
});
</script>

<style scoped lang="scss">
.tube-item {
  display: flex;
}
.sq {
    padding: 3px;
    display: inline-block;
    background-color: #efefef;
    border: 1px solid #bbb;
    border-radius: 5px;
    margin-right: 5px;
    vertical-align: middle;
}
.color-sq {
    height: 12px;
    width: 12px;
}
</style>
