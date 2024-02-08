<template>
  <DataList
    ref="dataList"
    v-model="selectedId"
    list-url="edit-forms/objects/search"
    :list-request-params="listRequestParams"
    :with-name-filter="withNameFilter"
    :with-creating="props.withCreating"
    :loading-text="props.loadingText"
    :add-text="props.addText"
    :selectable="selectable"
    @edit="openEdit"
  />
</template>

<script setup lang="ts">
import {
  computed, onMounted, ref, watch,
} from 'vue';

import { useStore } from '@/store';
import { EDIT_OPEN, EDIT_SAVED_OBJECT } from '@/store/action-types';

import DataList from './DataList.vue';
import { Id, IdOptional } from './EditableList.vue';

const props = defineProps<{
  formType: string,
  filters?: Record<string, any>,
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
}>();

const store = useStore();

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

const openEdit = (editId: IdOptional) => {
  store.dispatch(EDIT_OPEN, { editId, formType: props.formType });
};

const dataList = ref<InstanceType<typeof DataList> | null>(null);

onMounted(() => {
  store.subscribeAction(action => {
    if (
      action.type === EDIT_SAVED_OBJECT
      && (
        action.payload?.formType === props.formType
        || store.getters.editStackHasFormType(props.formType)
      )
      && action.payload?.result
    ) {
      if (dataList.value) {
        dataList.value.reload();
      }
    }
  });
});

const listRequestParams = computed(() => {
  const r: Record<string, any> = {
    formType: props.formType,
    returnTotalRows: true,
  };

  if (props.filters) {
    r.filters = props.filters;
  }

  return r;
});
</script>
