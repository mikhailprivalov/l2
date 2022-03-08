<template>
  <div>
    <Patient />
    <Card />
  </div>
</template>

<script lang="ts">
import Patient from './Patient.vue';
import Card from './Card.vue';

export default {
  name: 'PatientCard',
  components: { Patient, Card },
};
</script>
