<template>
  <VueTippyDiv
    :tag="props.tag"
    :text="props.text"
  >
    <div class="top-icons">
      <i class="fa-solid fa-copy" />
      <i class="fa-solid fa-paste" />
      <i class="fa-solid fa-xmark" />
    </div>
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
});

</script>

<style scoped lang="scss">
.text {
  margin: 0;
}
.top-icons {
  display: flex;
  justify-content: flex-end;
  gap: 5px;
}
</style>
