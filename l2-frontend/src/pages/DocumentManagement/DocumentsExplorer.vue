<template>
  <div class="explorer">
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
    <div class="section section-types">
      <div class="scroll-equal">
        <div
          v-for="type in documentTypes"
          :key="type.id"
          class="type-row"
        >
          <button
            class="btn btn-blue-nb type-btn"
            :class="{ 'active-button': selectedType === type.id}"
            type="button"
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
    <div class="section section-documents">
      <div class="flex section-header">
        <span class="group-button-header">
          Документы
        </span>
        <label
          class="filter-check review-check"
          @click.prevent="toggleRoleFilter('toReview')"
        >
          <input
            type="checkbox"
            :checked="roleFilter === 'toReview'"
            tabindex="-1"
          >
          <span>Новые {{ pendingReviewCount }}</span>
        </label>
        <label
          class="filter-check review-check"
          @click.prevent="toggleRoleFilter('recent')"
        >
          <input
            type="checkbox"
            :checked="roleFilter === 'recent'"
            tabindex="-1"
          >
          <span>Последние</span>
        </label>
        <label
          v-if="canViewHidden"
          class="filter-check hidden-check"
          @click.prevent="toggleHidden"
        >
          <input
            type="checkbox"
            :checked="showHidden"
            tabindex="-1"
          >
          <span>Скрытые</span>
        </label>
      </div>
      <div
        v-if="actionButtons.length"
        class="section-actions"
      >
        <div class="filter-checks">
          <label
            v-for="item in actionButtons"
            :key="item.id"
            class="filter-check"
            @click.prevent="toggleRoleFilter(item.id)"
          >
            <input
              type="checkbox"
              :checked="roleFilter === item.id"
              tabindex="-1"
            >
            <span>{{ item.label }}</span>
          </label>
        </div>
      </div>
      <div
        ref="docsEl"
        class="scroll-equal"
        @scroll="onDocumentsScroll"
      >
        <div
          v-for="document in documents"
          :key="document.id"
          class="flex row-border"
        >
          <button
            class="transparent-button"
            :class="{ 'active-button': selectedDocument === document.id}"
            type="button"
            @click="selectDocument(document.id)"
          >
            {{ document.title }}
          </button>
        </div>
        <div
          v-if="isLoadingMoreRecent"
          class="filter-check"
        >
          Загрузка...
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
  listRefresh?: number;
  countRefresh?: number;
  foundDocument?: { id: number; title: string } | null;
}>();

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'select', documentId: number | null): void;
  (e: 'update:filter', value: string | null): void;
}>();

const store = useStore();
const root = getCurrentInstance().proxy.$root;
const userGroups = computed(() => store.getters.user_groups || []);
const canViewHidden = computed(() => userGroups.value.includes('Admin') || userGroups.value.includes('Скрытие документа'));
const actionButtons = computed(() => {
  const items = [];
  if (userGroups.value.includes('Согласование')) {
    items.push({ id: 'toBeAgreed', label: 'Согласовать' });
  }
  if (userGroups.value.includes('Подписание')) {
    items.push({ id: 'onSignature', label: 'Подписать' });
  }
  return items;
});

const toggleRoleFilter = (id: string) => {
  emit('update:filter', props.roleFilter === id ? null : id);
};

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
const showHidden = ref(false);
const pendingReviewCount = ref(0);
const docsEl = ref<HTMLElement | null>(null);
const recentPage = ref(1);
const recentHasMore = ref(false);
const isLoadingMoreRecent = ref(false);
const RECENT_PAGE_SIZE = 50;

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

const loadPendingCount = async () => {
  const { pendingReviewCount: count } = await api('document-manager/documents/list', { countOnly: true });
  pendingReviewCount.value = Number(count) || 0;
};

const loadRecent = async (append = false) => {
  if (append) {
    if (!recentHasMore.value || isLoadingMoreRecent.value) {
      return;
    }
    isLoadingMoreRecent.value = true;
  }
  try {
    const nextPage = append ? recentPage.value + 1 : 1;
    const data = await api('document-manager/documents/recent', {
      page: nextPage,
      pageSize: RECENT_PAGE_SIZE,
    });
    const rows = data.result || [];
    recentPage.value = data.page || nextPage;
    recentHasMore.value = Boolean(data.hasMore);
    documents.value = append ? [...documents.value, ...rows] : rows;
  } finally {
    isLoadingMoreRecent.value = false;
  }
};

