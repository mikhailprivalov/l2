<template>
  <VueTippyDiv
    :tag="props.tag"
  >
    <a
      v-if="props.link && props.showLink"
      class="a-under"
      target="_blank"
      :href="props.link"
      :class="props.gender === 'ж' ? 'women' : 'men'"
    >
      {{ props.text }}
    </a>
    <p
      v-else
      class="text"
    >
      {{ props.text }}
    </p>
  </VueTippyDiv>
</template>

<script setup lang="ts">
import VueTippyDiv from '@/pages/ManageChambers/components/VueTippyDiv.vue';

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
  gender: {
    type: String,
    required: false,
  },
});

</script>

<style scoped lang="scss">
.text {
  margin: 0;
}
.women {
  color: #ff73ea;
}
.man {
  color: #00bfff;
}
</style>
