<template>
  <div class="paragraph-field">
    <div
      v-for="(item, index) in items"
      :key="item.id"
      class="paragraph-field__item"
    >
      <div class="paragraph-field__controls">
        <button
          type="button"
          class="paragraph-field__order-btn"
          :disabled="disabled || index === 0"
          title="Переместить вверх"
          @click="moveUp(index)"
        >
          ▲
        </button>
        <button
          type="button"
          class="paragraph-field__order-btn"
          :disabled="disabled || index === items.length - 1"
          title="Переместить вниз"
          @click="moveDown(index)"
        >
          ▼
        </button>
      </div>
      <textarea
        ref="textareaRefs"
        v-model="item.text"
        class="form-control paragraph-field__textarea"
        :disabled="disabled"
        :placeholder="`Параграф ${index + 1}`"
        :rows="initialRows"
        :style="{ maxHeight: maxHeightPx, minHeight: minHeightPx }"
        @input="onInput($event, index)"
      />
      <button
        v-if="!disabled"
        type="button"
        class="paragraph-field__remove"
        title="Удалить параграф"
        @click="removeItem(index)"
      >
        &times;
      </button>
    </div>

    <button
      v-if="!disabled"
      type="button"
      class="btn btn-blue-nb paragraph-field__add"
      @click="addItem"
    >
      Добавить параграф
    </button>

    <div
      v-if="items.length === 0 && disabled"
      class="paragraph-field__empty"
    >
      Нет данных
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed, nextTick, onMounted, ref, watch,
} from 'vue';

interface ParagraphItem {
  id: number;
  text: string;
}

const props = withDefaults(defineProps<{
  value: string;
  disabled?: boolean;
  lines?: number;
}>(), {
  disabled: false,
  lines: 3,
});

const emit = defineEmits<{(e: 'input', value: string): void;
}>();

const MAX_ROWS = 10;
const APPROX_LINE_PX = 20;

const initialRows = computed(() => Math.min(Math.max(props.lines || 3, 1), MAX_ROWS));
const maxHeightPx = computed(() => `${MAX_ROWS * APPROX_LINE_PX + 12}px`);
const minHeightPx = `${APPROX_LINE_PX + 12}px`;

const parseValue = (raw: string): ParagraphItem[] => {
  try {
    const parsed = JSON.parse(raw || '[]');
    if (!Array.isArray(parsed)) return [];
    return parsed
      .slice()
      .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
      .map((item, idx) => ({
        id: idx,
        text: item.text || '',
      }));
  } catch {
    return [];
  }
};

const items = ref<ParagraphItem[]>(parseValue(props.value));
let nextId = items.value.length;

const textareaRefs = ref<HTMLTextAreaElement[]>([]);

const emitValue = () => {
  emit('input', JSON.stringify(items.value.map((item, idx) => ({ text: item.text, order: idx }))));
};

const autosize = (el: HTMLTextAreaElement | undefined) => {
  if (!el) return;
  const cs = window.getComputedStyle(el);
  const lineH = parseFloat(cs.lineHeight) || APPROX_LINE_PX;
  const padTop = parseFloat(cs.paddingTop) || 0;
  const padBot = parseFloat(cs.paddingBottom) || 0;
  const borderTop = parseFloat(cs.borderTopWidth) || 0;
  const borderBot = parseFloat(cs.borderBottomWidth) || 0;
  const maxPx = lineH * MAX_ROWS + padTop + padBot + borderTop + borderBot;

  const { style } = el;
  style.height = 'auto';
  const contentH = el.scrollHeight + borderTop + borderBot;
  const newH = Math.min(contentH, maxPx);
  style.height = `${newH}px`;
  style.overflowY = contentH > maxPx ? 'auto' : 'hidden';

  if (contentH > maxPx && document.activeElement === el) {
    // eslint-disable-next-line no-param-reassign
    el.scrollTop = el.scrollHeight;
  }
};

const autosizeAll = () => {
  nextTick(() => {
    textareaRefs.value.forEach(autosize);
  });
};

const onInput = (e: Event, index: number) => {
  autosize(e.target as HTMLTextAreaElement);
  items.value[index].text = (e.target as HTMLTextAreaElement).value;
  emitValue();
};

const addItem = () => {
  items.value = [...items.value, { id: nextId++, text: '' }];
  emitValue();
  autosizeAll();
};

const removeItem = (index: number) => {
  items.value = items.value.filter((_, i) => i !== index);
  emitValue();
  autosizeAll();
};

const moveUp = (index: number) => {
  if (index === 0) return;
  const copy = [...items.value];
  [copy[index - 1], copy[index]] = [copy[index], copy[index - 1]];
  items.value = copy;
  emitValue();
  autosizeAll();
};

const moveDown = (index: number) => {
  if (index === items.value.length - 1) return;
  const copy = [...items.value];
  [copy[index], copy[index + 1]] = [copy[index + 1], copy[index]];
  items.value = copy;
  emitValue();
  autosizeAll();
};

watch(
  () => props.value,
  (newVal) => {
    const incoming = parseValue(newVal);
    const currentJson = JSON.stringify(items.value.map(it => it.text));
    const incomingJson = JSON.stringify(incoming.map(it => it.text));
    if (currentJson !== incomingJson) {
      items.value = incoming;
      nextId = incoming.length;
      autosizeAll();
    }
  },
);

watch(() => props.lines, autosizeAll);

onMounted(autosizeAll);
</script>

<style scoped>
.paragraph-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.paragraph-field__item {
  display: flex;
  align-items: flex-start;
  gap: 6px;
}

.paragraph-field__controls {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding-top: 4px;
  flex-shrink: 0;
}

.paragraph-field__order-btn {
  padding: 0 4px;
  height: 20px;
  font-size: 10px;
  line-height: 1;
  background: #f0f0f0;
  border: 1px solid #ccc;
  border-radius: 3px;
  cursor: pointer;
  color: #555;
  transition: background 0.15s;
}

.paragraph-field__order-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.paragraph-field__order-btn:not(:disabled):hover {
  background: #e0e0e0;
}

.paragraph-field__textarea {
  flex: 1 1 auto;
  resize: vertical;
  overflow-y: hidden;
}

.paragraph-field__remove {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  margin-top: 4px;
  border: 1px solid #e2b5b5;
  border-radius: 50%;
  background: #fff;
  color: #a33;
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.paragraph-field__remove:hover {
  background: #a33;
  color: #fff;
}

.paragraph-field__add {
  align-self: flex-start;
  color: #fff;
}

.paragraph-field__empty {
  color: #999;
  font-size: 13px;
  font-style: italic;
}
</style>
