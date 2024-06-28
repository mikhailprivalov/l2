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
        <RadioFieldById :variants="buttons" />
      </div>
      <h5>Группы</h5>
      <div>
        <div
          v-for="group in documentGroups"
          :key="group.id"
          class="sidebar-row row-border"
        >
          <button
            class="transparent-button"
            :class="{ 'active-button': selectedGroup === group.id}"
            @click="selectGroup(group.id)"
          >
            {{ group.label }}
          </button>
        </div>
      </div>
      <h5>Виды</h5>
      <div>
        <div
          v-for="type in documentTypes"
          :key="type.id"
          class="sidebar-row row-border"
        >
          <button
            class="transparent-button"
            :class="{ 'active-button': selectedType === type.id}"
            @click="selectType(type.id)"
          >
            {{ type.label }}
          </button>
        </div>
      </div>
      <h5>Документы</h5>
      <div class="scroll">
        <div
          v-for="document in documents"
          :key="document.id"
          class="sidebar-row row-border"
        >
          <button
            class="transparent-button"
            :class="{ 'active-button': selectedDocument === document.id}"
            @click="selectDocument(document.id)"
          >
            {{ document.label }}
          </button>
        </div>
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
import RadioFieldById from '@/fields/RadioFieldById.vue';

// import { useStore } from '@/store';
// import * as actions from '@/store/action-types';
// import api from '@/api';
const buttons = ref([
  { id: 1, label: 'Мои' },
  { id: 2, label: 'Создать' },
]);

const selectedGroup = ref(null);
const documentGroups = ref([
  { id: 1, label: 'Группа доков 1' },
  { id: 2, label: 'Группа доков 1' },
  { id: 3, label: 'Группа доков 1' },
]);

const selectGroup = (groupId: number) => {
  selectedGroup.value = groupId;
};

const selectedType = ref(null);
const documentTypes = ref([
  { id: 1, label: 'Тип дока 1' },
  { id: 2, label: 'Тип дока 2' },
  { id: 3, label: 'Тип дока 3' },
]);

const selectType = (typeId: number) => {
  selectedType.value = typeId;
};

const selectedDocument = ref(null);
const documents = ref([
  { id: 1, label: 'Документ 1' },
  { id: 2, label: 'Документ 2' },
  { id: 3, label: 'Документ 3' },
  { id: 4, label: 'Документ 4' },
  { id: 5, label: 'Документ 5' },
  { id: 6, label: 'Документ 6' },
  { id: 7, label: 'Документ 7' },
  { id: 8, label: 'Документ 8' },
  { id: 9, label: 'Документ 9' },
  { id: 10, label: 'Документ 10' },
  { id: 11, label: 'Документ 11' },
]);

const selectDocument = (documentId: number) => {
  selectedDocument.value = documentId;
};

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
.row-border {
  border-bottom: 1px solid #b1b1b1;
}
.row-border:nth-child(1) {
  border-top: 1px solid #b1b1b1;
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
.active-button {
  background-color: #049372;
  color: #FFFFFF;
}
.scroll {
  max-height: 231px;
  overflow-y: auto;
}
</style>
