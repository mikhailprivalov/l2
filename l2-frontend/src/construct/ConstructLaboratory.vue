<template>
  <div class="two-col">
    <div class="sidebar">
      <Treeselect
        v-model="department"
        :options="departments"
        class="treeselect-noborder"
        :clearable="false"
        placeholder="Выберите подразделение"
      />
      <input
        v-model.trim="search"
        class="form-control"
        style="padding-top: 7px; padding-bottom: 7px"
        placeholder="Фильтр по названию"
      >
      <div
        class="sidebar-content"
      >
        <div
          v-for="research in filteredResearches"
          :key="research.id"
          class="research"
        >
          {{ research.label }}
        </div>
        <div
          v-if="filteredResearches.length === 0"
          class="empty-list"
        >
          Не найдено
        </div>
      </div>
      <button
        class="btn btn-blue-nb nbr"
      >
        <i class="glyphicon glyphicon-plus" />
        Добавить
      </button>
    </div>
    <div class="content-construct" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

const department = ref(null);
const departments = ref([
  { id: 1, label: 'отделение1' },
]);

const search = ref('');

const researches = ref([
  { id: 1, label: 'Гле' },
  { id: 2, label: 'Анастаси' },
  { id: 3, label: 'Прив' },
]);
const filteredResearches = computed(() => researches.value.filter(research => {
  const researchTitle = research.label?.toLowerCase();
  const searchTerm = search.value.toLowerCase();
  return researchTitle.includes(searchTerm);
}));
</script>

<style scoped lang="scss">
.two-col {
  display: grid;
  grid-template-columns: 350px auto;
  margin-bottom: 5px;
  height: calc(100vh - 36px);
}
.sidebar {
  display: flex;
  flex-direction: column;
  background-color: #f8f7f7;
  border-right: 1px solid #b1b1b1;

  .form-control {
    border-radius: 0;
    border-left: none;
    border-right: none;
  }
}
.empty-list {
  height: 20px;
  width: 100px;
  margin: 20px auto;
}

.sidebar-content {
  height: 100%;
}

.research {
  background-color: #fff;
  padding: 5px;
  margin: 10px;
  border-radius: 4px;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
  position: relative;

  &.rhide {
    background-image: linear-gradient(#6c7a89, #56616c);
    color: #fff;
  }

  &:hover {
    box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
    z-index: 1;
    transform: scale(1.008);
  }
}

.research:not(:first-child) {
  margin-top: 0;
}

.research:last-child {
  margin-bottom: 0;
}
.sidebar-footer {
  border-radius: 0;
  margin: 0;
  flex: 0 0 34px;
}

.content-construct {
  display: flex;
}
</style>
