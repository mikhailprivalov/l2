<template>
  <div class="explorer">
    <div class="flex search-row">
      <input
        class="form-control search"
        placeholder="Номер документа"
      >
      <button class="btn btn-blue-nb nbr">
        Найти
      </button>
    </div>
    <div class="section section-groups">
      <div class="flex group-select-row">
        <Treeselect
          v-model="selectedGroup"
          class="treeselect-wide treeselect-34px group-select"
          :multiple="false"
          :options="groupOptions"
          placeholder="Выберите группу"
          :append-to-body="true"
          :clearable="false"
          no-options-text="Нет групп"
        />
      </div>
    </div>
    <div class="section section-equal">
      <div class="scroll-equal">
        <div
          v-for="type in documentTypes"
          :key="type.id"
          class="type-row"
        >
          <button
            v-tippy="{ placement: 'right' }"
            class="btn btn-blue-nb type-btn"
            :class="{ 'active-button': selectedType === type.id}"
            type="button"
            :title="type.title"
            @click="selectType(type.id)"
          >
            {{ type.title }}
          </button>
          <button
            class="btn btn-blue-nb type-btn type-btn-plus"
            type="button"
            title="Создать"
            @click="createDocument(type.id)"
          >
            <i class="fa fa-plus" />
          </button>
        </div>
      </div>
    </div>
    <div class="section section-equal">
      <div class="flex section-header">
        <span class="group-button-header">
          Документы
        </span>
      </div>
      <div class="scroll-equal">
        <div
          v-for="document in documents"
          :key="document.id"
          class="flex row-border"
        >
          <button
            v-tippy="{ placement: 'right' }"
            class="transparent-button"
            :class="{ 'active-button': selectedDocument === document.id}"
            type="button"
            :title="document.title"
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
  computed, getCurrentInstance, onMounted, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

const GROUP_ALL = 0;
const GROUP_NONE = -1;

interface CatalogItem {
  id: number;
  title: string;
}

const props = defineProps<{
  roleFilter?: string | null;
}>();

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'select', documentId: number | null): void;
}>();

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const selectedGroup = ref<number>(GROUP_ALL);
const documentGroups = ref<CatalogItem[]>([]);
const groupOptions = computed(() => [
  { id: GROUP_ALL, label: 'Все' },
  { id: GROUP_NONE, label: 'Без группы' },
  ...documentGroups.value.map(group => ({
    id: group.id,
    label: group.title,
  })),
]);

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

let documentsLoadId = 0;

const loadDocuments = async () => {
  const loadId = ++documentsLoadId;
  documents.value = [];
  if (!selectedType.value && props.roleFilter !== 'created') {
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    const { result } = await api('document-manager/documents/list', {
      typeId: selectedType.value,
      groupId: selectedGroup.value,
      filter: props.roleFilter,
    });
    if (loadId !== documentsLoadId) {
      return;
    }
    documents.value = result || [];
    if (selectedDocument.value && !documents.value.some(row => row.id === selectedDocument.value)) {
      selectedDocument.value = null;
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const createDocument = async (typeId: number) => {
  selectedType.value = typeId;
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/documents/create', { typeId });
    if (result?.ok) {
      root.$emit('msg', 'ok', 'Документ создан');
      await loadDocuments();
      selectedDocument.value = result.id;
    } else {
      root.$emit('msg', 'error', result?.message || 'Ошибка создания');
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const selectType = (typeId: number) => {
  selectedType.value = typeId;
  selectedDocument.value = null;
};

const selectDocument = (documentId: number) => {
  selectedDocument.value = documentId;
};

watch(selectedDocument, (id) => {
  emit('select', id);
});

watch(selectedGroup, () => {
  selectedType.value = null;
  selectedDocument.value = null;
  documents.value = [];
  loadTypes();
});

watch(selectedType, () => {
  loadDocuments();
});

watch(() => props.roleFilter, () => {
  loadDocuments();
});

onMounted(async () => {
  await loadGroups();
  await loadTypes();
});
</script>

<style scoped lang="scss">
.explorer {
  display: flex;
  flex-direction: column;
  flex: 1;
  height: 100%;
  min-height: 0;
}

.search-row {
  flex: 0 0 34px;
  height: 34px;
  min-height: 34px;
}

.section {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.section-groups {
  flex: 0 0 auto;
}

.group-select-row,
.section-header {
  flex: 0 0 34px;
  height: 34px;
  min-height: 34px;
}

.group-select {
  flex: 1 1 0;
  min-width: 0;
}

:deep(.group-select .vue-treeselect__control) {
  height: 34px;
  border: none;
  border-radius: 0;
}

:deep(.group-select .vue-treeselect__single-value),
:deep(.group-select .vue-treeselect__placeholder) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.section-equal {
  flex: 1 1 0;
}

.flex {
  display: flex;
  min-width: 0;
}
.row-border {
  height: 34px;
  min-height: 34px;
  min-width: 0;
  border-bottom: 1px solid #b1b1b1;
}
.row-border:nth-child(1) {
  border-top: 1px solid #b1b1b1;
}

.search {
  height: 34px;
  border-radius: 0;
  padding-left: 10px;
}

.search-row .btn {
  height: 34px;
  border-radius: 0;
}

.group-button-header {
  background-color: transparent;
  flex: 1;
  min-width: 0;
  height: 34px;
  line-height: 34px;
  border: none;
  padding: 0 5px 0 10px;
  text-align: left;
  cursor: default;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.type-row {
  display: flex;
  flex-direction: row;
  min-width: 0;
}

.type-btn {
  border-radius: 0;
  text-align: left;
  border-top: none !important;
  border-right: none !important;
  border-left: none !important;
  padding: 0 12px;
  height: 24px;
  line-height: 24px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;

  &:not(:hover):not(.active-button) {
    background-color: rgba(#000, 0.02) !important;
    color: #000 !important;
    border-bottom: 1px solid #b1b1b1 !important;
  }

  &.active-button:not(:hover) {
    background-color: #049372 !important;
    color: #fff;
    border-bottom: 1px solid #b1b1b1 !important;
  }
}

.type-row .type-btn:first-child {
  flex: 1 1 auto;
  min-width: 0;
}

.type-btn-plus {
  flex: 0 0 auto;
  padding: 0 12px;
}

.transparent-button {
  background-color: transparent;
  align-self: stretch;
  color: #434A54;
  flex: 1;
  min-width: 0;
  height: 34px;
  line-height: 22px;
  border: none;
  padding: 0 5px 0 10px;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
.scroll-equal {
  flex: 1 1 0;
  min-height: 0;
  overflow-y: auto;
}
</style>
