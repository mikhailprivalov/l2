<template>
  <div :class="$style.root">
    <div
      v-if="!props.hideTop"
      :class="topClass"
      :style="topStyle"
    >
      <slot name="top" />
    </div>
    <div
      :class="[$style.bottom, props.bottomScrollable && $style.scrollable]"
      :style="bottomStyle"
    >
      <slot name="bottom" />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, useCssModule } from 'vue';

const props = withDefaults(defineProps<{
  topHeightPx?: number,
  topPaddingPx?: number,
  topScrollable?: boolean,
  bottomScrollable?: boolean,
  hideTop?: boolean,
  /**
   * Включает режим разделения пополам: top и bottom по 50% высоты
   */
  splitHalf?: boolean,
  /**
   * Отключает нижнюю границу у top
   */
  noBorder?: boolean,
}>(), { topHeightPx: 100 });

const $style = useCssModule();

const topStyle = computed(() => {
  if (props.splitHalf) {
    return { height: '50%' };
  }
  const style: Record<string, string> = { height: `${props.topHeightPx}px` };

  if (props.topPaddingPx) {
    style.padding = `${props.topPaddingPx}px`;
  }

  return style;
});
const bottomStyle = computed(() => {
  if (props.splitHalf) {
    return { top: '50%', height: '50%' };
  }
  return { top: props.hideTop ? '0' : topStyle.value.height };
});

const topClass = computed(() => [
  $style.top,
  props.topScrollable && $style.scrollable,
  props.noBorder && $style.noBorder,
]);
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

  &.noBorder {
    border-bottom: none;
  }
}

.bottom {
  bottom: 0;
}

// splitHalf режим: top и bottom по 50%
:global(.split-half) .top {
  border-bottom: none;
}
</style>
