<template>
  <div class="root">
  <div class="body">
    <TwoSidedLayout
      :left-width-px="leftWidthPx"
      :min-left-width-px="MIN_LEFT_WIDTH_PX"
      :min-right-width-px="360"
      resizable
      @update:left-width-px="onLeftWidthChange"
    >
      <template #left>
        <aside class="side">
      <div class="side-filters">
        <div class="side-filter-row">
          <label
            v-for="item in roleButtons"
            :key="item.id"
            class="filter-check side-check"
            @click.prevent="toggleRole(item.id)"
          >
            <input
              type="checkbox"
              :checked="roleFilter === item.id"
              tabindex="-1"
            >
            <span>{{ item.label }}</span>
          </label>
        </div>
        <div class="side-filter-row">
          <label
            class="filter-check side-check"
            @click.prevent="toggleRole('toReview')"
          >
            <input
              type="checkbox"
              :checked="roleFilter === 'toReview'"
              tabindex="-1"
            >
            <span>Новые {{ pendingReviewCount }}</span>
          </label>
          <label
            class="filter-check side-check"
            @click.prevent="toggleRole('recent')"
          >
            <input
              type="checkbox"
              :checked="roleFilter === 'recent'"
              tabindex="-1"
            >
            <span>Последние</span>
          </label>
          <label
            class="filter-check side-check"
            @click.prevent="toggleRole('toBeAgreed')"
          >
            <input
              type="checkbox"
              :checked="roleFilter === 'toBeAgreed'"
              tabindex="-1"
            >
            <span>Согласовать</span>
          </label>
          <label
            class="filter-check side-check"
            @click.prevent="toggleRole('onSignature')"
          >
            <input
              type="checkbox"
              :checked="roleFilter === 'onSignature'"
              tabindex="-1"
            >
            <span>Подписать</span>
          </label>
        </div>
        <label
          v-if="canViewHidden"
          class="filter-check side-check side-check-hidden"
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
        ref="docsEl"
        class="doc-list"
        @scroll="onDocumentsScroll"
      >
        <div
          v-for="document in documents"
          :key="document.id"
          class="doc-row"
        >
          <button
            class="doc-btn"
            :class="{ 'active-button': selectedDocument === document.id }"
            type="button"
            @click="selectedDocument = document.id"
          >
            <span class="doc-title">{{ document.title }}</span>
            <i
              v-if="roleFilter === 'created' && !document.confirmed"
              class="fa-solid fa-pen doc-draft"
            />
          </button>
        </div>
        <div
          v-if="isLoadingMoreRecent"
          class="filter-check"
        >
          Загрузка...
        </div>
      </div>
    </aside>
      </template>
      <template #right>
        <div class="main">
      <div class="top-panel">
        <div class="search-dates">
          <DateRange
            v-model="dateRange"
            small
          />
        </div>
        <input
          v-model="query"
          class="form-control search"
          :placeholder="byText ? 'Номер или текст' : 'Номер документа'"
          :maxlength="byNumber && !byText ? 15 : 128"
          spellcheck="false"
          @keypress.enter="searchDocuments"
        >
        <label
          class="mode-check"
          @click.prevent="toggleMode('number')"
        >
          <input
            type="checkbox"
            :checked="byNumber"
            tabindex="-1"
          >
          <span>по номеру</span>
        </label>
        <label
          class="mode-check"
          @click.prevent="toggleMode('text')"
        >
          <input
            type="checkbox"
            :checked="byText"
            tabindex="-1"
          >
          <span>по тексту</span>
        </label>
        <button
          class="btn btn-blue-nb nbr"
          type="button"
          :disabled="!query.trim()"
          @click="searchDocuments"
        >
          Найти
        </button>
      </div>
      <div class="viewer">
        <DocumentViewer
          :document-id="selectedDocument"
          @visibility-change="onVisibilityChange"
          @reviewed="onReviewed"
        />
      </div>
    </div>
      </template>
    </TwoSidedLayout>
  </div>
  <div
    v-if="ready"
    class="picker"
  >
      <ResearchesPicker
        v-model="selectedResearches"
        :hidetemplates="true"
        :types-only="DOU_TYPE"
        :override-departments="overrideDepartments"
        :override-researches="overrideResearches"
        skip-directory-load
        :default-research-columns="10"
        :max-content-rows="2"
        just_search
        kk="dou2"
      >
        <template #search-prefix>
          <button
            class="btn btn-blue-nb create-btn"
            type="button"
            :disabled="!canCreate"
            @click="createDocument"
          >
            Создать
          </button>
        </template>
      </ResearchesPicker>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed, getCurrentInstance, onMounted, ref, watch,
} from 'vue';
import moment from 'moment';

