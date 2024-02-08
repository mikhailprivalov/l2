<template>
  <EditableList
    v-model="selectedId"
    :rows="rows"
    selectable
  />
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';

import EditableList, {
  type Id,
  type IdOptional,
  type ListElement,
} from './EditableList.vue';

export interface ListElementSimple {
  id: Id,
  name: string,
}

const props = defineProps<{
  rows: ListElementSimple[],
  value?: Id,
}>();

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'input', id: IdOptional): void
}>();

const selectedId = ref<IdOptional>(null);

watch(
  selectedId,
  () => {
    emit('input', selectedId.value);
  },
);

const rows = computed<ListElement[]>(() => {
  if (Array.isArray(props.rows)) {
    return props.rows.map(r => ({
      id: r.id,
      name: r.name,
      createdAt: null,
      updatedAt: null,
      isActive: true,
    }));
  }

  return [];
});
</script>