const onDocumentsScroll = () => {
  if (props.roleFilter !== 'recent') {
    return;
  }
  const el = docsEl.value;
  if (!el || !recentHasMore.value || isLoadingMoreRecent.value) {
    return;
  }
  if (el.scrollHeight - el.scrollTop - el.clientHeight < 80) {
    loadRecent(true);
  }
};

const loadDocuments = async () => {
  const loadId = ++documentsLoadId;
  documents.value = [];
  recentPage.value = 1;
  recentHasMore.value = false;
  if (
    !selectedType.value
    && props.roleFilter !== 'created'
    && props.roleFilter !== 'toReview'
    && props.roleFilter !== 'recent'
  ) {
    await loadPendingCount();
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    if (props.roleFilter === 'recent') {
      await loadRecent(false);
      await loadPendingCount();
      if (loadId !== documentsLoadId) {
        return;
      }
      return;
    }
    const { result, pendingReviewCount: count } = await api('document-manager/documents/list', {
      typeId: selectedType.value,
      groupId: selectedGroup.value,
      filter: props.roleFilter,
      hidden: Boolean(canViewHidden.value && showHidden.value),
    });
    if (loadId !== documentsLoadId) {
      return;
    }
    documents.value = result || [];
    pendingReviewCount.value = Number(count) || 0;
    if (selectedDocument.value && !documents.value.some(row => row.id === selectedDocument.value)) {
      selectedDocument.value = null;
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const toggleHidden = () => {
  if (!canViewHidden.value) {
    return;
  }
  showHidden.value = !showHidden.value;
  selectedDocument.value = null;
  loadDocuments();
};

const createDocument = async (typeId: number) => {
  selectedType.value = typeId;
  showHidden.value = false;
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

watch(() => props.foundDocument, (doc) => {
  if (!doc?.id) {
    return;
  }
  if (!documents.value.some(row => row.id === doc.id)) {
    documents.value = [doc, ...documents.value];
  }
  selectedDocument.value = doc.id;
});

watch(selectedGroup, () => {
  selectedType.value = null;
  loadTypes();
});

watch(selectedType, (typeId) => {
  if (typeId) {
    loadDocuments();
  }
});

watch(() => props.roleFilter, () => {
  loadDocuments();
});

watch(() => props.listRefresh, () => {
  loadDocuments();
});

watch(() => props.countRefresh, () => {
  loadPendingCount();
});

onMounted(async () => {
  await loadGroups();
  await loadTypes();
  await loadPendingCount();
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

.section-types {
  flex: 1 1 0;
}

.section-documents {
  flex: 7 1 0;
}

.section-actions {
  flex: 0 0 auto;
}

.filter-checks {
  display: flex;
  flex-wrap: wrap;
  width: 100%;
}

.filter-check {
  flex: 1 1 33%;
  min-width: 0;
  height: 25px;
  display: flex;
  align-items: center;
  gap: 4px;
  margin: 0;
  padding: 0 6px;
  font-size: 12px;
  font-weight: normal;
  cursor: pointer;
  overflow: hidden;
  white-space: nowrap;

  input {
    flex: 0 0 auto;
    margin: 0;
    pointer-events: none;
  }

  span {
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

.flex {
  display: flex;
  min-width: 0;
}
.row-border {
  min-height: 34px;
  min-width: 0;
  border-bottom: 1px solid #b1b1b1;
}
.row-border:nth-child(1) {
  border-top: 1px solid #b1b1b1;
}

.group-button-header {
  background-color: transparent;
  flex: 0 0 auto;
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

.review-check {
  flex: 0 0 auto;
  height: 34px;
}

.hidden-check {
  flex: 0 0 auto;
  height: 34px;
  margin-left: auto;
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
  min-height: 34px;
  line-height: 16px;
  border: none;
  padding: 1px 5px 1px 10px;
  text-align: left;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  overflow-wrap: anywhere;
  white-space: normal;
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