import researchesPoint from '@/api/researches-point';
import api from '@/api';
import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import DateRange from '@/ui-cards/DateRange.vue';
import DocumentViewer from '@/pages/DocumentManagement/DocumentViewer.vue';
import TwoSidedLayout from '@/layouts/TwoSidedLayout.vue';
import ResearchesPicker from '@/ui-cards/ResearchesPicker.vue';

const DOU_TYPE = [10010];
const DOU_RESEARCH_KEY = String(2 - DOU_TYPE[0]);
const DOCUMENT_PK_SHIFT = 1000000000;
const CASE_PK_SHIFT = 2000000000;

const store = useStore();
const root = getCurrentInstance().proxy.$root;
const selectedResearches = ref<number[]>([]);
const overrideDepartments = ref<Record<string, unknown>[]>([]);
const overrideResearches = ref<Record<string, unknown>[]>([]);
const ready = ref(false);
const query = ref('');
const byNumber = ref(true);
const byText = ref(false);
const LIST_FILTER_STORAGE_KEY = 'document-manager-2-list-filter';
const LEFT_WIDTH_STORAGE_KEY = 'document-manager-2-left-width';
const DEFAULT_LEFT_WIDTH_PX = 448;
const MIN_LEFT_WIDTH_PX = 448;
const LIST_ROLE_FILTERS = ['created', 'doing', 'wrote', 'onControl', 'toReview', 'recent', 'toBeAgreed', 'onSignature'];
const SIDE_LIST_FILTERS = ['toReview', 'recent', 'toBeAgreed', 'onSignature'];

const readStoredListFilter = (): { role: string | null; hidden: boolean } => {
  try {
    const raw = localStorage.getItem(LIST_FILTER_STORAGE_KEY);
    if (!raw) {
      return { role: 'recent', hidden: false };
    }
    const data = JSON.parse(raw);
    const role = LIST_ROLE_FILTERS.includes(data?.role) ? data.role : null;
    const hidden = Boolean(data?.hidden) && !(role && SIDE_LIST_FILTERS.includes(role));
    return { role, hidden };
  } catch {
    return { role: 'recent', hidden: false };
  }
};

const storedListFilter = readStoredListFilter();

const readStoredLeftWidth = (): number => {
  try {
    const value = Number(localStorage.getItem(LEFT_WIDTH_STORAGE_KEY));
    if (Number.isFinite(value) && value >= MIN_LEFT_WIDTH_PX) {
      return value;
    }
  } catch {
    // ignore storage errors
  }
  return DEFAULT_LEFT_WIDTH_PX;
};

const leftWidthPx = ref(readStoredLeftWidth());

const onLeftWidthChange = (value: number) => {
  leftWidthPx.value = value;
};
const roleFilter = ref<string | null>(storedListFilter.role);
const showHidden = ref(storedListFilter.hidden);
const pendingReviewCount = ref(0);
const documents = ref<{ id: number; title: string; confirmed?: boolean }[]>([]);
const selectedDocument = ref<number | null>(null);
const docsEl = ref<HTMLElement | null>(null);
const recentPage = ref(1);
const recentHasMore = ref(false);
const isLoadingMoreRecent = ref(false);
const RECENT_PAGE_SIZE = 50;
let documentsLoadId = 0;

const roleButtons = [
  { id: 'created', label: 'Создал' },
  { id: 'doing', label: 'Исполняю' },
  { id: 'wrote', label: 'Поручил' },
  { id: 'onControl', label: 'Контролирую' },
];

const dateRange = ref<[string, string]>([
  moment().subtract(32, 'day').format('DD.MM.YY'),
  moment().format('DD.MM.YY'),
]);

