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
        placeholder="Фильтр по названию"
      >
      <div
        class="sidebar-content"
      >
        <TubeGroup
          v-for="(tube, idx) in filteredResearchTubes"
          :key="idx"
          :tube="tube"
          @updateOrder="updateOrder"
          @changeVisibility="changeVisibility"
          @edit="edit"
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
    <div class="content-construct">
      <ResearchDetail
        v-if="currentResearchPk"
        :research-pk="currentResearchPk"
        @updateResearch="getTubes"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed, getCurrentInstance, onMounted, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import TubeGroup from '@/construct/TubeGroup.vue';
import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';
import ResearchDetail from '@/construct/ResearchDetail.vue';

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const department = ref(null);
const departments = ref([
  { id: 1, label: 'отделение1' },
]);

const getDepartments = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('construct/laboratory/get-departments');
  await store.dispatch(actions.DEC_LOADING);
  result.push({
    id: -1, label: 'Все',
  });
  departments.value = result;
};

const search = ref('');

const researchTubes = ref([]);

const getTubes = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('construct/laboratory/get-tubes', { department_id: department.value });
  await store.dispatch(actions.DEC_LOADING);
  researchTubes.value = result;
};

const currentResearchPk = ref(null);

const edit = async ({ researchPk }) => {
  currentResearchPk.value = researchPk;
};

watch([department], () => {
  getTubes();
  currentResearchPk.value = null;
});

const filteredResearchTubes = computed(() => researchTubes.value.map(tubes => {
  const searchTerm = search.value.toLowerCase();
  const result = tubes.researches.filter(research => {
    const researchTitle = research.title.toLowerCase();
    return researchTitle.includes(searchTerm);
  });
  if (result) {
    return { researches: result, tubes: tubes.tubes };
  }
  return [];
}).filter(tubes => tubes.researches.length !== 0));

const updateOrder = async ({ researchPk, researchNearbyPk, action }) => {
  await store.dispatch(actions.INC_LOADING);
  const { ok } = await api('construct/laboratory/update-order-research', {
    researchPk, researchNearbyPk, action,
  });
  await store.dispatch(actions.DEC_LOADING);
  if (ok) {
    root.$emit('msg', 'ok', 'Обновлено');
    await getTubes();
  } else {
    root.$emit('msg', 'error', 'Ошибка');
  }
};

const changeVisibility = async ({ researchPk }) => {
  await store.dispatch(actions.INC_LOADING);
  const { ok } = await api('construct/laboratory/change-visibility-research', {
    researchPk,
  });
  await store.dispatch(actions.DEC_LOADING);
  if (ok) {
    root.$emit('msg', 'ok', 'Обновлено');
    await getTubes();
  } else {
    root.$emit('msg', 'error', 'Ошибка');
  }
};

onMounted(() => {
  getDepartments();
});

</script>

<style scoped lang="scss">
.two-col {
  display: grid;
  grid-template-columns: 450px auto;
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
    height: 36px;
  }
}
.empty-list {
  height: 20px;
  width: 100px;
  margin: 20px auto;
}

.sidebar-content {
  height: calc(100vh - 142px);
  overflow-y: auto;
}

.sidebar-footer {
  border-radius: 0;
  margin: 0;
  flex: 0 0 34px;
}
</style>