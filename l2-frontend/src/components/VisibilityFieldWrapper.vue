<template>
  <div v-if="visible">
    <slot />
  </div>
</template>

<script lang="ts">
import { vField } from './visibility-triggers';

export default {
  name: 'VisibilityFieldWrapper',
  props: ['group', 'groups', 'formula', 'patient', 'paid_fin_source', 'is_gistology'],
  computed: {
    visible() {
      if (this.is_gistology && this.paid_fin_source) {
        if (this.formula === 'платно') {
          return true;
        }
      }
      if (this.is_gistology && !this.paid_fin_source) {
        if (this.formula === '!платно') {
          return true;
        }
      }

      return vField(this.group, this.groups, this.formula, this.patient);
    },
  },
};
</script>
