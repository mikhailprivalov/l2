<template>
  <div>
    <div class="flex">
      <input
        class="form-control"
        placeholder="Номер документа"
      >
      <button class="btn btn-blue-nb nbr">
        Найти
      </button>
    </div>
    <div class="flex row-border">
      <RadioFieldById
        :variants="filterButtons"
        item-width="33%"
        item-height="25px"
        :auto-height="true"
      />
    </div>
    <div>
      <div class="flex">
        <span
          class="group-button-header"
        >
          Группы
        </span>
      </div>
      <div class="scroll">
        <div
          v-for="group in documentGroups"
          :key="group.id"
          class="flex row-border"
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
    </div>
    <div>
      <div class="flex">
        <span
          class="group-button-header"
        >
          Виды
        </span>
      </div>
      <div class="scroll">
        <div
          v-for="type in documentTypes"
          :key="type.id"
          class="flex row-border"
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
    </div>
    <div>
      <div class="row">
        <span class="group-button-header">
          Документы
        </span>
      </div>
      <div class="scroll-doc">
        <div
          v-for="document in documents"
          :key="document.id"
          class="row row-border"
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
  </div>
</template>

<script setup lang="ts">
import {
  ref,
} from 'vue';

import RadioFieldById from '@/fields/RadioFieldById.vue';

// import { useStore } from '@/store';
// import * as actions from '@/store/action-types';
// import api from '@/api';
const filterButtons = ref([
  { id: 'my', label: 'Мои' },
  { id: 'wrote', label: 'Отписал' },
  { id: 'onControl', label: 'На контроле' },
  { id: 'toBeAgreed', label: 'На согласовании' },
  { id: 'onSignature', label: 'На подписи' },
]);

const selectedGroup = ref(null);
const documentGroups = ref([
  { id: 1, label: 'Группа доков 1' },
  { id: 2, label: 'Группа доков 2' },
  { id: 3, label: 'Группа доков 3' },
  { id: 4, label: 'Группа доков 4' },
  { id: 5, label: 'Группа доков 5' },
  { id: 6, label: 'Группа доков 6' },
  { id: 7, label: 'Группа доков 7' },
]);

const selectGroup = (groupId: number) => {
  selectedGroup.value = groupId;
};

const selectedType = ref(null);
const documentTypes = ref([
  { id: 1, label: 'Тип дока 1' },
  { id: 2, label: 'Тип дока 2' },
  { id: 3, label: 'Тип дока 3' },
  { id: 4, label: 'Тип дока 4' },
  { id: 5, label: 'Тип дока 5' },
  { id: 6, label: 'Тип дока 6' },
  { id: 7, label: 'Тип дока 7' },
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

.flex {
  display: flex;
}
.row-border {
  border-bottom: 1px solid #b1b1b1;
}
.row-border:nth-child(1) {
  border-top: 1px solid #b1b1b1;
}

.group-button-header {
  background-color: #ededed;
  flex: 1;
  align-self: flex-start;
  border: none;
  padding: 1px 5px 1px 10px;
  text-align: left;
  cursor: default;
}

.transparent-button {
  background-color: transparent;
  align-self: stretch;
  color: #434A54;
  flex: 1;
  border: none;
  padding: 1px 5px 1px 10px;
  text-align: left;
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
  height: 139px;
  overflow-y: auto;
}
.scroll-doc {
  height: calc(100vh - 424px);
  overflow-y: auto;
}
</style>
