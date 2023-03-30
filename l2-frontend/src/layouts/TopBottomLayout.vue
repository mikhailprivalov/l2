<template>
  <div :class="$style.root">
    <div
      :class="$style.top"
      :style="topStyle"
    >
      <slot name="top" />
    </div>
    <div
      :class="$style.bottom"
      :style="bottomStyle"
    >
      <slot name="bottom" />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue';

const props = withDefaults(defineProps<{
  topHeightPx?: number,
}>(), { topHeightPx: 100 });

const topStyle = computed(() => ({ height: `${props.topHeightPx}px` }));
const bottomStyle = computed(() => ({ top: topStyle.value.height }));
</script>

<style module lang="scss">
.root {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
}

.top, .bottom {
  position: absolute;
  right: 0;
  left: 0;
}

.top {
  border-bottom: 1px solid #646d78;
  top: 0;
}

.bottom {
  bottom: 0;
}
</style>
