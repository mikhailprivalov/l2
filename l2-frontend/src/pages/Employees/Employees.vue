<template>
  <div>
    <div class="filters">
      <div>
        <div class="filter-item">
          <label>Подразделения</label>
          <Treeselect
            v-model="filters.departements"
            :options="refBooks.departments"
            :clearable="false"
            class="treeselect-34px"
            placeholder="Выберите подразделение"
            :append-to-body="true"
          />
        </div>
      </div>
      <div>
        <div class="filter-item">
          <label>Должности</label>
          <Treeselect
            v-model="filters.positions"
            :options="refBooks.positions"
            :clearable="false"
            class="treeselect-34px"
            placeholder="Выберите подразделение"
            :append-to-body="true"
          />
        </div>
      </div>
      <div>
        <div class="filter-item">
          <label>Форма занятости</label>
          <Treeselect
            v-model="filters.employmentForms"
            :options="refBooks.employmentForms"
            :clearable="false"
            class="treeselect-34px"
            placeholder="Выберите подразделение"
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
import { ref } from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

const filters = ref({
  departements: null,
  positions: null,
  employmentForms: null,
});

const refBooks = ref({
  departments: [],
  positions: [],
  employmentForms: [],
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
