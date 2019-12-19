<template>
  <div>
    <div>{{patient.fio_age}}</div>
  </div>
</template>

<script>
    import Patient from '../../types/patient'

    export default {
        props: {
            patient: {
                type: Patient,
                required: true,
            }
        }
    }
</script>

<style scoped>

</style>