const toApiDate = (value: string) => {
  const parsed = moment(value, 'DD.MM.YY', true);
  return parsed.isValid() ? parsed.format('YYYY-MM-DD') : value;
};

const toggleMode = (mode: 'number' | 'text') => {
  if (mode === 'number') {
    byNumber.value = true;
    byText.value = false;
    return;
  }
  byNumber.value = false;
  byText.value = true;
};

const userGroups = computed(() => store.getters.user_groups || []);
const canViewHidden = computed(() => userGroups.value.includes('Admin') || userGroups.value.includes('Скрытие документа'));
if (!canViewHidden.value) {
  showHidden.value = false;
}

const toggleRole = (id: string) => {
  if (SIDE_LIST_FILTERS.includes(id)) {
    showHidden.value = false;
  }
  roleFilter.value = roleFilter.value === id ? null : id;
};

const loadPendingCount = async () => {
  const { pendingReviewCount: count } = await api('document-manager/documents/list', { countOnly: true });
  pendingReviewCount.value = Number(count) || 0;
};

const loadRecent = async (append = false) => {
  const loadId = documentsLoadId;
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
    if (loadId !== documentsLoadId) {
      return;
    }
    const rows = data.result || [];
    recentPage.value = data.page || nextPage;
    recentHasMore.value = Boolean(data.hasMore);
    documents.value = append ? [...documents.value, ...rows] : rows;
  } finally {
    isLoadingMoreRecent.value = false;
  }
};

