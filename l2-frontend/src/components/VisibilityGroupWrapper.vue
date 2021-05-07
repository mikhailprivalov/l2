<template>
  <div v-if="visible">
    <slot></slot>
  </div>
</template>

<script>
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
