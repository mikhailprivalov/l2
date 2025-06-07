<template>
  <div class="column-row">
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
      class="fa column-icon"
      :class="selectedPositionIds.length > 0 ? 'fa-filter-circle-xmark': 'fa-filter'"
    />
    <i
      v-if="currentSort === 'none'"
      class="fa fa-sort column-icon"
      @click="changeSort"
    />
    <i
      v-else-if="currentSort === 'asc'"
      class="fa fa-sort-up column-icon"
      @click="changeSort"
    />
    <i
      v-else
      class="fa fa-sort-down column-icon"
      @click="changeSort"
    />
    <div
      id="tempPositionFilter"
      class="tp"
    >
      <Treeselect
        v-model="selectedPositionIds"
        :options="positions"
        :normalizer="normalizer"
        class="treeselect-34px"
        placeholder="Должности"
        :multiple="true"
        :always-open="true"
      >
        <label
          slot="option-label"
          slot-scope="{ node }"
          v-tippy="{
            maxWidth: '50%'
          }"
          class="treeselect-options"
          :title="node.label"
        > {{ node.label }}</label>
      </Treeselect>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
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
    default: () => [],
  },
});
const emit = defineEmits(['input', 'sort']);

const selectedPositionIds = ref([]);

watch(selectedPositionIds, () => {
  emit('input', selectedPositionIds.value);
});
const positions = ref([]);
watch(() => props.employeePositions, () => {
  selectedPositionIds.value = [];
  positions.value = props.employeePositions.filter(employee => {
    const isDuplicate = positions.value.includes(employee.position);
    if (!isDuplicate) {
      positions.value.push(employee.position);
      return true;
    }
    return false;
  });
});
const normalizer = (node) => ({
  id: node.position,
  label: node.position,
});

const sortVariant = ref(['asc', 'desc', 'none']);
const currentSort = ref('none');
const changeSort = () => {
  const currentIndex = sortVariant.value.indexOf(currentSort.value);
  if (currentIndex === 2) {
    [currentSort.value] = sortVariant.value;
  } else {
    currentSort.value = sortVariant.value[currentIndex + 1];
  }
};

watch(currentSort, () => {
  emit('sort', currentSort.value);
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
.treeselect-options {
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
  margin-bottom: 0;
  padding-top: 6px;
}
</style>
