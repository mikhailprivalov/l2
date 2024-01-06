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
        <Tube
          v-for="tube in filteredResearchTubes"
          :key="tube.id"
          :tube="tube"
        />
        <div
          v-if="filteredResearchTubes.length === 0"
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
import { computed, onMounted, ref } from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import Tube from '@/construct/tube.vue';
import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';

const store = useStore();

const department = ref(null);
const departments = ref([
  { id: 1, label: 'отделение1' },
]);

const getDepartments = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('laboratory/get-departments');
  await store.dispatch(actions.DEC_LOADING);
  departments.value = result;
};

const search = ref('');

const researchTubes = ref([
  {
    id: 1,
    label: 'Гле',
    color: '#809030',
    research: [
      { id: 1, label: 'Исследование 1' },
      { id: 2, label: 'Исследование 2' },
      { id: 3, label: 'Исследование 3' },
    ],
  },
  {
    id: 2,
    label: '4234fsd',
    color: '#800800',
    research: [
      { id: 1, label: 'Исследование 11' },
      { id: 2, label: 'Исследование 12' },
      { id: 3, label: 'Исследование 13' },
    ],
  },
  {
    id: 3,
    label: 'Глsdfsdfе',
    color: '#803000',
    research: [
      { id: 1, label: 'Исследование 111' },
      { id: 2, label: 'Исследование 112' },
      { id: 3, label: 'Исследование 113' },
    ],
  },
]);

const getTubes = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('laboratory/get-tubes', { podrazdelenie_id: department });
  await store.dispatch(actions.DEC_LOADING);
  researchTubes.value = result;
};
const filteredResearchTubes = computed(() => researchTubes.value.filter(research => {
  const researchTitle = research.label?.toLowerCase();
  const searchTerm = search.value.toLowerCase();
  return researchTitle.includes(searchTerm);
}));

onMounted(() => {
  getDepartments();
});

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

.sidebar-footer {
  border-radius: 0;
  margin: 0;
  flex: 0 0 34px;
}

.content-construct {
  display: flex;
}
</style>