const onDocumentsScroll = () => {
  if (roleFilter.value !== 'recent') {
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
  const hasListFilter = roleFilter.value === 'created' || roleFilter.value === 'toReview' || roleFilter.value === 'recent';
  if (!hasListFilter && !showHidden.value) {
    await loadPendingCount();
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    if (roleFilter.value === 'recent') {
      await loadRecent(false);
      await loadPendingCount();
      return;
    }
    const { result, pendingReviewCount: count } = await api('document-manager/documents/list', {
      filter: roleFilter.value === 'created' || roleFilter.value === 'toReview' ? roleFilter.value : null,
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
  const next = !showHidden.value;
  showHidden.value = next;
  selectedDocument.value = null;
  if (next && roleFilter.value && SIDE_LIST_FILTERS.includes(roleFilter.value)) {
    roleFilter.value = null;
    return;
  }
  loadDocuments();
};

watch([query, byNumber, byText], () => {
  if (!byNumber.value || byText.value) {
    return;
  }
  const digits = query.value.replace(/[^0-9]/g, '');
  if (digits !== query.value) {
    query.value = digits;
  }
});

const searchDocuments = async () => {
  const text = query.value.trim();
  if (!text) {
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/documents/search', {
      query: text,
      byNumber: byNumber.value,
      byText: byText.value,
      dateFrom: toApiDate(dateRange.value[0]),
      dateTo: toApiDate(dateRange.value[1]),
    });
    if (result?.ok) {
      root.$emit('msg', 'ok', result.message || 'Найдено');
    } else {
      root.$emit('msg', 'error', result?.message || 'Документ не найден');
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const canCreate = computed(() => selectedResearches.value.length === 1);

const resolveTypeId = (pk: number): number | null => {
  const row = overrideResearches.value.find(item => Number(item.pk) === Number(pk));
  if (row?.is_dou_case_type) {
    const typeId = Number(row.defaultTypeDocumentId);
    return typeId > 0 ? typeId : null;
  }
  if (pk >= DOCUMENT_PK_SHIFT && pk < CASE_PK_SHIFT) {
    return pk - DOCUMENT_PK_SHIFT;
  }
  return null;
};

const createDocument = async () => {
  if (!canCreate.value) {
    return;
  }
  const typeId = resolveTypeId(selectedResearches.value[0]);
  if (!typeId) {
    root.$emit('msg', 'error', 'Не указан вид документа');
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/documents/create', { typeId });
    if (result?.ok) {
      root.$emit('msg', 'ok', 'Документ создан');
      selectedDocument.value = result.id;
    } else {
      root.$emit('msg', 'error', result?.message || 'Ошибка создания');
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

onMounted(async () => {
  await store.dispatch(actions.INC_LOADING);
  try {
    const data = await researchesPoint.getResearches({ params: { dou: 1 } });
    overrideDepartments.value = data?.departments || [];
    const researches = data?.researches || {};
    overrideResearches.value = researches[DOU_RESEARCH_KEY] || [];
  } finally {
    ready.value = true;
    await store.dispatch(actions.DEC_LOADING);
  }
  await loadDocuments();
});

watch(roleFilter, () => {
  loadDocuments();
});

watch([roleFilter, showHidden], () => {
  try {
    localStorage.setItem(LIST_FILTER_STORAGE_KEY, JSON.stringify({
      role: roleFilter.value,
      hidden: showHidden.value,
    }));
  } catch {
    // ignore storage errors
  }
});

watch(leftWidthPx, value => {
  try {
    localStorage.setItem(LEFT_WIDTH_STORAGE_KEY, String(value));
  } catch {
    // ignore storage errors
  }
});

const onVisibilityChange = () => {
  loadDocuments();
};

const onReviewed = () => {
  loadPendingCount();
};
</script>

<style scoped lang="scss">
.root {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  box-sizing: border-box;
  height: calc(100% - 4px);
  margin-bottom: 4px;
  background-color: #f8f7f7;
}

.top-panel {
  display: flex;
  align-items: stretch;
  flex: 0 0 34px;
  width: 100%;
  height: 34px;
  min-height: 34px;
  background-color: #f8f7f7;
}

.search-dates {
  flex: 0 0 126px;
  width: 126px;
  height: 34px;

  ::v-deep .input-daterange {
    width: 126px;
  }

  ::v-deep .form-control,
  ::v-deep .input-group-addon {
    border-radius: 0;
  }
}

.search {
  flex: 0 0 31.25%;
  max-width: 31.25%;
  min-width: 120px;
  height: 34px;
  border-radius: 0;
  padding-left: 10px;
}

.top-panel .btn {
  height: 34px;
  border-radius: 0;
}

.mode-check {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 0 0 auto;
  margin: 0;
  height: 34px;
  padding: 0 8px;
  font-size: 12px;
  font-weight: normal;
  cursor: pointer;
  white-space: nowrap;

  input {
    margin: 0;
    pointer-events: none;
  }
}

.body {
  position: relative;
  flex: 1 1 auto;
  min-height: 0;
  width: 100%;
}

.main {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

.side {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-height: 0;
  background-color: #fff;
}

.side-filters {
  display: flex;
  flex-direction: column;
  flex: 0 0 auto;
}

.side-filter-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(112px, 1fr));
}

.side-check {
  flex: 0 0 auto;
  width: auto;
  min-width: 0;
  height: 25px;
  padding: 0 6px;
}

.side-check-hidden {
  width: max-content;
}

.viewer {
  flex: 1 1 auto;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  background-color: #fff;
}

.filter-check {
  display: flex;
  align-items: center;
  gap: 4px;
  width: 100%;
  height: 25px;
  margin: 0;
  padding: 0 8px;
  font-size: 12px;
  font-weight: normal;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;

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

.doc-list {
  flex: 1 1 auto;
  width: 0;
  min-width: 100%;
  min-height: 0;
  overflow-y: auto;
}

.doc-row {
  min-height: 34px;
  border-bottom: 1px solid #b1b1b1;

  &:first-child {
    border-top: 1px solid #b1b1b1;
  }
}

.doc-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  min-height: 34px;
  padding: 1px 8px 1px 10px;
  border: none;
  background-color: transparent;
  color: #434a54;
  font-size: 12px;
  line-height: 16px;
  text-align: left;
  overflow: hidden;

  &:hover {
    background-color: #434a54;
    color: #fff;
  }
}

.doc-title {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  overflow-wrap: anywhere;
  text-align: left;
}

.doc-draft {
  flex: 0 0 auto;
}

.active-button {
  background-color: #049372;
  color: #fff;
}

.picker {
  flex: 0 0 auto;
  flex-shrink: 0;
  width: 100%;
  height: auto;
  position: relative;
  margin-top: auto;
}

.create-btn {
  flex: 0 0 auto;
  height: 34px;
  border-radius: 0;
}
</style>
