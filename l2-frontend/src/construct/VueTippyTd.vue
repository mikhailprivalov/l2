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

<script setup lang="ts">
import { ref } from 'vue';

defineProps<{
  text: string;
  tippyMaxWidth?: string;
}>();

const show = ref(false);

const showTitle = (event: MouseEvent) => {
  const target = event.target as HTMLElement;
  if (target.scrollWidth > target.clientWidth) {
    show.value = true;
  } else {
    show.value = false;
    target.removeAttribute('data-original-title');
  }
};
</script>
