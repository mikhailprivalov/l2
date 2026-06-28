<template>
  <div v-if="visible">
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import { vField } from './visibility-triggers';

const props = defineProps<{
  group?: any;
  groups?: any;
  formula?: any;
  patient?: any;
  paid_fin_source?: any;
  is_gistology?: any;
}>();

const visible = computed(() => {
  if (props.is_gistology && props.paid_fin_source) {
    if (props.formula === 'платно') {
      return true;
    }
  }
  if (props.is_gistology && !props.paid_fin_source) {
    if (props.formula === '!платно') {
      return true;
    }
  }

  return vField(props.group, props.groups, props.formula, props.patient);
});
</script>
