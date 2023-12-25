<script setup lang="ts">
import { ref, watch } from 'vue';

import TopBottomLayout from '@/layouts/TopBottomLayout.vue';
import TopView from '@/pages/CaseControl/Content/TopView.vue';
import ResultsParaclinic from '@/pages/ResultsParaclinic.vue';
import UrlData from '@/UrlData';
import AggregateLaboratory from '@/fields/AggregateLaboratory.vue';
import AggregateDesc from '@/fields/AggregateDesc.vue';

const props = defineProps<{
  caseId?: number | null;
  view?: string | null;
  value?: number | null;
}>();

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'input', value: number | null): void
  (e: 'close-view'): void
  (e: 'close-direction'): void
}>();

const openedDirection = ref<number | null>(null);

const updateData = () => {
  UrlData.set({ pk: props.caseId, childrenDirection: openedDirection.value, view: props.view });
};

watch(() => props.value, () => {
  const pk = props.value;
  setTimeout(() => {
    openedDirection.value = pk;
  }, 10);
}, {
  immediate: true,
});

watch(() => props.view, (prevView) => {
  if (prevView) {
    openedDirection.value = null;
  }
  updateData();
});

watch(() => openedDirection.value, () => {
  emit('input', openedDirection.value);
  updateData();
});
</script>

<template>
  <div>
    <TopBottomLayout
      v-if="props.caseId && props.view"
      :top-height-px="80"
      :top-padding-px="5"
      top-scrollable
      :hide-top="props.view === 'closing'"
    >
      <template #top>
        <TopView
          v-model="openedDirection"
          :case-id="props.caseId"
          :view="props.view"
          @close-view="emit('close-view')"
          @close-direction="emit('close-direction')"
        />
      </template>
      <template #bottom>
        <ResultsParaclinic
          v-if="openedDirection"
          :key="openedDirection"
          :direction-id-to-open="openedDirection"
          :case-id="props.caseId"
          kk="case"
        />
        <div
          v-else
          :key="`${props.caseId}_${props.view}`"
          :class="$style.aggregate"
        >
          <AggregateLaboratory
            v-if="props.view === 'laboratory'"
            :case-direction="props.caseId"
            disabled
          />
          <AggregateDesc
            v-else-if="['paraclinical', 'consultation', 'morfology', 'forms'].includes(props.view)"
            :key="`desc_${props.caseId}_${props.view}`"
            :case-direction="props.caseId"
            :r_type="props.view"
            disabled
          />
        </div>
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
.aggregate {
  padding: 10px;
}
</style>
