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
      <a
        class="a-under a-align"
        href="#"
        @click.prevent="downloadXlsx()"
      >
        XLSX
      </a>
      <div
        class="sidebar-content"
      >
        <ResearchesGroup
          v-for="(tube, idx) in filteredResearchTubes"
          :key="idx"
          :tube="tube"
          @updateOrder="updateOrder"
          @changeVisibility="changeVisibility"
          @edit="edit"
          @add="add"
          @editRelationTube="editRelation"
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
        @click="addResearch"
      >
        <i class="glyphicon glyphicon-plus" />
        Добавить
      </button>
    </div>
    <div class="content-construct">
      <ResearchDetail
        v-if="currentResearch.pk"
        :research="currentResearch"
        :ref-books="refBooks"
        :departments="departments.slice(1)"
        @updateResearch="getTubes"
      />
    </div>
    <RelationTubeEdit
      v-if="editRelationId"
      :edit-relation-id="editRelationId"
      @hideModal="hideModal"
    />
  </div>
</template>

<script setup lang="ts">
import {
  computed, getCurrentInstance, onMounted, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';
import ResearchDetail from '@/construct/ResearchDetail.vue';
import ResearchesGroup from '@/construct/ResearchesGroup.vue';
import RelationTubeEdit from '@/modals/RelationTubeEdit.vue';

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const department = ref(null);
const departments = ref([]);

const getDepartments = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('construct/laboratory/get-departments');
  await store.dispatch(actions.DEC_LOADING);
  result.unshift({ id: -1, label: 'Все' });
  departments.value = result;
};

const search = ref('');

const researchTubes = ref([]);

const currentResearch = ref({
  pk: null, order: 1, departmentId: department.value, tubes: null,
});
const getTubes = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('construct/laboratory/get-tubes', { department_id: department.value });
  await store.dispatch(actions.DEC_LOADING);
  researchTubes.value = result;
};

const edit = ({ researchPk }) => {
  currentResearch.value.pk = researchPk;
};

const add = (newResearchData: object) => {
  currentResearch.value = {
    pk: -1, order: newResearchData.order, departmentId: department.value, tubes: newResearchData.tubes,
  };
};

const filteredResearchTubes = computed(() => researchTubes.value.map(tubes => {
  const searchTerm = search.value.toLowerCase();
  const result = tubes.researches.filter(research => {
    const researchTitle = research.title.toLowerCase();
    const researchInternalCode = research.internalCode.toLowerCase();
    return researchTitle.includes(searchTerm) || researchInternalCode.includes(searchTerm);
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

const downloadXlsx = () => {
  window.open(`/forms/xlsx?type=102.01&departmentId=${department.value}`, '_blank');
};

const addResearch = () => {
  currentResearch.value = {
    pk: -1, order: 1, departmentId: department.value, tubes: [],
  };
};

export interface refBook {
  units: object[],
  materials: object[],
  subGroups: object[],
  variants: object[],
  tubes: object[],
  relations: object[],
}
const refBooks = ref<refBook>({
  units: [],
  materials: [],
  subGroups: [],
  variants: [],
  tubes: [],
  relations: [],
});

const getRefbooks = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('construct/laboratory/get-ref-books', { departmentId: department.value });
  await store.dispatch(actions.DEC_LOADING);
  refBooks.value = result;
};

watch([department], () => {
  getTubes();
  currentResearch.value = {
    pk: null, order: null, departmentId: department.value, tubes: null,
  };
  getRefbooks();
});

const editRelationId = ref(null);
const editRelation = ({ relationId }) => {
  editRelationId.value = relationId;
};

const hideModal = () => {
  getTubes();
  editRelationId.value = null;
};

onMounted(() => {
  getDepartments();
  getRefbooks();
});

</script>

<style scoped lang="scss">
.two-col {
  display: grid;
  grid-template-columns: minmax(200px, 380px) minmax(150px, auto);
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
  .a-align {
    margin-left: auto;
  }
}
.empty-list {
  height: 20px;
  width: 100px;
  margin: 20px auto;
}

.sidebar-content {
  height: calc(100vh - 162px);
  overflow-y: auto;
}

.sidebar-footer {
  border-radius: 0;
  margin: 0;
  flex: 0 0 34px;
}

</style>
