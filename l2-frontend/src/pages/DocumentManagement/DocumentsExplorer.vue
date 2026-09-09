<template>
  <div>
    <div class="flex">
      <input
        class="form-control search"
        placeholder="Номер документа"
      >
      <button class="btn btn-blue-nb nbr">
        Найти
      </button>
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
            {{ group.title }}
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
            {{ type.title }}
          </button>
        </div>
      </div>
    </div>
    <div>
      <div class="flex">
        <span class="group-button-header">
          Документы
        </span>
      </div>
      <div class="scroll-doc">
        <div
          v-for="document in documents"
          :key="document.id"
          class="flex row-border"
        >
          <button
            class="transparent-button"
            :class="{ 'active-button': selectedDocument === document.id}"
            @click="selectDocument(document.id)"
          >
            {{ document.title }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  onMounted, ref, watch,
} from 'vue';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';

interface CatalogItem {
  id: number;
  title: string;
}

const store = useStore();

const selectedGroup = ref<number | null>(null);
const documentGroups = ref<CatalogItem[]>([]);

const selectedType = ref<number | null>(null);
const documentTypes = ref<CatalogItem[]>([]);

const selectedDocument = ref<number | null>(null);
const documents = ref<CatalogItem[]>([]);

const loadGroups = async () => {
  await store.dispatch(actions.INC_LOADING);
  try {
    const { result } = await api('document-manager/groups/list');
    documentGroups.value = result || [];
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const loadTypes = async () => {
  await store.dispatch(actions.INC_LOADING);
  try {
    const { result } = await api('document-manager/types/list', { groupId: selectedGroup.value });
    documentTypes.value = result || [];
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const selectGroup = (groupId: number) => {
  selectedGroup.value = groupId;
  selectedType.value = null;
  selectedDocument.value = null;
};

const selectType = (typeId: number) => {
  selectedType.value = typeId;
  selectedDocument.value = null;
};

const selectDocument = (documentId: number) => {
  selectedDocument.value = documentId;
};

watch(selectedGroup, () => {
  loadTypes();
});

onMounted(async () => {
  await loadGroups();
  await loadTypes();
});
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

.search {
  border-radius: 0;
  padding-left: 10px;
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
  height: calc(100vh - 465px);
  overflow-y: auto;
}
</style>
