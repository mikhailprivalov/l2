<template>
  <div>
    {{individual}} {{research}}
  </div>
</template>

<script>
  export default {
    name: 'last-result',
    props: {
      individual: {
        type: Number
      },
      research: {
        type: Number
      }
    }
  }
</script>

<style scoped>

</style>
