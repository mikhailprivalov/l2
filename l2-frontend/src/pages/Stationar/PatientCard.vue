<template>
  <div>
    <a :href="`/mainmenu/directions?card_pk=${patient.cardId}&base_pk=${patient.base}`"
       target="_blank" class="a-under">
      {{ patient.fio_age }}
    </a>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'
import Component from 'vue-class-component'

import Patient from '@/types/patient'

const PatientCardProps = Vue.extend({
  props: {
    patient: Patient
  }
});

@Component
export default class PatientCard extends PatientCardProps {}
</script>
