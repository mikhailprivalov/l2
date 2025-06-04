<template>
  <div class="column-row">
    <p class="column-text">
      {{ props.columnText }}
    </p>
    <i
      v-tippy="{
        html: `#tempPositionFilter`,
        arrow: true,
        reactive: true,
        interactive: true,
        animation: 'fade',
        duration: 0,
        theme: 'light',
        placement: 'bottom',
        trigger: 'click',
      }"
      class="fa fa-filter column-icon"
    />
    <div
      id="tempPositionFilter"
      class="tp"
    >
      <Treeselect
        v-model="selectedPositionIds"
        :options="props.employeePosition"
        class="treeselect-34px"
        placeholder="Должности"
        :normalizer="normalizer"
        :multiple="true"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

const props = defineProps({
  columnText: {
    type: String,
    required: true,
  },
  employeePositions: {
    type: Array,
    required: true,
  },
});
const emit = defineEmits(['input']);

const selectedPositionIds = ref('');

const normalizer = (node) => ({
  id: node.position,
  label: node.position,
});
</script>

<style scoped lang="scss">
.column-row {
  display: flex;
  gap: 2px;
  padding: 7px 0;
}
.column-text {
  margin: 0;
}
.column-icon {
  padding: 3px;
  color: #636e7e;
}
.tp {
  height: auto;
  width: 150px;
}
</style>
