<template>
  <div class="column-row">
    <i
      v-tippy="popover('#tempPositionFilter')"
      class="fa column-icon"
      :class="selectedPositionIds.length > 0 ? 'fa-filter-circle-xmark': 'fa-filter'"
    />
    <i
      v-tippy="popover('#tempPositionSorted')"
      class="fa fa-sort column-icon"
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
    <div
      id="tempPositionSorted"
      class="tp"
    >
      <Treeselect
        v-model="currentSort"
        :options="sortVariants"
        class="treeselect-34px"
        placeholder="Сортировать"
        :always-open="true"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import popover from '@/pages/WorkingTime/utils/tippy';

const props = defineProps({
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

const sortVariants = ref([
  { id: 'none', label: 'Нет' },
  { id: 'asc', label: 'А-Я' },
  { id: 'desc', label: 'Я-А' },
]);
const currentSort = ref('none');

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
