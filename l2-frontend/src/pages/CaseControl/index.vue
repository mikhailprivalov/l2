<script setup lang="ts">
import { ref, watch } from 'vue';

import TwoSidedLayout from '@/layouts/TwoSidedLayout.vue';
import Sidebar from '@/pages/CaseControl/Sidebar/index.vue';
import Content from '@/pages/CaseControl/Content/index.vue';

const caseId = ref<number | null>(null);
const view = ref<string | null>(null);
const direction = ref<number | null>(null);

watch(caseId, () => {
  direction.value = null;
  view.value = null;
});
</script>

<template>
  <TwoSidedLayout light-right>
    <template #left>
      <Sidebar
        @open-case="id => caseId = id"
        @open-view="v => view = v"
        @open-direction="(v, d) => {view = v; direction = d;}"
      />
    </template>
    <template #right>
      <Content
        v-model="direction"
        :case-id="caseId"
        :view="view"
        @close-view="view = null"
      />
    </template>
  </TwoSidedLayout>
</template>

<script lang="ts">
export default {
  name: 'CaseControl',
};
</script>
