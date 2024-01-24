<template>
  <td
    v-tippy="{
      maxWidth: tippyMaxWidth,
    }"
    :title="show ? text : null"
    @mouseenter="showTitle"
  >
    {{ text }}
  </td>
</template>

<script lang="ts">
export default {
  name: 'VueTippyTd',
  props: {
    text: {
      type: String,
      required: true,
    },
    tippyMaxWidth: {
      type: String,
      required: false,
    },
  },
  data() {
    return {
      show: false,
    };
  },
  methods: {
    showTitle(event) {
      if (event.target.scrollWidth > event.target.clientWidth) {
        this.show = true;
      } else {
        this.show = false;
        event.target.removeAttribute('data-original-title');
      }
    },
  },
};
</script>

<style scoped>
</style>
