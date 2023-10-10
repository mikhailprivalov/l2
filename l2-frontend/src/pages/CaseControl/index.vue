<script setup lang="ts">
import { ref, watch } from 'vue';

import TwoSidedLayout from '@/layouts/TwoSidedLayout.vue';
import Sidebar from '@/pages/CaseControl/Sidebar/index.vue';
import Content from '@/pages/CaseControl/Content/index.vue';
import UrlData from '@/UrlData';

let initialView = null;
let initialDirection = null;
let initialCase = null;

const storedData = UrlData.get();
if (storedData && typeof storedData === 'object') {
  initialView = storedData.view || null;
  initialDirection = storedData.childrenDirection || null;
  initialCase = storedData.pk || null;
}

const caseId = ref<number | null>(initialCase);
const view = ref<string | null>(initialView);
const direction = ref<number | null>(initialDirection);
const inited = ref<boolean>(!initialCase && !initialDirection);

watch(() => caseId.value, () => {
  if (inited.value) {
    direction.value = null;
    view.value = null;
  } else {
    inited.value = true;
  }
});
</script>

<template>
  <TwoSidedLayout
    light-right
  >
    <template #left>
      <Sidebar
        @open-case="id => caseId = id"
        @open-view="v => view = v"
        @open-direction="({case: c, view: v, id}) => {caseId = c; view = v; direction = id;}"
      />
    </template>
    <template #right>
      <Content
        v-model="direction"
        :case-id="caseId"
        :view="view"
        @close-view="view = null"
        @close-direction="direction = null"
      />
    </template>
  </TwoSidedLayout>
</template>

<script lang="ts">
export default {
  name: 'CaseControl',
};
</script>
