<template>
  <div>
    <div
      ref="content"
      :class="{ [$style.collapsed]: !isExpanded && isCollapsible }"
      :style="contentStyle"
    >
      <slot />
    </div>
    <button
      v-if="isCollapsible"
      :class="$style.button"
      @click="toggle"
    >
      {{ isExpanded ? 'Свернуть' : 'Развернуть' }}
    </button>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  nextTick,
  onMounted,
  onUpdated,
  ref,
  useSlots,
} from 'vue';

const props = defineProps({
  maxHeight: {
    type: String,
    default: '200px',
  },
  bgColor: {
    type: String,
    default: 'white',
  },
});

const content = ref<HTMLElement | null>(null);
const isCollapsible = ref(false);
const isExpanded = ref(false);
const slots = useSlots();

const contentStyle = computed(() => {
  const style: Record<string, string> = {};
  if (!isExpanded.value && isCollapsible.value) {
    style['max-height'] = props.maxHeight;
    style['--collapse-bg'] = props.bgColor;
  } else {
    style['max-height'] = 'none';
  }
  return style;
});

const checkHeight = async () => {
  await nextTick();
  if (content.value) {
    const contentHeight = content.value.scrollHeight;
    if (contentHeight > parseInt(props.maxHeight, 10)) {
      isCollapsible.value = true;
    }
  }
};

const toggle = () => {
  isExpanded.value = !isExpanded.value;
};

onMounted(() => {
  checkHeight();
});

onUpdated(() => {
  if (slots.default) {
    checkHeight();
  }
});
</script>

<style lang="scss" module>
.collapsed {
  overflow: hidden;
  position: relative;

  &::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 50px;
    background: linear-gradient(to bottom, transparent, var(--collapse-bg, white));
    pointer-events: none;
  }
}

.button {
  background: #f1f3f5;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 4px 12px;
  margin-top: 8px;
  cursor: pointer;
  font-size: 12px;
  color: #495057;
  font-weight: 500;

  &:hover {
    background: #e9ecef;
  }
}
</style>
