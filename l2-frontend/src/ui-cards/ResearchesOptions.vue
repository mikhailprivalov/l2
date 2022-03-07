<template>
  <div>
    <a
      v-for="row in researches_display"
      :key="row.pk"
      href="#"
      class="research-select"
      :class="{ active: research_selected(row.pk) }"
      :title="row.title"
      @click.prevent="select_research(row.pk)"
    ><span>{{ row.title }}</span></a>
  </div>
</template>

<script lang="ts">
export default {
  name: 'ResearchesOptions',
  props: {
    value: {
      type: Array,
    },
    researches: {
      type: Array,
    },
  },
  data() {
    return {
      selected: [],
    };
  },
};
</script>

<style scoped>

</style>
