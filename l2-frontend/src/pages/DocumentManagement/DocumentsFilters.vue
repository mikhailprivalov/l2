<template>
  <div>
    <div class="sidebar">
      <div class="flex search-row">
        <input
          v-model="query"
          class="form-control search"
          placeholder="Номер документа"
          maxlength="15"
          spellcheck="false"
          @keypress.enter="search"
        >
        <button
          class="btn btn-blue-nb nbr"
          type="button"
          :disabled="!query"
          @click="search"
        >
          Найти
        </button>
      </div>
    </div>
    <div class="filters-panel">
      <div class="filter-checks">
        <label
          v-for="item in filterButtons"
          :key="item.id"
          class="filter-check"
          @click.prevent="toggleFilter(item.id)"
        >
          <input
            type="checkbox"
            :checked="filter === item.id"
            tabindex="-1"
          >
          <span>{{ item.label }}</span>
        </label>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

const props = defineProps<{
  filter?: string | null;
}>();

const filterButtons = [
  { id: 'created', label: 'Создал' },
  { id: 'doing', label: 'Исполняю' },
  { id: 'wrote', label: 'Поручил' },
  { id: 'onControl', label: 'Контролирую' },
];

const query = ref('');

watch(query, (value) => {
  const digits = String(value || '').replace(/[^0-9]/g, '');
  if (digits !== value) {
    query.value = digits;
  }
});

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'update:filter', value: string | null): void;
  (e: 'search', value: string): void;
}>();

const toggleFilter = (id: string) => {
  emit('update:filter', props.filter === id ? null : id);
};

const search = () => {
  if (!query.value) {
    return;
  }
  emit('search', query.value);
};
</script>

<style scoped lang="scss">
.sidebar {
  display: flex;
  flex-direction: column;
  background-color: #f8f7f7;
  border-right: 1px solid #b1b1b1;
}

.search-row {
  display: flex;
  min-width: 0;
  flex: 0 0 34px;
  height: 34px;
  min-height: 34px;
}

.search {
  height: 34px;
  border-radius: 0;
  padding-left: 10px;
}

.search-row .btn {
  height: 34px;
  border-radius: 0;
}

.filter-checks {
  display: flex;
  flex-wrap: nowrap;
  width: 100%;
  height: 34px;
}

.filter-check {
  flex: 1 1 0;
  min-width: 0;
  height: 34px;
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
  align-items: center;
  background-color: #f8f7f7;
}
</style>
