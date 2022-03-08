<template>
  <div v-if="visible">
    <slot />
  </div>
</template>

<script lang="ts">
import { vGroup } from './visibility-triggers';

export default {
  name: 'VisibilityGroupWrapper',
  props: ['group', 'groups', 'patient'],
  computed: {
    visible() {
      return vGroup(this.group, this.groups, this.patient);
    },
  },
};
</script>
