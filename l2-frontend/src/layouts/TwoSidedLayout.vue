<template>
  <div
    ref="rootEl"
    :class="[$style.root, dragging && $style.dragging]"
  >
    <div
      :class="[$style.left, props.resizable && $style.leftResizable]"
      :style="leftStyle"
    >
      <slot name="left" />
    </div>
    <div
      v-if="props.resizable"
      :class="[$style.gutter, dragging && $style.gutterActive]"
      @pointerdown="onPointerDown"
      @pointermove="onPointerMove"
      @pointerup="stopDrag"
      @pointercancel="stopDrag"
    />
    <div :class="[$style.right, props.lightRight && $style.light]">
      <slot name="right" />
    </div>
  </div>
</template>

<script lang="ts" setup>
import {
  computed, onBeforeUnmount, onMounted, ref, watch,
} from 'vue';

const props = withDefaults(defineProps<{
  lightRight?: boolean;
  leftWidthPx?: number;
  resizable?: boolean;
  minLeftWidthPx?: number;
  minRightWidthPx?: number;
}>(), {
  leftWidthPx: 320,
  minLeftWidthPx: 360,
  minRightWidthPx: 400,
});

const emit = defineEmits(['update:leftWidthPx', 'update:left-width-px']);

const rootEl = ref<HTMLElement | null>(null);
const dragging = ref(false);
const leftWidth = ref(props.leftWidthPx);

watch(() => props.leftWidthPx, value => {
  if (value !== leftWidth.value) {
    leftWidth.value = value;
  }
});

const leftStyle = computed(() => ({
  width: `${leftWidth.value}px`,
}));

const clampWidth = (width: number) => {
  const rootWidth = rootEl.value?.clientWidth ?? 0;
  const maxLeft = rootWidth > 0
    ? Math.max(props.minLeftWidthPx, rootWidth - props.minRightWidthPx)
    : width;
  return Math.min(maxLeft, Math.max(props.minLeftWidthPx, width));
};

const setLeftWidth = (width: number) => {
  const next = clampWidth(width);
  if (next === leftWidth.value) {
    return;
  }
  leftWidth.value = next;
  emit('update:leftWidthPx', next);
  emit('update:left-width-px', next);
};

const onPointerDown = (event: PointerEvent) => {
  if (event.pointerType === 'mouse' && event.button !== 0) {
    return;
  }
  dragging.value = true;
  (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
  event.preventDefault();
};

const onPointerMove = (event: PointerEvent) => {
  if (!dragging.value || !rootEl.value) {
    return;
  }
  const rect = rootEl.value.getBoundingClientRect();
  setLeftWidth(event.clientX - rect.left);
};

const stopDrag = () => {
  dragging.value = false;
};

const onWindowResize = () => {
  if (!props.resizable) {
    return;
  }
  setLeftWidth(leftWidth.value);
};

onMounted(() => {
  if (props.resizable) {
    setLeftWidth(leftWidth.value);
  }
  window.addEventListener('resize', onWindowResize);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', onWindowResize);
});
</script>

<style module lang="scss">
.root {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
}

.dragging {
  cursor: col-resize;
  user-select: none;

  iframe {
    pointer-events: none;
  }
}

.light {
  background: #fff;
}

.left, .right {
  height: 100%;
  position: relative;
}

.left {
  flex: 0 0 auto;
  border-right: 1px solid #646d78;
  padding: 0;
}

.leftResizable {
  border-right: none;
}

.gutter {
  flex: 0 0 5px;
  width: 5px;
  height: 100%;
  cursor: col-resize;
  z-index: 2;
  touch-action: none;
  position: relative;
  background: transparent;

  &::after {
    content: '';
    position: absolute;
    top: 0;
    bottom: 0;
    left: 2px;
    width: 1px;
    background: #646d78;
  }

  &:hover::after {
    left: 1px;
    width: 3px;
    background: #049372;
  }
}

.gutterActive::after {
  left: 1px;
  width: 3px;
  background: #049372;
}

.right {
  flex: 1;
  min-width: 0;
}
</style>
