<template>
  <div>
    <patient></patient>
    <card></card>
  </div>
</template>

<script>
  import Patient from './Patient'
  import Card from './Card'

  export default {
    name: 'patient-card',
    components: {Patient, Card}
  }
</script>

<style scoped>

</style>
