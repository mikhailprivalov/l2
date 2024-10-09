<template>
  <div
    v-tippy="{
      maxWidth: props.tippyMaxWidth,
    }"
    :title="show ? props.text : null"
    @mouseenter="showTitle"
  >
    {{ props.text }}
  </div>
</template>

<script setup lang="ts">

import { ref } from 'vue';

const props = defineProps({
  text: {
    type: [String, undefined, null],
    required: true,
  },
  tippyMaxWidth: {
    type: String,
    required: false,
  },
});

const show = ref(false);

const showTitle = (event) => {
  if (event.target.scrollWidth > event.target.clientWidth) {
    show.value = true;
  } else {
    show.value = false;
    event.target.removeAttribute('data-original-title');
  }
};

</script>

<style scoped lang="scss">

</style>
