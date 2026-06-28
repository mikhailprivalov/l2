<template>
  <div v-if="visible">
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import { vGroup } from './visibility-triggers';

const props = defineProps<{
  group?: any;
  groups?: any;
  patient?: any;
}>();

const visible = computed(() => vGroup(props.group, props.groups, props.patient));
</script>
