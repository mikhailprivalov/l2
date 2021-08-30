<template>
  <div>
    <a :href="`/ui/directions?card_pk=${patient.cardId}&base_pk=${patient.base}`" target="_blank" class="a-under">
      {{ patient.fio_age }}
    </a>
  </div>
</template>

<script lang="ts">
export default {
  props: {
    patient: Object,
  },
};
</script>
