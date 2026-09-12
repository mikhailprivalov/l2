<template>
  <div>
    <div class="sidebar">
      <div class="filter-checks">
        <label
          v-for="item in filterButtons"
          :key="item.id"
          class="filter-check"
          @click.prevent="toggleFilter(item.id)"
        >
          <input
            type="checkbox"
            :checked="selectedFilter === item.id"
            tabindex="-1"
          >
          <span>{{ item.label }}</span>
        </label>
      </div>
    </div>
    <div class="filters-panel">
      <input
        class="form-control filters-input"
        placeholder="Исполнитель"
      >
      <input
        class="form-control filters-input"
        placeholder="Контроль до"
      >
      <input
        class="form-control filters-input"
        placeholder="Фильтр 3"
      >
      <input
        class="form-control filters-input"
        placeholder="фильтр 4"
      >
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const filterButtons = [
  { id: 'created', label: 'Создал' },
  { id: 'doing', label: 'Исполняю' },
  { id: 'wrote', label: 'Поручил' },
  { id: 'onControl', label: 'Контролирую' },
  { id: 'toBeAgreed', label: 'Согласовать' },
  { id: 'onSignature', label: 'Подписать' },
];

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'update:filter', value: string | null): void;
}>();

const selectedFilter = ref<string | null>(null);

const toggleFilter = (id: string) => {
  selectedFilter.value = selectedFilter.value === id ? null : id;
  emit('update:filter', selectedFilter.value);
};
</script>

<style scoped lang="scss">
.sidebar {
  display: flex;
  flex-direction: column;
  background-color: #f8f7f7;
  border-right: 1px solid #b1b1b1;
}

.filter-checks {
  display: flex;
  flex-wrap: wrap;
  width: 100%;
}

.filter-check {
  flex: 1 1 33%;
  min-width: 0;
  height: 25px;
  display: flex;
  align-items: center;
  gap: 4px;
  margin: 0;
  padding: 0 6px;
  font-size: 12px;
  font-weight: normal;
  cursor: pointer;
  overflow: hidden;
  white-space: nowrap;

  input {
    flex: 0 0 auto;
    margin: 0;
    pointer-events: none;
  }

  span {
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

.filters-panel {
  display: flex;
  flex-direction: row;
  background-color: #f8f7f7;
}

.filters-input {
  height: 25px;
  border-radius: 0;
}
</style>
