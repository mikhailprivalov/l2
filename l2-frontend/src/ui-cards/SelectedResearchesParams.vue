<template>
  <div
    v-if="research.show"
    class="root"
  >
    <template v-if="selected_card.pk">
      <ResultsByYear
        :card_pk="selected_card.pk"
        is-doc-referral
      />
      <ResultsByYear
        :card_pk="selected_card.pk"
        is-paraclinic
      />
      <ResultsByYear
        :card_pk="selected_card.pk"
        is-lab
      />
    </template>
    <DescriptiveForm
      :research="research"
      :confirmed="false"
      :patient="card"
    />
  </div>
</template>

<script lang="ts">
export default {
  name: 'SelectedResearchesParams',
  components: {
    DescriptiveForm: () => import('@/forms/DescriptiveForm.vue'),
    ResultsByYear: () => import('@/ui-cards/PatientResults/ResultsByYear.vue'),
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
  computed: {
    card() {
      return {
        card_pk: this.selected_card.pk,
        ...this.selected_card,
      };
    },
  },
};
</script>

<style scoped lang="scss">
.results {
  z-index: 1000;
}

.root {
  width: 100%;
  min-width: 500px;
}
</style>
