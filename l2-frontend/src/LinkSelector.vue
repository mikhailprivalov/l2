<template>
  <div>A {{value}}</div>
</template>

<script>
  export default {
    name: 'link-selector',
    props: {
      options: {
        type: Array,
        required: true
      },
      value: {}
    }
  }
</script>

<style scoped>

</style>
