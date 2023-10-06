<script setup lang="ts">
import { ref, watch } from 'vue';

import TopBottomLayout from '@/layouts/TopBottomLayout.vue';
import TopView from '@/pages/CaseControl/Content/TopView.vue';

const props = defineProps<{
  caseId?: number | null;
  view?: string | null;
  value?: number | null;
}>();

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'input', value: number): void
  (e: 'close-view'): void
}>();

const openedDirection = ref<number | null>(null);

watch(() => props.view, () => {
  openedDirection.value = null;
});
watch(() => props.caseId, () => {
  openedDirection.value = null;
});

watch(() => props.value, () => {
  openedDirection.value = props.value;
});

watch(openedDirection, () => {
  emit('input', openedDirection.value);
});

const openDirection = pk => {
  openedDirection.value = pk;
};
</script>

<template>
  <div>
    <TopBottomLayout
      v-if="props.caseId && props.view"
      :top-height-px="80"
      :top-padding-px="5"
      top-scrollable
    >
      <template #top>
        <TopView
          :case-id="props.caseId"
          :view="props.view"
          :selected-direction="openedDirection"
          @close-view="emit('close-view')"
          @open-direction="openDirection"
        />
      </template>
      <template #bottom>
        {{ openedDirection }}
      </template>
    </TopBottomLayout>
  </div>
</template>

<script lang="ts">
export default {
  name: 'CaseContent',
};
</script>

<style module lang="scss">

</style>
