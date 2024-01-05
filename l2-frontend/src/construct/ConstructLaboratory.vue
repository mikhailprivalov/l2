<template>
  <div class="two-col">
    <div class="sidebar">
      <div class="picker">
        <Treeselect
          v-model="department"
          :options="departments"
          class="treeselect-nbr"
          placeholder="Выберите подразделение"
        />
      </div>
      <input
        v-model.trim="search"
        class="form-control"
        style="padding-top: 7px; padding-bottom: 7px"
        placeholder="Фильтр по названию"
      >
       <div
        class="sidebar-content"
      >
        <div>
          Не найдено
        </div>
        <div
          v-for="row in researches_list_filtered"
          :key="row.pk"
          class="research"
          :class="{ rhide: row.hide }"
          @click="open_editor(row.pk)"
        >
          {{ row.title }}
        </div>
      </div>
      <button
        class="btn btn-blue-nb sidebar-footer"
        @click="open_editor(-1)"
      >
        <i class="glyphicon glyphicon-plus" />
        Добавить
      </button>
    </div>
    <div class="content-construct" />
  </div>
</template>

<script setup lang="ts">
import {computed, ref} from 'vue';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

const department = ref(-1);
const departments = ref([]);

const search = ref('');

const researches = ref([])
const filteredResearched = computed()
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
    border-top: none;
    border-left: none;
    border-right: none;
  }
}
.picker ::v-deep .btn {
  border-radius: 0;
  border-top: none;
  border-left: none;
  border-right: none;
  border-top: 1px solid #fff;
}

.content-construct {
  display: flex;
}
</style>
