<template>
  <div :class="$style.root">
    <div :class="$style.filterWrapper">
      <input
        v-model.trim="filter"
        type="text"
        class="form-control nbr"
        :class="$style.filterInput"
        placeholder="Фильтр"
      >
    </div>

    <div :class="$style.listWrapper">
      <div
        v-if="status !== ApiStatus.SUCCESS"
      >
        LOADING
      </div>
      <template v-else>
        <div
          v-for="e in filteredRows"
          :key="e.id"
        >
          {{ e.name }}
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';

import useApi, { ApiStatus } from '@/api/useApi';

type Id = number | string;
type IdOptional = Id | null;

interface ListElement {
  id: Id,
  name: string,
}

const props = defineProps<{
  source: string,
  value?: Id,
}>();

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'input', id: IdOptional): void
}>();

const { data, status } = useApi<{rows: ListElement[]}>({
  path: props.source,
}, { defaultData: { rows: [] } });

const selectedId = ref<IdOptional>(null);

watch(
  selectedId,
  () => {
    emit('input', selectedId.value);
  },
);

const filter = ref('');

const filteredRows = computed<ListElement[]>(() => {
  if (filter.value === '') {
    return data.value.rows;
  }
  return data.value.rows.filter(row => row.name.includes(filter.value));
});
</script>

<style lang="scss" module>
.root {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
}

.filterWrapper {
  position: absolute;
  top: 0;
  right: 0;
  left: 0;
  height: 34px;
}

.filterInput {
  border-top: 0;
  border-right: 0;
  border-left: 0;
}

.listWrapper {
  position: absolute;
  top: 34px;
  right: 0;
  bottom: 0;
  left: 0;
  overflow-x: visible;
  overflow-y: auto;
}
</style>
