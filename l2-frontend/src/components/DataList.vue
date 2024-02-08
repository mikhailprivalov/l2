<template>
  <EditableList
    v-model="selectedId"
    :rows="rows"
    :is-loading="status !== ApiStatus.SUCCESS"
    :loading-text="props.loadingText"
    :add-text="props.addText"
    :with-name-filter="withNameFilter"
    :with-creating="props.withCreating"
    :selectable="props.selectable"
    :view-params="viewParams"
    @edit="openEdit"
  />
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';

import EditableList, {
  Id, IdOptional, ListElement, ViewParams,
} from '@/components/EditableList.vue';
import useApi, { ApiStatus } from '@/api/useApi';

const props = defineProps<{
  listUrl: string,
  listRequestParams?: Record<string, any>,
  value?: Id,
  loadingText?: string,
  addText?: string,
  withCreating?: boolean,
  withNameFilter?: boolean,
  selectable?: boolean,
}>();

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'input', id: IdOptional): void
  (e: 'edit', id: IdOptional): void
}>();

const apiParams = computed(() => ({
  path: props.listUrl,
  data: props.listRequestParams,
}));

interface ApiType {
  rows?: ListElement[],
  result?: {rows: ListElement[]},
  viewParams?: ViewParams,
}

const {
  data,
  status,
  call: reload,
} = useApi<ApiType>(apiParams, { defaultData: { rows: [] } });

const viewParams = computed(() => data.value?.viewParams);

const selectedId = ref<IdOptional>(null);

watch(
  selectedId,
  () => {
    emit('input', selectedId.value);
  },
);

const inputValue = computed(() => props.value);
watch(
  inputValue,
  () => {
    if (selectedId.value !== inputValue.value) {
      selectedId.value = inputValue.value;
    }
  },
  {
    immediate: true,
  },
);

const openEdit = (id: IdOptional) => {
  emit('edit', id);
};

const rows = computed<ListElement[]>(() => {
  if (Array.isArray(data.value.rows)) {
    return data.value.rows;
  }

  if (Array.isArray(data.value.result?.rows)) {
    return data.value.result.rows;
  }

  return [];
});

defineExpose({ reload });
</script>
