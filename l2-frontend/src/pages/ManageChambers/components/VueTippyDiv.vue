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
      v-if="props.historyId && showLink"
      class="a-under"
      target="_blank"
      :href="stationarLink(props.historyId)"
    >
      {{ props.text }}
    </a>
    <p v-else>
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
  historyId: {
    type: Number,
    required: false,
  },
  showLink: {
    type: Boolean,
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
const stationarLink = (historyId) => `/ui/stationar#{%22pk%22:${historyId},%22opened_list_key%22:null,%22opened_form_pk%22:null,%22every%22:false}`;
</script>

<style scoped lang="scss">

</style>
