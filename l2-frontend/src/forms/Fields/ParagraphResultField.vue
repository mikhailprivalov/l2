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
        v-model="item.text"
        class="form-control paragraph-field__textarea"
        :disabled="disabled"
        :placeholder="`Параграф ${index + 1}`"
        rows="3"
        @input="emitValue"
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
      class="paragraph-field__add"
      @click="addItem"
    >
      + Добавить параграф
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
import { ref, watch } from 'vue';

interface ParagraphItem {
  id: number;
  text: string;
}

const props = defineProps<{
  value: string;
  disabled?: boolean;
}>();

const emit = defineEmits<{(e: 'input', value: string): void;
}>();

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

watch(
  () => props.value,
  (newVal) => {
    const incoming = parseValue(newVal);
    const currentJson = JSON.stringify(items.value.map(it => it.text));
    const incomingJson = JSON.stringify(incoming.map(it => it.text));
    if (currentJson !== incomingJson) {
      items.value = incoming;
      nextId = incoming.length;
    }
  },
);

const emitValue = () => {
  emit('input', JSON.stringify(items.value.map((item, idx) => ({ text: item.text, order: idx }))));
};

const addItem = () => {
  items.value = [...items.value, { id: nextId++, text: '' }];
  emitValue();
};

const removeItem = (index: number) => {
  items.value = items.value.filter((_, i) => i !== index);
  emitValue();
};

const moveUp = (index: number) => {
  if (index === 0) return;
  const copy = [...items.value];
  [copy[index - 1], copy[index]] = [copy[index], copy[index - 1]];
  items.value = copy;
  emitValue();
};

const moveDown = (index: number) => {
  if (index === items.value.length - 1) return;
  const copy = [...items.value];
  [copy[index], copy[index + 1]] = [copy[index + 1], copy[index]];
  items.value = copy;
  emitValue();
};
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
  min-height: 60px;
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
  padding: 5px 12px;
  font-size: 13px;
  background: #f4f8ff;
  border: 1px dashed #7aadde;
  border-radius: 4px;
  color: #3a76b0;
  cursor: pointer;
  transition: background 0.15s;
}

.paragraph-field__add:hover {
  background: #e5f0ff;
}

.paragraph-field__empty {
  color: #999;
  font-size: 13px;
  font-style: italic;
}
</style>
