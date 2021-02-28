<template>
  <div class="root">
    <div class="search-place">
      <SearchToEnter :laboratory="currentLaboratory"/>
      <ReadyToEnter :laboratory="currentLaboratory" class="ready-to-enter"/>
    </div>
    <div class="direction-form">b</div>
    <div class="results-form">c</div>
  </div>
</template>

<script>
import SearchToEnter from "@/pages/LaboratoryResults/SearchToEnter";
import ReadyToEnter from "@/pages/LaboratoryResults/ReadyToEnter";

export default {
  components: {ReadyToEnter, SearchToEnter},
  name: 'laboratory-results',
  data() {
    return {
      currentLaboratory: -1,
    };
  },
  watch: {},
  mounted() {
    this.$root.$on('change-laboratory', pk => {
      this.currentLaboratory = pk;
    });
  },
  methods: {},
  computed: {},
}
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
  overflow-y: auto;
}

.search-place {
  left: 0;
  width: 350px;
  border-right: 1px solid #b1b1b1;
  overflow-y: visible;
}

.direction-form {
  left: 350px;
  width: 360px;
  border-right: 1px solid #b1b1b1;
}

.results-form {
  right: 0;
  left: 710px;
}

.ready-to-enter {
  position: absolute;
  top: 34px;
  left: 0;
  right: 0;
}
</style>
