<template>
  <div>
    <a href="#" @click.prevent="select_research(row.pk)" class="research-select"
       :class="{ active: research_selected(row.pk) }"
       :key="row.pk"
       v-for="row in researches_display" :title="row.title"><span>{{ row.title }}</span></a>
  </div>
</template>

<script>
export default {
  name: 'researches-options',
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
