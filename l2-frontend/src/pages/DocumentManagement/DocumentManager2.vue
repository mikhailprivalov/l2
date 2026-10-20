<template>
  <div class="root">
  <div class="body">
    <TwoSidedLayout
      :left-width-px="leftWidthPx"
      :min-left-width-px="MIN_LEFT_WIDTH_PX"
      :min-right-width-px="360"
      resizable
      cover-gutter
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
        <div class="side-check-line">
          <label
            class="filter-check side-check side-check-hidden"
            @click.prevent="toggleMyCases"
          >
            <input
              type="checkbox"
              :checked="showMyCases"
              tabindex="-1"
            >
            <span>Мои дела</span>
          </label>
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
          <label
            class="filter-check side-check side-check-hidden"
            @click.prevent="toggleParticipant"
          >
            <input
              type="checkbox"
              :checked="showParticipant"
              tabindex="-1"
            >
            <span>Участник</span>
          </label>
          <label
            class="filter-check side-check side-check-hidden"
            @click.prevent="toggleTopics"
          >
            <input
              type="checkbox"
              :checked="showTopics"
              tabindex="-1"
            >
            <span>Блоки</span>
          </label>
          <button
            v-if="showTopics && canCreateBlocks"
            class="blocks-add"
            type="button"
            @click="openBlockModal"
          >
            <i class="fa-regular fa-square-plus" />
          </button>
        </div>
      </div>
      <div
        v-if="listFilterActive"
        class="list-filter-row"
      >
        <input
          v-model="listQuery"
          class="form-control list-filter"
          type="text"
          placeholder="Фильтр"
          spellcheck="false"
        >
        <div
          v-if="showParticipant"
          class="side-check-line list-filter-kinds"
        >
          <label
            class="filter-check side-check side-check-hidden"
            @click.prevent="participantDocuments = !participantDocuments"
          >
            <input
              type="checkbox"
              :checked="participantDocuments"
              tabindex="-1"
            >
            <span>Документы</span>
          </label>
          <label
            class="filter-check side-check side-check-hidden"
            @click.prevent="toggleParticipantCases"
          >
            <input
              type="checkbox"
              :checked="participantCases"
              tabindex="-1"
            >
            <span>Дела</span>
          </label>
        </div>
      </div>
      <div
        ref="docsEl"
        class="doc-list"
        @scroll="onDocumentsScroll"
      >
        <template v-if="showTopics">
          <div
            v-for="block in visibleBlocks"
            :key="`block-${block.id}`"
            class="doc-row"
          >
            <button
              class="doc-btn"
              :class="{ 'active-button': selectedBlock === block.id }"
              type="button"
              @click="selectBlock(block.id)"
            >
              <span class="doc-title">{{ blockLabel(block) }}</span>
            </button>
          </div>
        </template>
        <template v-else-if="caseSearch">
          <div
            v-for="row in visibleDocuments"
            :key="`case-${row.id}`"
            class="doc-row"
          >
            <button
              class="doc-btn"
              :class="{ 'active-button': selectedCase === row.id }"
              type="button"
              @click="selectCase(row.id)"
            >
              <span class="doc-title">{{ row.title }}</span>
            </button>
            <button
              v-if="showParticipant && row.isMine === false"
              class="case-mark"
              :class="{ 'case-mark--on': row.inMyCases }"
              type="button"
              :title="row.inMyCases ? 'Убрать из моих дел' : 'В мои дела'"
              @click="toggleMyCase(row)"
            >
              <i :class="row.inMyCases ? 'fa-solid fa-briefcase' : 'fa-regular fa-briefcase'" />
            </button>
            <button
              v-if="showParticipant && row.isFavorite !== undefined"
              class="case-mark"
              :class="{ 'case-mark--on': row.isFavorite }"
              type="button"
              :title="row.isFavorite ? 'Убрать из избранного' : 'В избранное'"
              @click="toggleCaseStar(row)"
            >
              <i class="fa fa-star" />
            </button>
          </div>
        </template>
        <template v-else>
          <div
            v-for="document in visibleDocuments"
            :key="document.id"
            class="doc-row"
          >
          <button
            class="doc-btn"
            :class="{ 'active-button': selectedDocument === document.id }"
            type="button"
            @click="selectDocument(document.id)"
          >
            <span class="doc-title">{{ document.title }}</span>
            <i
              v-if="roleFilter === 'created' && !document.confirmed"
              class="fa-solid fa-pen doc-draft"
            />
          </button>
          <button
            v-if="showMyCases && document.caseId"
            class="case-mark"
            :class="{ 'case-mark--on': document.isFavorite }"
            type="button"
            :title="document.isFavorite ? 'Убрать из избранного' : 'В избранное'"
            @click="toggleCaseStar(document)"
          >
            <i class="fa fa-star" />
          </button>
          </div>
        </template>
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
        <button
          class="clear-x"
          type="button"
          title="Очистить даты"
          @click="clearDates"
        >
          ×
        </button>
        <div class="search-dates">
          <DateRange
            v-model="dateRange"
            small
            allow-empty
          />
        </div>
        <button
          class="clear-x"
          type="button"
          title="Очистить поиск"
          @click="clearQuery"
        >
          ×
        </button>
        <input
          v-model="query"
          class="form-control search"
          :placeholder="searchPlaceholder"
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
          @click.prevent="toggleMode('case')"
        >
          <input
            type="checkbox"
            :checked="byCase"
            tabindex="-1"
          >
          <span>по делу</span>
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
        <DocumentBlockPanel
          v-if="showTopics"
          :block-id="selectedBlock"
        />
        <DocumentViewer
          v-else
          :document-id="caseSearch ? null : selectedDocument"
          :case-id="caseSearch ? selectedCase : null"
          :show-case-documents="showCaseDocuments || caseSearch"
          :approval-mode="roleFilter === 'toBeAgreed'"
          @visibility-change="onVisibilityChange"
          @reviewed="onReviewed"
          @approved="onApproved"
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
        ref="picker"
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
          <button
            class="btn btn-blue-nb create-btn"
            type="button"
            :disabled="!canCreate"
            @click="toggleFavorite"
          >
            В избранное
          </button>
        </template>
      </ResearchesPicker>
    </div>
  <Modal
    v-if="caseTopicModalOpen"
    show-footer="true"
    white-bg="true"
    max-width="480px"
    width="100%"
    margin-left-right="auto"
    @close="closeCaseTopicModal"
  >
    <span slot="header">Тема дела</span>
    <div slot="body">
      <label class="case-topic-label">
        <span>Тема дела</span>
        <input
          v-model="caseTopicDraft"
          type="text"
          class="form-control"
          autofocus
          @keyup.enter="confirmCaseTopic"
        >
      </label>
    </div>
    <div
      slot="footer"
      class="case-topic-footer"
    >
      <button
        type="button"
        class="btn btn-blue-nb"
        @click="closeCaseTopicModal"
      >
        Отмена
      </button>
      <button
        type="button"
        class="btn btn-blue-nb"
        :disabled="!caseTopicDraft.trim()"
        @click="confirmCaseTopic"
      >
        Создать
      </button>
    </div>
  </Modal>
  <Modal
    v-if="blockModalOpen"
    show-footer="true"
    white-bg="true"
    max-width="480px"
    width="100%"
    margin-left-right="auto"
    @close="closeBlockModal"
  >
    <span slot="header">Блок</span>
    <div slot="body">
      <label class="case-topic-label">
        <span>Название</span>
        <input
          v-model="blockTitleDraft"
          type="text"
          class="form-control"
          autofocus
          @keyup.enter="confirmBlock"
        >
      </label>
    </div>
    <div
      slot="footer"
      class="case-topic-footer"
    >
      <button
        type="button"
        class="btn btn-blue-nb"
        @click="closeBlockModal"
      >
        Отмена
      </button>
      <button
        type="button"
        class="btn btn-blue-nb"
        :disabled="!blockTitleDraft.trim()"
        @click="confirmBlock"
      >
        Создать
      </button>
    </div>
  </Modal>
  </div>
