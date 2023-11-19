<template>
  <div :class="$style.root">
    <div
      v-if="!props.hideTop"
      :class="[$style.top, props.topScrollable && $style.scrollable]"
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
  topPaddingPx?: number,
  topScrollable?: boolean,
  hideTop?: boolean,
}>(), { topHeightPx: 100 });

const topStyle = computed(() => {
  const style: Record<string, string> = { height: `${props.topHeightPx}px` };

  if (props.topPaddingPx) {
    style.padding = `${props.topPaddingPx}px`;
  }

  return style;
});
const bottomStyle = computed(() => ({ top: props.hideTop ? '0' : topStyle.value.height }));
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

  &.scrollable {
    overflow-x: auto;
    overflow-y: visible;
    white-space: nowrap;
  }
}

.bottom {
  bottom: 0;
}
</style>
