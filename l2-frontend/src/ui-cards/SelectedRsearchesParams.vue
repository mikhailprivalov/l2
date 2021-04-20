<template>
  <tr v-if="research.show">
    <td colspan="5">
      <ResultsByYear class="results" :card_pk="selected_card.pk" isDocReferral/>
      <ResultsByYear class="results" :card_pk="selected_card.pk" isParaclinic/>
      <ResultsByYear class="results" :card_pk="selected_card.pk" isLab/>
      <DescriptiveForm
        :research="research"
        :confirmed="false"
        :patient="selected_card"/>
    </td>
  </tr>
</template>

<script>

export default {
  name: "SelectedRsearchesParams",
  components: {
    'DescriptiveForm': () => import('@/forms/DescriptiveForm'),
    'ResultsByYear': () => import('@/ui-cards/PatientResults/ResultsByYear'),
  },
  props: {
    research: {
      type: Object,
      required: true,
    },
    selected_card: {
      type: Object,
    }
  },
  data(){
    return {
    }
  },
}
</script>

<style scoped lang="scss">
.results {
  z-index: 1000;
}
</style>
