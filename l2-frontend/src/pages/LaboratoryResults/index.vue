<template>
  <div class="root">
    <div class="search-place">
      <SearchToEnter :laboratory="currentLaboratory"/>
      <ReadyToEnter :laboratory="currentLaboratory" class="ready-to-enter"/>
    </div>
    <div class="direction-form">
      <DirectionForm :laboratory="currentLaboratory"/>
    </div>
    <div class="results-form">
      <ResultsForm/>
    </div>
  </div>
</template>

<script>
import SearchToEnter from '@/pages/LaboratoryResults/SearchToEnter.vue';
import ReadyToEnter from '@/pages/LaboratoryResults/ReadyToEnter.vue';
import DirectionForm from '@/pages/LaboratoryResults/DirectionForm.vue';
import ResultsForm from '@/pages/LaboratoryResults/ResultsForm.vue';

export default {
  components: {
    ResultsForm, DirectionForm, ReadyToEnter, SearchToEnter,
  },
  name: 'laboratory-results',
  data() {
    return {
      currentLaboratory: -1,
    };
  },
  watch: {},
  mounted() {
    this.$root.$on('change-laboratory', (pk) => {
      this.currentLaboratory = pk;
    });
    this.$root.$emit('emit-laboratory');
  },
  methods: {},
  computed: {},
};
</script>

<style scoped lang="scss">
.root {
  position: absolute;
  top: 36px;
  left: 0;
  right: 0;
  bottom: 0;
}

.search-place, .direction-form, .results-form, .ready-to-enter {
  position: absolute;
  top: 0;
  bottom: 0;
  overflow-x: visible;
  overflow-y: hidden;
}

.search-place {
  left: 0;
  width: 354px;
  border-right: 5px solid #e2e2e2;
  overflow-y: visible;
}

.direction-form {
  left: 354px;
  width: 365px;
  border-right: 5px solid #e2e2e2;
}

.results-form {
  right: 0;
  left: 719px;
}

.ready-to-enter {
  position: absolute;
  top: 34px;
  left: 0;
  right: 0;
}
</style>
