<template>
  <td
    v-tippy
    :title="show ? text : null"
    @mouseenter="showTitle"
  >
    {{ text }}
  </td>
</template>

<script>
export default {
  name: 'VueTippyTd',
  props: {
    text: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      title: '',
      show: false,
    };
  },
  methods: {
    showTitle(event) {
      this.show = event.target.scrollWidth > event.target.clientWidth;
    },
  },
};
</script>

<style scoped>
</style>