</template>

<script setup lang="ts">
import {
  computed, getCurrentInstance, onMounted, onUnmounted, ref, watch,
} from 'vue';
import moment from 'moment';

import researchesPoint from '@/api/researches-point';
import api from '@/api';
import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import DateRange from '@/ui-cards/DateRange.vue';
import DocumentViewer from '@/pages/DocumentManagement/DocumentViewer.vue';
import DocumentBlockPanel from '@/pages/DocumentManagement/DocumentBlockPanel.vue';
import TwoSidedLayout from '@/layouts/TwoSidedLayout.vue';
import ResearchesPicker from '@/ui-cards/ResearchesPicker.vue';
import Modal from '@/ui-cards/Modal.vue';

const DOU_TYPE = [10010];
const DOU_RESEARCH_KEY = String(2 - DOU_TYPE[0]);
const DOCUMENT_PK_SHIFT = 1000000000;
const CASE_PK_SHIFT = 2000000000;

const store = useStore();
const root = getCurrentInstance().proxy.$root;
const selectedResearches = ref<number[]>([]);
const picker = ref<{ favoritePks: number[] } | null>(null);
const overrideDepartments = ref<Record<string, unknown>[]>([]);
const overrideResearches = ref<Record<string, unknown>[]>([]);
const ready = ref(false);
const caseTopicModalOpen = ref(false);
const caseTopicDraft = ref('');
const pendingCreate = ref<{ typeId: number | null; caseId: number | null } | null>(null);
const query = ref('');
const byNumber = ref(true);
const byCase = ref(false);
const byText = ref(false);
const LIST_FILTER_STORAGE_KEY = 'document-manager-2-list-filter';
const LEFT_WIDTH_STORAGE_KEY = 'document-manager-2-left-width';
const DEFAULT_LEFT_WIDTH_PX = 448;
const MIN_LEFT_WIDTH_PX = 448;
const LIST_ROLE_FILTERS = ['created', 'doing', 'wrote', 'onControl', 'toReview', 'recent', 'toBeAgreed', 'onSignature'];

