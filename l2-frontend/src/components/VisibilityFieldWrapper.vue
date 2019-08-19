<template>
  <div v-if="visible">
    <slot></slot>
  </div>
</template>

<script>
  import {vField} from './visibility-triggers'

  export default {
    name: 'VisibilityFieldWrapper',
    props: ['groups', 'formula'],
    computed: {
      visible() {
        return vField(this.groups, this.formula);
      },
    },
  }
</script>
