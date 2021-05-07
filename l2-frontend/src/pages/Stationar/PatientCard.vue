<template>
  <div>
    <a :href="`/mainmenu/directions?card_pk=${patient.cardId}&base_pk=${patient.base}`"
       target="_blank" class="a-under">
      {{ patient.fio_age }}
    </a>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';

import Patient from '@/types/patient';

@Component({
  props: {
    patient: Patient,
  },
})
export default class PatientCard extends Vue {}
</script>
