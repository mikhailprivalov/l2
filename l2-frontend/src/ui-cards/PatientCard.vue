<template>
  <div>
    <patient></patient>
    <card></card>
  </div>
</template>

<script lang="ts">
import Patient from './Patient.vue';
import Card from './Card.vue';

export default {
  name: 'patient-card',
  components: { Patient, Card },
};
</script>
