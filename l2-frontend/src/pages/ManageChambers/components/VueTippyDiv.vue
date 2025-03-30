<template>
  <component
    :is="tag"
    v-tippy="{
      maxWidth: props.tippyMaxWidth,
    }"
    :title="show ? props.text : null"
    @mouseenter="showTitle"
  >
    <slot />
    {{ props.text }}
  </component>
</template>

<script setup lang="ts">

import { ref } from 'vue';

const props = defineProps({
  text: {
    type: [String, undefined, null],
    required: false,
  },
  tippyMaxWidth: {
    type: String,
    required: false,
  },
  tag: {
    type: String,
    required: false,
    default: 'div',
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
