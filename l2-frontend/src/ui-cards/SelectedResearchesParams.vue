<template>
  <div v-if="research.show" class="root">
    <ResultsByYear :card_pk="selected_card.pk" isDocReferral/>
    <ResultsByYear :card_pk="selected_card.pk" isParaclinic/>
    <ResultsByYear :card_pk="selected_card.pk" isLab/>
    <DescriptiveForm
      :research="research"
      :confirmed="false"
      :patient="selected_card"/>
  </div>
</template>

<script>

export default {
  name: 'SelectedResearchesParams',
  components: {
    DescriptiveForm: () => import('@/forms/DescriptiveForm'),
    ResultsByYear: () => import('@/ui-cards/PatientResults/ResultsByYear'),
  },
  props: {
    research: {
      type: Object,
      required: true,
    },
    selected_card: {
      type: Object,
    },
  },
  data() {
    return {};
  },
};
</script>

<style scoped lang="scss">
.results {
  z-index: 1000;
}

.root {
  width: 100%;
  min-width: 1000px;
}
</style>
