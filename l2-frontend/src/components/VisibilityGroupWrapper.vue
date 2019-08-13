<template>
  <div v-if="visible">
    <slot></slot>
  </div>
</template>

<script>
  import {vGroup} from './visibility-triggers'

  export default {
    name: 'VisibilityGroupWrapper',
    props: ['group', 'groups', 'formula'],
    computed: {
      visible() {
        return vGroup(this.group, this.groups, this.formula);
      },
    },
  }
</script>
