<template>
  <div>
    <a :href="`/mainmenu/directions?card_pk=${patient.cardId}&base_pk=${patient.base}`"
       target="_blank" class="a-under">
      {{patient.fio_age}}
    </a>
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
