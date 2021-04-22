<template>
  <tr v-if="show">
    <td colspan="6">
      <ResultsByYear :card_pk="selected_card.pk" isDocReferral/>
      <ResultsByYear :card_pk="selected_card.pk" isParaclinic/>
      <ResultsByYear :card_pk="selected_card.pk" isLab/>
      <DescriptiveForm
        :research="research"
        :confirmed="false"
        :patient="selected_card"/>
    </td>
  </tr>
</template>

<script>

export default {
  name: "SelectedResearchesParams",
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
    },
    show:{
      type: Boolean,
      required: true,
    }
  },
  data(){
    return {
    }
  },
  mounted() {
    console.log(this.research)
  }
}
</script>

<style scoped lang="scss">
 .results {
   z-index: 1000;
}
</style>
