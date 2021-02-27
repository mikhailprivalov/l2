<template>
  <div class="root">
    <div class="search-form">
      <SearchToEnter/>
    </div>
    <div class="direction-form">b</div>
    <div class="results-form">c</div>
  </div>
</template>

<script>
import SearchToEnter from "@/pages/LaboratoryResults/SearchToEnter";

export default {
  components: {SearchToEnter},
  name: 'laboratory-results',
  data() {
    return {}
  },
  watch: {},
  created() {
  },
  mounted() {
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

.search-form, .direction-form, .results-form {
  position: absolute;
  top: 0;
  bottom: 0;
  overflow-x: visible;
  overflow-y: auto;
}

.search-form {
  left: 0;
  width: 350px;
  border-right: 1px solid #b1b1b1;
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
</style>