const readStoredListFilter = (): {
  role: string | null; hidden: boolean; myCases: boolean; topics: boolean; participant: boolean;
} => {
  try {
    const raw = localStorage.getItem(LIST_FILTER_STORAGE_KEY);
    if (!raw) {
      return {
        role: 'recent', hidden: false, myCases: false, topics: false, participant: false,
      };
    }
    const data = JSON.parse(raw);
    const role = LIST_ROLE_FILTERS.includes(data?.role) ? data.role : null;
    const topics = Boolean(data?.topics) && !role;
    const hidden = Boolean(data?.hidden) && !role && !topics;
    const myCases = Boolean(data?.myCases) && !hidden && !role && !topics;
    const participant = Boolean(data?.participant) && !role && !topics && !hidden && !myCases;
    return {
      role, hidden, myCases, topics, participant,
    };
  } catch {
    return {
      role: 'recent', hidden: false, myCases: false, topics: false, participant: false,
    };
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
const showMyCases = ref(storedListFilter.myCases);
const showTopics = ref(storedListFilter.topics);
const showParticipant = ref(storedListFilter.participant);
const participantDocuments = ref(true);
const participantCases = ref(true);
const pendingReviewCount = ref(0);
type ListRow = {
  id: number;
  title: string;
  confirmed?: boolean;
  caseId?: number;
  isMine?: boolean;
  inMyCases?: boolean;
  isFavorite?: boolean;
};
const documents = ref<ListRow[]>([]);
const listQuery = ref('');
const blocks = ref<{ id: number; title: string; creator: string; createdAt: string }[]>([]);
const selectedDocument = ref<number | null>(null);
const selectedCase = ref<number | null>(null);
const caseSearch = ref(false);
const selectedBlock = ref<number | null>(null);
const blockModalOpen = ref(false);
const blockTitleDraft = ref('');
const openedFromCaseFavorite = ref(false);
const showCaseDocuments = computed(() => showMyCases.value || openedFromCaseFavorite.value);
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
  { id: 'onControl', label: 'Контроль' },
];

const dateRange = ref<[string, string]>([
  moment().subtract(32, 'day').format('DD.MM.YY'),
  moment().format('DD.MM.YY'),
]);

const toApiDate = (value: string) => {
  const parsed = moment(value, 'DD.MM.YY', true);
  return parsed.isValid() ? parsed.format('YYYY-MM-DD') : value;
};

const toggleMode = (mode: 'number' | 'case' | 'text') => {
  byNumber.value = mode === 'number';
  byCase.value = mode === 'case';
  byText.value = mode === 'text';
};

const searchPlaceholder = computed(() => {
  if (byText.value) {
    return 'Номер или текст';
  }
  if (byCase.value) {
    return 'Тема дела';
  }
  return 'Номер документа';
});

const userGroups = computed(() => store.getters.user_groups || []);
const canViewHidden = computed(() => userGroups.value.includes('Admin') || userGroups.value.includes('Скрытие документа'));
const canCreateBlocks = computed(() => userGroups.value.includes('Admin') || userGroups.value.includes('Создание блоков'));
const listFilterActive = computed(() => Boolean(
  roleFilter.value || showHidden.value || showMyCases.value || showTopics.value || showParticipant.value,
));
if (!canViewHidden.value) {
  showHidden.value = false;
}

const toggleRole = (id: string) => {
  listQuery.value = '';
  const next = roleFilter.value === id ? null : id;
  showMyCases.value = false;
  showTopics.value = false;
  showParticipant.value = false;
  if (next) {
    showHidden.value = false;
  }
  roleFilter.value = next;
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

const loadDocuments = async (keepSelection = false) => {
  const loadId = ++documentsLoadId;
  const previousCase = selectedCase.value;
  documents.value = [];
  caseSearch.value = false;
  selectedCase.value = null;
  recentPage.value = 1;
  recentHasMore.value = false;
  const hasListFilter = roleFilter.value === 'created'
    || roleFilter.value === 'toReview'
    || roleFilter.value === 'recent'
    || roleFilter.value === 'toBeAgreed';
  if (showTopics.value) {
    selectedDocument.value = null;
    await loadPendingCount();
    await store.dispatch(actions.INC_LOADING);
    try {
      const { result } = await api('document-manager/blocks/list');
      if (loadId !== documentsLoadId) {
        return;
      }
      blocks.value = result || [];
      const stillThere = blocks.value.some(row => row.id === selectedBlock.value);
      if (selectedBlock.value && !stillThere) {
        selectedBlock.value = null;
      }
    } finally {
      await store.dispatch(actions.DEC_LOADING);
    }
    return;
  }
  blocks.value = [];
  selectedBlock.value = null;
  if (showParticipant.value) {
    await loadPendingCount();
    if (!participantCases.value) {
      return;
    }
    await store.dispatch(actions.INC_LOADING);
    try {
      const data = await api('document-manager/documents/list', {
        participant: true,
        cases: true,
        dateFrom: toApiDate(dateRange.value[0]),
        dateTo: toApiDate(dateRange.value[1]),
      });
      if (loadId !== documentsLoadId) {
        return;
      }
      if (data?.message) {
        root.$emit('msg', 'error', data.message);
      }
      documents.value = data?.result || [];
      caseSearch.value = true;
      pendingReviewCount.value = Number(data?.pendingReviewCount) || 0;
      if (previousCase && documents.value.some(row => row.id === previousCase)) {
        selectedCase.value = previousCase;
      }
    } finally {
      await store.dispatch(actions.DEC_LOADING);
    }
    return;
  }
  if (!hasListFilter && !showHidden.value && !showMyCases.value) {
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
    const listFilter = roleFilter.value === 'created'
      || roleFilter.value === 'toReview'
      || roleFilter.value === 'toBeAgreed'
      ? roleFilter.value
      : null;
    const { result, pendingReviewCount: count } = await api('document-manager/documents/list', {
      filter: listFilter,
      hidden: Boolean(canViewHidden.value && showHidden.value),
      myCases: Boolean(showMyCases.value),
    });
    if (loadId !== documentsLoadId) {
      return;
    }
    documents.value = result || [];
    pendingReviewCount.value = Number(count) || 0;
    if (!keepSelection && selectedDocument.value && !documents.value.some(row => row.id === selectedDocument.value)) {
      selectedDocument.value = null;
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const onApproved = () => {
  loadDocuments(true);
};

const toggleHidden = () => {
  if (!canViewHidden.value) {
    return;
  }
  const next = !showHidden.value;
  listQuery.value = '';
  showHidden.value = next;
  selectedDocument.value = null;
  if (next) {
    showMyCases.value = false;
    showTopics.value = false;
    showParticipant.value = false;
  }
  if (next && roleFilter.value) {
    roleFilter.value = null;
    return;
  }
  loadDocuments();
};

const toggleMyCases = () => {
  listQuery.value = '';
  const next = !showMyCases.value;
  showMyCases.value = next;
  selectedDocument.value = null;
  if (next) {
    showHidden.value = false;
    showTopics.value = false;
    showParticipant.value = false;
    if (roleFilter.value) {
      roleFilter.value = null;
      return;
    }
  }
  loadDocuments();
};

const toggleParticipantCases = () => {
  participantCases.value = !participantCases.value;
  loadDocuments();
};

const toggleParticipant = () => {
  listQuery.value = '';
  const next = !showParticipant.value;
  showParticipant.value = next;
  selectedDocument.value = null;
  if (next) {
    participantDocuments.value = true;
    participantCases.value = true;
    showHidden.value = false;
    showMyCases.value = false;
    showTopics.value = false;
    if (roleFilter.value) {
      roleFilter.value = null;
      return;
    }
  }
  loadDocuments();
};

const toggleTopics = () => {
  listQuery.value = '';
  const next = !showTopics.value;
  showTopics.value = next;
  selectedDocument.value = null;
  openedFromCaseFavorite.value = false;
  if (next) {
    showHidden.value = false;
    showMyCases.value = false;
    showParticipant.value = false;
    if (roleFilter.value) {
      roleFilter.value = null;
      return;
    }
  }
  loadDocuments();
};

watch([query, byNumber, byCase, byText], () => {
  if (!byNumber.value || byCase.value || byText.value) {
    return;
  }
  const digits = query.value.replace(/[^0-9]/g, '');
  if (digits !== query.value) {
    query.value = digits;
  }
});

const clearDates = () => {
  dateRange.value = ['', ''];
};

const clearQuery = () => {
  query.value = '';
};

const searchDocuments = async () => {
  const text = query.value.trim();
  if (!text) {
    return;
  }
  const listSearch = !byText.value;
  const loadId = listSearch ? ++documentsLoadId : documentsLoadId;
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/documents/search', {
      query: text,
      byNumber: byNumber.value,
      byCase: byCase.value,
      byText: byText.value,
      dateFrom: toApiDate(dateRange.value[0]),
      dateTo: toApiDate(dateRange.value[1]),
    });
    if (listSearch && loadId !== documentsLoadId) {
      return;
    }
    if (result?.ok) {
      if (listSearch) {
        const rows = result.result || [];
        const searchingCases = byCase.value;
        showTopics.value = false;
        selectedBlock.value = null;
        documents.value = rows;
        recentPage.value = 1;
        recentHasMore.value = false;
        openedFromCaseFavorite.value = false;
        caseSearch.value = searchingCases;
        if (searchingCases) {
          selectedDocument.value = null;
          selectedCase.value = rows[0]?.id || null;
        } else {
          selectedCase.value = null;
          selectedDocument.value = rows[0]?.id || null;
        }
      }
      root.$emit('msg', 'ok', result.message || 'Найдено');
    } else {
      if (listSearch) {
        documents.value = [];
        recentHasMore.value = false;
        caseSearch.value = false;
        selectedCase.value = null;
        selectedDocument.value = null;
      }
      root.$emit('msg', 'error', result?.message || 'Документ не найден');
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const canCreate = computed(() => selectedResearches.value.length === 1);

const resolveCreate = (pk: number): { typeId: number | null; caseId: number | null } => {
  const row = overrideResearches.value.find(item => Number(item.pk) === Number(pk));
  if (row?.is_dou_case_type) {
    const typeId = Number(row.defaultTypeDocumentId);
    return {
      typeId: typeId > 0 ? typeId : null,
      caseId: pk - CASE_PK_SHIFT,
    };
  }
  if (pk >= DOCUMENT_PK_SHIFT && pk < CASE_PK_SHIFT) {
    return { typeId: pk - DOCUMENT_PK_SHIFT, caseId: null };
  }
  return { typeId: null, caseId: null };
};

const toggleFavorite = async () => {
  const pk = selectedResearches.value[0];
  if (!pk) {
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/favorites/toggle', { pk });
    if (result?.ok) {
      if (picker.value) {
        picker.value.favoritePks = result.pks || [];
      }
      root.$emit('msg', 'ok', result.favorite ? 'Добавлено в избранное' : 'Убрано из избранного');
    } else {
      root.$emit('msg', 'error', result?.message || 'Не удалось изменить избранное');
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const runCreate = async (payload: { typeId: number | null; caseId: number | null; topic?: string }) => {
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/documents/create', {
      typeId: payload.typeId,
      caseId: payload.caseId,
      topic: payload.topic || '',
    });
    if (result?.ok) {
      if (result.emptyCase) {
        root.$emit('msg', 'ok', 'Дело создано');
        openedFromCaseFavorite.value = false;
        selectedDocument.value = null;
      } else {
        root.$emit('msg', 'ok', 'Документ создан');
        openedFromCaseFavorite.value = false;
        selectedDocument.value = result.id;
      }
    } else {
      root.$emit('msg', 'error', result?.message || 'Ошибка создания');
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const createDocument = async () => {
  if (!canCreate.value) {
    return;
  }
  const resolved = resolveCreate(selectedResearches.value[0]);
  if (resolved.caseId) {
    pendingCreate.value = resolved;
    caseTopicDraft.value = '';
    caseTopicModalOpen.value = true;
    return;
  }
  if (!resolved.typeId) {
    root.$emit('msg', 'error', 'Не указан вид документа');
    return;
  }
  await runCreate(resolved);
};

const closeCaseTopicModal = () => {
  caseTopicModalOpen.value = false;
  pendingCreate.value = null;
  caseTopicDraft.value = '';
};

const confirmCaseTopic = async () => {
  const topic = caseTopicDraft.value.trim();
  if (!topic) {
    root.$emit('msg', 'error', 'Укажите тему дела');
    return;
  }
  if (!pendingCreate.value) {
    return;
  }
  const payload = { ...pendingCreate.value, topic };
  closeCaseTopicModal();
  await runCreate(payload);
};

const selectDocument = (id: number) => {
  openedFromCaseFavorite.value = false;
  caseSearch.value = false;
  selectedCase.value = null;
  selectedDocument.value = id;
};

const selectCase = (id: number) => {
  selectedCase.value = id;
  selectedDocument.value = null;
};

const patchListRow = (id: number, patch: Partial<ListRow>) => {
  const index = documents.value.findIndex(item => item.id === id);
  if (index < 0) {
    return;
  }
  documents.value.splice(index, 1, { ...documents.value[index], ...patch });
};

const toggleMyCase = async (row: ListRow) => {
  const result = await api('document-manager/cases/my', { id: row.id });
  if (!result?.ok) {
    root.$emit('msg', 'error', result?.message || 'Не удалось изменить мои дела');
    return;
  }
  patchListRow(row.id, { inMyCases: Boolean(result.inMyCases) });
};

const patchCaseFavorite = (caseId: number, favorite: boolean) => {
  documents.value = documents.value.map(item => (
    item.id === caseId || item.caseId === caseId ? { ...item, isFavorite: favorite } : item
  ));
};

const toggleCaseStar = async (row: ListRow) => {
  const caseId = row.caseId || row.id;
  const result = await api('document-manager/record-favorites/toggle', { caseId });
  if (!result?.ok) {
    root.$emit('msg', 'error', result?.message || 'Не удалось изменить избранное');
    return;
  }
  patchCaseFavorite(caseId, Boolean(result.favorite));
  root.$emit('dou-favorites-changed', { caseId, favorite: result.favorite, case: true });
};

const blockLabel = (block: { title: string; creator: string; createdAt: string }) => (
  [block.title, block.creator, block.createdAt].filter(part => (part || '').trim()).join(', ')
);

const folded = (value: string) => (value || '').toLocaleLowerCase();

const visibleDocuments = computed(() => {
  const filterText = folded(listQuery.value.trim());
  if (!filterText) {
    return documents.value;
  }
  return documents.value.filter(row => folded(row.title).includes(filterText));
});

const visibleBlocks = computed(() => {
  const filterText = folded(listQuery.value.trim());
  if (!filterText) {
    return blocks.value;
  }
  return blocks.value.filter(row => folded(blockLabel(row)).includes(filterText));
});

const selectBlock = (id: number) => {
  selectedBlock.value = id;
};

const openBlockModal = () => {
  blockTitleDraft.value = '';
  blockModalOpen.value = true;
};

const closeBlockModal = () => {
  blockModalOpen.value = false;
  blockTitleDraft.value = '';
};

const confirmBlock = async () => {
  const title = blockTitleDraft.value.trim();
  if (!title) {
    root.$emit('msg', 'error', 'Укажите название блока');
    return;
  }
  const result = await api('document-manager/blocks/create', { title });
  if (!result?.ok) {
    root.$emit('msg', 'error', result?.message || 'Не удалось создать блок');
    return;
  }
  closeBlockModal();
  selectedBlock.value = result.id;
  await loadDocuments();
};

const openFavorite = (payload: number | { id?: number; cases?: boolean }) => {
  const id = typeof payload === 'number' ? payload : Number(payload?.id);
  openedFromCaseFavorite.value = typeof payload === 'object' && Boolean(payload?.cases);
  if (id) {
    const topicsWereOn = showTopics.value;
    showTopics.value = false;
    selectedBlock.value = null;
    caseSearch.value = false;
    selectedCase.value = null;
    selectedDocument.value = id;
    if (topicsWereOn) {
      loadDocuments();
    }
  }
};

const openDocumentFromQuery = () => {
  const id = Number(new URLSearchParams(window.location.search).get('document'));
  if (id > 0) {
    openedFromCaseFavorite.value = false;
    showTopics.value = false;
    selectedBlock.value = null;
    caseSearch.value = false;
    selectedCase.value = null;
    selectedDocument.value = id;
  }
};

const onCaseFavoriteChanged = (payload?: { caseId?: number; favorite?: boolean; case?: boolean }) => {
  if (!payload?.case || !payload.caseId) {
    return;
  }
  patchCaseFavorite(Number(payload.caseId), Boolean(payload.favorite));
};

onMounted(() => {
  openDocumentFromQuery();
  root.$on('open-dou-document', openFavorite);
  root.$on('dou-favorites-changed', onCaseFavoriteChanged);
});

onUnmounted(() => {
  root.$off('open-dou-document', openFavorite);
  root.$off('dou-favorites-changed', onCaseFavoriteChanged);
});

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

watch(dateRange, () => {
  if (showParticipant.value) {
    loadDocuments();
  }
}, { deep: true });

watch([roleFilter, showHidden, showMyCases, showTopics, showParticipant], () => {
  try {
    localStorage.setItem(LIST_FILTER_STORAGE_KEY, JSON.stringify({
      role: roleFilter.value,
      hidden: showHidden.value,
      myCases: showMyCases.value,
      topics: showTopics.value,
      participant: showParticipant.value,
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
  margin-left: 0;
  padding-left: 0;
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

.clear-x {
  box-sizing: border-box;
  flex: 0 0 34px;
  width: 34px;
  height: 34px;
  margin: 0;
  padding: 0;
  border: 1px solid #aab2bd;
  border-radius: 0;
  background: #aab2bd;
  color: #fff;
  font-size: 16px;
  line-height: 32px;

  &:hover {
    background: #434a54;
    border-color: #434a54;
    color: #fff;
  }
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

.side-check-line {
  display: flex;
  flex-direction: row;
  align-items: center;
}

.side-check-line .filter-check {
  width: max-content;
  flex: 0 0 auto;
  overflow: visible;
}

.blocks-add {
  align-self: center;
  flex: 0 0 auto;
  margin: 0 4px 0 0;
  padding: 0;
  border: none;
  background: transparent;
  color: #434a54;
  font-size: 14px;
  line-height: 16px;
}

.doc-list {
  flex: 1 1 auto;
  width: 0;
  min-width: 100%;
  min-height: 0;
  overflow-y: auto;
}

.list-filter-row {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  flex: 0 0 34px;
  box-sizing: border-box;
  height: 34px;
  min-width: 0;
  border-top: 1px solid #b1b1b1;
}

.list-filter-kinds {
  flex: 0 0 auto;
  align-items: center;
}

.list-filter {
  flex: 1 1 auto;
  align-self: stretch;
  width: auto;
  min-width: 0;
  height: auto;
  margin: 0;
  border-color: #b1b1b1;
  border-top: 0;
  border-right: 0;
  border-bottom: 0;
  border-radius: 0;
  box-shadow: none;
}

.doc-row {
  display: flex;
  align-items: stretch;
  min-height: 34px;
  border-bottom: 1px solid #b1b1b1;

  &:first-child {
    border-top: 1px solid #b1b1b1;
  }
}

.case-mark {
  flex: 0 0 28px;
  border: none;
  background: transparent;
  color: #aab2bd;
  cursor: pointer;
}

.case-mark--on {
  color: #93046d;
}

.doc-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1 1 auto;
  width: auto;
  min-width: 0;
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

.case-topic-label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}

.case-topic-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
