<template>
  <component
    :is="tag"
    v-tippy="{
      maxWidth: props.tippyMaxWidth,
    }"
    :title="show ? props.text : null"
    @mouseenter="showTitle"
  >
    <a
      v-if="props.link && props.showLink"
      class="a-under"
      target="_blank"
      :href="props.link"
    >
      {{ props.text }}
    </a>
    <p
      v-else
      class="text"
    >
      {{ props.text }}
    </p>
  </component>
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
  tag: {
    type: String,
    required: false,
    default: 'div',
  },
  showLink: {
    type: Boolean,
    required: false,
  },
  link: {
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

// eslint-disable-next-line max-len
</script>

<style scoped lang="scss">
.text {
  margin: 0;
}
</style>
