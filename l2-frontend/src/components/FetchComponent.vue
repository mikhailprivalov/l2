<template>
  <div>
    <Spinner v-if="status !== ApiStatus.SUCCESS && withLoader" />
    <slot
      v-else
      :status="status"
      :data="localData?.object || props.defaultData"
    />
  </div>
</template>

<script setup lang="ts">
import {
  computed, onMounted, ref, watch,
} from 'vue';

import { useStore } from '@/store';
import { Id } from '@/store/modules/edit';
import { EDIT_SAVED_OBJECT } from '@/store/action-types';
import Spinner from '@/components/Spinner.vue';
import useApi, { ApiStatus } from '@/api/useApi';

const props = withDefaults(defineProps<{
  formType: string,
  id: Id,
  defaultData?: any,
  withLoader?: boolean,
}>(), { defaultData: () => ({}) });

const store = useStore();

const apiParams = computed(() => ({
  path: 'edit-forms/objects/get-by-id',
  data: {
    formType: props.formType,
    id: props.id,
  },
}));

const {
  data,
  status,
} = useApi<any>(apiParams, { defaultData: props.defaultData });

const localData = ref(data.value);

watch(data, () => {
  localData.value = data.value;
});

onMounted(() => {
  store.subscribeAction(action => {
    if (
      action.type === EDIT_SAVED_OBJECT
      && (
        action.payload?.formType === props.formType
        || store.getters.editStackHasFormType(props.formType)
      )
      && action.payload?.id === props.id
      && action.payload?.result
    ) {
      localData.value = {
        object: action.payload.result,
      };
    }
  });
});
</script>
