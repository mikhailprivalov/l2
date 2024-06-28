<template>
  <div class="two-col">
    <div class="sidebar">
      <div class="sidebar-row">
        <input
          class="form-control"
          placeholder="Номер документа"
        >
        <button class="btn btn-blue-nb nbr">
          Найти
        </button>
      </div>
      <div class="sidebar-row bottom-border space-between">
        <a>Мои документы</a>
        <a>что-то ещё</a>
      </div>
      <div class="sidebar-row bottom-border">
        <button class="btn btn-blue-nb nbr">
          Создать
        </button>
      </div>
      <div class="sidebar-row bottom-border">
        <Treeselect
          :options="documentGroups"
          class="treeselect-noborder"
          :clearable="false"
          placeholder="Выберите группу документов"
        />
      </div>
      <div
        v-for="group in documentGroups"
        :key="group.id"
        class="sidebar-row bottom-border"
      >
        <button
          class="transparent-button"
        >
          {{ group.label }}
        </button>
      </div>
    </div>
    <div class="viewer">
      <h4>Просмотрщик</h4>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed, getCurrentInstance, onMounted, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

// import { useStore } from '@/store';
// import * as actions from '@/store/action-types';
// import api from '@/api';

const documentGroups = ref([
  { id: 1, label: 'ОРД' },
  { id: 2, label: 'ЧТД' },
  { id: 3, label: 'МВЗ' },
]);

</script>

<style scoped lang="scss">
.two-col {
  display: grid;
  grid-template-columns: minmax(200px, 380px) minmax(150px, auto);
  height: calc(100vh - 36px);
}
.sidebar {
  display: flex;
  flex-direction: column;
  background-color: #f8f7f7;
  border-right: 1px solid #b1b1b1;

  .form-control {
    border-radius: 0;
    padding-left: 10px;
  }
}
.empty-list {
  height: 20px;
  width: 100px;
  margin: 20px auto;
}
.sidebar-row {
  display: flex;
}
.bottom-border {
  border-bottom: 1px solid #b1b1b1;
}
.space-between {
  justify-content: space-between;
}
.transparent-button {
  background-color: transparent;
  align-self: stretch;
  color: #434A54;
  flex: 1;
  border: none;
  padding: 1px 5px;
}
.transparent-button:hover {
  background-color: #434a54;
  color: #FFFFFF;
  border: none;
}
.transparent-button:active {
  background-color: #37BC9B;
  color: #FFFFFF;
}
</style>
