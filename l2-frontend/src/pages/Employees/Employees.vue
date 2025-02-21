<template>
  <div>
    <div class="filters">
      <div>
        <div class="filter-item">
          <label>Организации</label>
          <Treeselect
            v-model="filters.organizationId"
            :options="refBooks.organizations"
            :clearable="false"
            class="treeselect-34px"
            placeholder="Выберите организацию"
            :append-to-body="true"
          />
        </div>
      </div>
      <div>
        <div class="filter-item">
          <label>Подразделения</label>
          <Treeselect
            v-model="filters.departementIds"
            :options="refBooks.departments"
            :clearable="false"
            :multiple="true"
            class="treeselect-34px"
            placeholder="Выберите подразделения"
            :append-to-body="true"
          />
        </div>
      </div>
      <div>
        <div class="filter-item">
          <label>Должности</label>
          <Treeselect
            v-model="filters.positionsIds"
            :options="refBooks.positions"
            :clearable="false"
            :multiple="true"
            class="treeselect-34px"
            placeholder="Выберите должности"
            :append-to-body="true"
          />
        </div>
      </div>
      <div>
        <div class="filter-item">
          <label>Форма занятости</label>
          <Treeselect
            v-model="filters.employmentFormsIds"
            :options="refBooks.employmentForms"
            :clearable="false"
            :multiple="true"
            class="treeselect-34px"
            placeholder="Выберите форму занятости"
            :append-to-body="true"
          />
        </div>
      </div>
    </div>
    <div class="search-block" />
    <div class="employee-block" />
  </div>
</template>

<script setup lang="ts">
import { getCurrentInstance, onMounted, ref } from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';

const root = getCurrentInstance().proxy.$root;
const store = useStore();

const filters = ref({
  organizationId: null,
  departementIds: null,
  positionsIds: null,
  employmentFormsIds: null,
});

const refBooks = ref({
  organizations: [],
  departments: [],
  positions: [],
  employmentForms: [],
});

const getRefBooks = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('employees/get-ref-books');
  await store.dispatch(actions.DEC_LOADING);
  refBooks.value = result;
};

onMounted(() => {
  getRefBooks();
});

</script>

<style scoped lang="scss">
.filters {
  display: grid;
  background-color: #fff;
  border-radius: 4px;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  padding: 10px 0;
  box-shadow: 0 1px 3px rgb(0 0 0 / 12%), 0 1px 2px rgb(0 0 0 / 24%);
  max-height: 185px;
  overflow-y: auto;
}
.filter-item {
  margin: 0 5px;
}
</style>
