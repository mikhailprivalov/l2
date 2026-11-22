<template>
  <div class="root">
    <div class="top-panel">
      <label
        v-for="item in roleButtons"
        :key="item.id"
        class="filter-check"
        @click.prevent="toggleRole(item.id)"
      >
        <input
          type="checkbox"
          :checked="roleFilter === item.id"
          tabindex="-1"
        >
        <span>{{ item.label }}</span>
      </label>
      <label
        class="filter-check"
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
        class="filter-check"
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
        class="filter-check"
        @click.prevent="toggleRole('onSignature')"
      >
        <input
          type="checkbox"
          :checked="roleFilter === 'onSignature'"
          tabindex="-1"
        >
        <span>Подписать {{ pendingSignatureCount }}</span>
      </label>
      <label
        class="filter-check"
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
        class="filter-check"
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
        class="filter-check"
        @click.prevent="toggleTests"
      >
        <input
          type="checkbox"
          :checked="showTests"
          tabindex="-1"
        >
        <span>Тесты</span>
      </label>
      <label
        class="filter-check"
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
    <RadioField
      v-model="direction"
      class="direction-row"
      :variants="directionVariants"
      :bages="directionBadges"
    />
    <div
      ref="splitEl"
      class="split"
    >
      <TwoSidedLayout
        :left-width-px="leftWidthPx"
        :min-left-width-px="MIN_SIDE_WIDTH_PX"
        :min-right-width-px="MIN_SIDE_WIDTH_PX"
        resizable
        cover-gutter
        @update:left-width-px="onLeftWidthChange"
      >
        <template #left>
          <div class="doc-pane">
            <input
              v-if="listFilterActive"
              v-model="listQuery"
              class="form-control list-filter"
              type="text"
              placeholder="Фильтр"
              spellcheck="false"
            >
            <div
              ref="docsEl"
              class="doc-list"
              @scroll="onDocumentsScroll"
            >
            <template v-if="showTests">
              <div
                v-for="test in visibleTests"
                :key="`test-${test.id}`"
                class="doc-row"
              >
                <button
                  class="doc-btn"
                  :class="{ 'active-button': selectedTest === test.id }"
                  type="button"
                  @click="selectTest(test.id)"
                >
                  <span class="doc-title">{{ test.shortTitle || test.title }}</span>
                </button>
              </div>
            </template>
            <template v-else-if="showTopics">
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
            <table
              v-else-if="tableMode"
              class="incoming-table"
            >
              <thead>
                <tr>
                  <th>Номер</th>
                  <th>Вид документа</th>
                  <th>Подразделение</th>
                  <th>Подписал ЭЦП</th>
                  <th>Подтвердил</th>
                  <th class="incoming-table__eye" />
                  <th class="incoming-table__reg" />
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="document in visibleDocuments"
                  :key="`${document.id}-${document.caseId || 0}`"
                  :class="{ 'incoming-table__active': isRowSelected(document) }"
                >
                  <td>{{ document.number || document.id }}</td>
                  <td>{{ document.typeTitle }}</td>
                  <td>{{ document.department }}</td>
                  <td>{{ document.signedBy }}</td>
                  <td>{{ document.confirmedBy }}</td>
                  <td class="incoming-table__eye">
                    <button
                      class="doc-eye"
                      type="button"
                      title="Открыть"
                      @click="selectListRow(document)"
                    >
                      <i class="fas fa-eye" />
                    </button>
                  </td>
                  <td class="incoming-table__reg">
                    <button
                      v-if="!document.registrationNumber"
                      class="doc-reg"
                      type="button"
                      title="Зарегистрировать"
                      @click="registerRow(document)"
                    >
                      Р
                    </button>
                    <template v-else>
                      <span>{{ document.registrationNumber }}</span>
                      <button
                        v-if="internalJournal"
                        class="doc-resolution"
                        type="button"
                        title="Резолюция"
                        @click="openResolution(document)"
                      >
                        <i class="fa-regular fa-pen-to-square" />
                      </button>
                    </template>
                  </td>
                </tr>
              </tbody>
            </table>
            <template v-else>
              <div
                v-for="document in visibleDocuments"
                :key="`${document.id}-${document.caseId || 0}`"
                class="doc-row"
              >
              <button
                class="doc-btn"
                :class="{ 'active-button': isRowSelected(document) }"
                type="button"
                @click="selectListRow(document)"
              >
                <span class="doc-title">{{ document.title }}</span>
                <i
                  v-if="roleFilter === 'created' && !document.confirmed"
                  class="fa-solid fa-pen doc-draft"
                />
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
          </div>
        </template>
        <template #right>
          <div class="split-right">
            <DocumentTestPanel
              v-if="showTests"
              :test-id="selectedTest"
            />
            <DocumentBlockPanel
              v-else-if="showTopics"
              :block-id="selectedBlock"
            />
            <DocumentViewer
              v-else
              :document-id="viewerDocumentId"
              :case-id="viewerCaseId"
              :show-case-documents="Boolean(viewerCaseId)"
              :registered-number="openRegistrationNumber"
              @reviewed="loadPendingCount"
              @opened="loadPendingCount"
              @visibility-change="loadDocuments"
            />
            <div
              v-if="resolutionDocumentId"
              class="resolution-pane"
            >
              <div class="resolution-pane__title">
                Резолюция {{ resolutionNumber }}
              </div>
              <div
                ref="resolutionBody"
                class="resolution-pane__body"
              >
                <div
                  v-for="(row, index) in resolutionRows"
                  :key="row.key"
                  class="resolution-pair"
                >
                  <textarea
                    v-model="row.note"
                    class="form-control resolution-note"
                    rows="1"
                    maxlength="255"
                    placeholder="Резолюция"
                    @input="fitResolutionNote"
                  />
                  <AddresseeField
                    :value="row.addressee"
                    header="Адресат"
                    @input="onResolutionAddressee(row.key, $event)"
                  />
                  <button
                    class="resolution-remove"
                    type="button"
                    title="Убрать"
                    @click="removeResolutionRow(index)"
                  >
                    ×
                  </button>
                </div>
                <button
                  class="btn btn-blue-nb resolution-add"
                  type="button"
                  @click="addResolutionRow"
                >
                  Добавить
                </button>
              </div>
              <div class="resolution-pane__footer">
                <button
                  class="btn btn-blue-nb"
                  type="button"
                  @click="closeResolution"
                >
                  Закрыть
                </button>
                <button
                  class="btn btn-blue-nb"
                  type="button"
                  @click="saveResolutions"
                >
                  Сохранить
                </button>
              </div>
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
        kk="dour"
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
  <MonitoringPeriodModal
    :open="monitoringModalOpen"
    :direction-params-id="monitoringDirectionParamsId"
    @close="closeMonitoringModal"
    @confirm="confirmMonitoringPeriod"
  />
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
  computed, getCurrentInstance, nextTick, onMounted, ref, watch,
} from 'vue';
import moment from 'moment';

import researchesPoint from '@/api/researches-point';
import api from '@/api';
import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import DateRange from '@/ui-cards/DateRange.vue';
import RadioField from '@/fields/RadioField.vue';
import ResearchesPicker from '@/ui-cards/ResearchesPicker.vue';
import TwoSidedLayout from '@/layouts/TwoSidedLayout.vue';
import Modal from '@/ui-cards/Modal.vue';
import DocumentBlockPanel from '@/pages/DocumentManagement/DocumentBlockPanel.vue';
import MonitoringPeriodModal from '@/pages/DocumentManagement/MonitoringPeriodModal.vue';
import DocumentTestPanel from '@/pages/DocumentManagement/DocumentTestPanel.vue';
import DocumentViewer from '@/pages/DocumentManagement/DocumentViewer.vue';
import AddresseeField from '@/forms/Fields/AddresseeField.vue';

const LEFT_WIDTH_STORAGE_KEY = 'document-registrar-left-width';
const TABLE_LEFT_WIDTH_STORAGE_KEY = 'document-registrar-left-width-table';
const MIN_SIDE_WIDTH_PX = 80;
const ISSUING_BUTTON_CENTER = 0.3;

const DOU_TYPE = [10010];
const DOU_RESEARCH_KEY = String(2 - DOU_TYPE[0]);
const DOCUMENT_PK_SHIFT = 1000000000;
const CASE_PK_SHIFT = 2000000000;

type DocumentJournalRow = {
  id: number;
  title: string;
  showsSignedChiefs: boolean;
};
const journals = ref<DocumentJournalRow[]>([]);
const direction = ref('');
const directionVariants = computed(() => journals.value.map(row => row.title));
const selectedJournal = computed(() => journals.value.find(row => row.title === direction.value) || null);
const journalBadges = ref<Record<string, number>>({});
const directionBadges = computed(() => {
  const badges: Record<string, string> = {};
  journals.value.forEach(row => {
    if (row.showsSignedChiefs) {
      badges[row.title] = String(Number(journalBadges.value[String(row.id)]) || 0);
    }
  });
  return badges;
});

const store = useStore();
const root = getCurrentInstance().proxy.$root;
const selectedResearches = ref<number[]>([]);
const picker = ref<{ favoritePks: number[] } | null>(null);
const overrideDepartments = ref<Record<string, unknown>[]>([]);
const overrideResearches = ref<Record<string, unknown>[]>([]);
const ready = ref(false);
const caseTopicModalOpen = ref(false);
const caseTopicDraft = ref('');
const monitoringModalOpen = ref(false);
const monitoringDirectionParamsId = ref(0);

type CreatePayload = {
  typeId: number | null;
  caseId: number | null;
  topic?: string;
  monitoringDirectionParams?: number;
  periodParams?: Record<string, unknown> | null;
};

const pendingCreate = ref<CreatePayload | null>(null);
const splitEl = ref<HTMLElement | null>(null);

const readStoredLeftWidth = (key: string): number | null => {
  try {
    const value = Number(localStorage.getItem(key));
    if (Number.isFinite(value) && value >= MIN_SIDE_WIDTH_PX) {
      return value;
    }
  } catch {
    // ignore storage errors
  }
  return null;
};

const issuingButtonCenter = (width: number) => Math.round(width * ISSUING_BUTTON_CENTER);
const storedLeftWidth = readStoredLeftWidth(LEFT_WIDTH_STORAGE_KEY);
const plainWidthPx = ref(storedLeftWidth ?? issuingButtonCenter(window.innerWidth));
const tableWidthPx = ref<number | null>(readStoredLeftWidth(TABLE_LEFT_WIDTH_STORAGE_KEY));
const leftWidthPx = ref(plainWidthPx.value);
const query = ref('');
const byNumber = ref(true);
const byCase = ref(false);
const byText = ref(false);
const LIST_FILTER_STORAGE_KEY = 'document-registrar-list-filter';
const LIST_ROLE_FILTERS = ['created', 'doing', 'wrote', 'onControl', 'toReview', 'recent', 'onSignature'];

const readStoredListFilter = (): {
  role: string | null; hidden: boolean; myCases: boolean; topics: boolean; tests: boolean;
} => {
  try {
    const raw = localStorage.getItem(LIST_FILTER_STORAGE_KEY);
    if (!raw) {
      return {
        role: 'recent', hidden: false, myCases: false, topics: false, tests: false,
      };
    }
    const data = JSON.parse(raw);
    const role = LIST_ROLE_FILTERS.includes(data?.role) ? data.role : null;
    const topics = Boolean(data?.topics) && !role;
    const tests = Boolean(data?.tests) && !role && !topics;
    const hidden = Boolean(data?.hidden) && !role && !topics && !tests;
    const myCases = Boolean(data?.myCases) && !hidden && !role && !topics && !tests;
    return {
      role, hidden, myCases, topics, tests,
    };
  } catch {
    return {
      role: 'recent', hidden: false, myCases: false, topics: false, tests: false,
    };
  }
};

const openedWithResetFilters = () => {
  try {
    return new URLSearchParams(window.location.search).get('resetFilters') === '1';
  } catch {
    return false;
  }
};

const storedListFilter = openedWithResetFilters()
  ? {
    role: null, hidden: false, myCases: false, topics: false, tests: false,
  }
  : readStoredListFilter();
const roleFilter = ref<string | null>(storedListFilter.role);
const showHidden = ref(storedListFilter.hidden);
const showMyCases = ref(storedListFilter.myCases);
const showTopics = ref(storedListFilter.topics);
const showTests = ref(storedListFilter.tests);
const tableMode = computed(() => {
  if (showTests.value || showTopics.value || showMyCases.value) {
    return false;
  }
  const title = (selectedJournal.value?.title || '').trim().toLocaleLowerCase();
  return title === 'исходящие' || title === 'внутренние' || title === 'внутренние входящие';
});
const internalJournal = computed(() => (
  (selectedJournal.value?.title || '').trim().toLocaleLowerCase() === 'внутренние'
));
const pendingReviewCount = ref(0);
const pendingSignatureCount = ref(0);
const documents = ref<{
  id: number;
  title?: string;
  confirmed?: boolean;
  number?: string;
  typeTitle?: string;
  department?: string;
  signedBy?: string;
  confirmedBy?: string;
  registrationNumber?: string;
  fio?: string;
  caseId?: number;
}[]>([]);
const listQuery = ref('');
const blocks = ref<{ id: number; title: string; creator: string; createdAt: string }[]>([]);
const tests = ref<{ id: number; title: string; shortTitle?: string }[]>([]);
const selectedDocument = ref<number | null>(null);
const selectedCase = ref<number | null>(null);

const clearSelection = () => {
  selectedDocument.value = null;
  selectedCase.value = null;
};

const keepSelection = () => {
  if (showMyCases.value && selectedCase.value) {
    const row = documents.value.find(item => item.caseId === selectedCase.value);
    if (!row) {
      clearSelection();
      return;
    }
    selectedDocument.value = row.id;
    return;
  }
  if (selectedDocument.value && !documents.value.some(row => row.id === selectedDocument.value)) {
    clearSelection();
  }
};
const selectedBlock = ref<number | null>(null);
const selectedTest = ref<number | null>(null);
const blockModalOpen = ref(false);
const blockTitleDraft = ref('');
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
  selectedJournal.value
  || roleFilter.value
  || showHidden.value
  || showMyCases.value
  || showTopics.value
  || showTests.value,
));
if (!canViewHidden.value) {
  showHidden.value = false;
}

const toggleRole = (id: string) => {
  listQuery.value = '';
  const next = roleFilter.value === id ? null : id;
  showMyCases.value = false;
  showTopics.value = false;
  showTests.value = false;
  if (next) {
    showHidden.value = false;
  }
  roleFilter.value = next;
};

const applyListCounts = (data?: {
  pendingReviewCount?: number;
  pendingSignatureCount?: number;
  journalBadges?: Record<string, number>;
} | null) => {
  pendingReviewCount.value = Number(data?.pendingReviewCount) || 0;
  pendingSignatureCount.value = Number(data?.pendingSignatureCount) || 0;
  const next: Record<string, number> = {};
  Object.entries(data?.journalBadges || {}).forEach(([key, value]) => {
    next[String(key)] = Number(value) || 0;
  });
  journalBadges.value = next;
};

const loadPendingCount = async () => {
  applyListCounts(await api('document-manager/documents/list', { countOnly: true, registrar: true }));
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
      journalId: selectedJournal.value?.id || null,
      registrar: true,
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
  const journalId = selectedJournal.value?.id || null;
  if (showTests.value) {
    clearSelection();
    selectedBlock.value = null;
    blocks.value = [];
    await loadPendingCount();
    await store.dispatch(actions.INC_LOADING);
    try {
      const { result } = await api('document-manager/tests/list');
      if (loadId !== documentsLoadId) {
        return;
      }
      tests.value = result || [];
      const stillThere = tests.value.some(row => row.id === selectedTest.value);
      if (selectedTest.value && !stillThere) {
        selectedTest.value = null;
      }
    } finally {
      await store.dispatch(actions.DEC_LOADING);
    }
    return;
  }
  tests.value = [];
  selectedTest.value = null;
  if (showTopics.value) {
    clearSelection();
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
  if (!hasListFilter && !showHidden.value && !showMyCases.value) {
    if (!journalId) {
      await loadPendingCount();
      return;
    }
    await store.dispatch(actions.INC_LOADING);
    try {
      const data = await api('document-manager/documents/list', { journalId, registrar: true });
      if (loadId !== documentsLoadId) {
        return;
      }
      documents.value = data?.result || [];
      applyListCounts(data);
      keepSelection();
    } finally {
      await store.dispatch(actions.DEC_LOADING);
    }
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    if (roleFilter.value === 'recent') {
      await loadRecent(false);
      await loadPendingCount();
      return;
    }
    const data = await api('document-manager/documents/list', {
      filter: roleFilter.value === 'created' || roleFilter.value === 'toReview' ? roleFilter.value : null,
      hidden: Boolean(canViewHidden.value && showHidden.value),
      myCases: Boolean(showMyCases.value),
      journalId,
      registrar: true,
    });
    if (loadId !== documentsLoadId) {
      return;
    }
    documents.value = data?.result || [];
    applyListCounts(data);
    keepSelection();
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const toggleHidden = () => {
  if (!canViewHidden.value) {
    return;
  }
  const next = !showHidden.value;
  listQuery.value = '';
  showHidden.value = next;
  clearSelection();
  if (next) {
    showMyCases.value = false;
    showTopics.value = false;
    showTests.value = false;
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
  clearSelection();
  if (next) {
    showHidden.value = false;
    showTopics.value = false;
    showTests.value = false;
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
  clearSelection();
  if (next) {
    showHidden.value = false;
    showMyCases.value = false;
    showTests.value = false;
    if (roleFilter.value) {
      roleFilter.value = null;
      return;
    }
  }
  loadDocuments();
};

const toggleTests = () => {
  listQuery.value = '';
  const next = !showTests.value;
  showTests.value = next;
  clearSelection();
  if (next) {
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
      journalId: selectedJournal.value?.id || null,
      registrar: true,
    });
    if (listSearch && loadId !== documentsLoadId) {
      return;
    }
    if (result?.ok) {
      if (listSearch) {
        const rows = result.result || [];
        showTopics.value = false;
        showTests.value = false;
        selectedBlock.value = null;
        selectedTest.value = null;
        documents.value = rows;
        recentPage.value = 1;
        recentHasMore.value = false;
        if (tableMode.value) {
          clearSelection();
        } else {
          const first = rows[0];
          selectedDocument.value = first?.id || null;
          selectedCase.value = showMyCases.value && first?.caseId ? first.caseId : null;
        }
      }
      root.$emit('msg', 'ok', result.message || 'Найдено');
    } else {
      if (listSearch) {
        documents.value = [];
        recentHasMore.value = false;
        clearSelection();
      }
      root.$emit('msg', 'error', result?.message || 'Документ не найден');
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const selectListRow = (row: { id: number; caseId?: number }) => {
  selectedDocument.value = row.id;
  selectedCase.value = showMyCases.value && row.caseId ? row.caseId : null;
};

const isRowSelected = (row: { id: number; caseId?: number }) => (
  showMyCases.value && row.caseId
    ? selectedCase.value === row.caseId
    : selectedDocument.value === row.id
);

const viewerCaseId = computed(() => (
  showMyCases.value && selectedCase.value ? selectedCase.value : null
));

const viewerDocumentId = computed(() => (
  viewerCaseId.value ? null : selectedDocument.value
));

const openRegistrationNumber = computed(() => {
  const id = viewerDocumentId.value;
  if (!id) {
    return '';
  }
  const row = documents.value.find(item => item.id === id);
  return row?.registrationNumber || '';
});

const registerRow = async (row: { id: number; registrationNumber?: string }) => {
  if (!row.id || row.registrationNumber) {
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/documents/register', { id: row.id });
    if (result?.ok) {
      const current = documents.value.find(item => item.id === row.id);
      if (current) {
        current.registrationNumber = result.number || '';
      }
      root.$emit('msg', 'ok', 'Зарегистрировано');
    } else {
      root.$emit('msg', 'error', result?.message || 'Ошибка регистрации');
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

type ResolutionFormRow = {
  key: number;
  id: number;
  note: string;
  addressee: string;
};

const resolutionDocumentId = ref<number | null>(null);
const resolutionNumber = ref('');
const resolutionRows = ref<ResolutionFormRow[]>([]);
const resolutionBody = ref<HTMLElement | null>(null);
let resolutionKey = 0;

const growNote = (field: HTMLTextAreaElement) => {
  const area = field;
  area.style.height = '34px';
  const border = area.offsetHeight - area.clientHeight;
  area.style.height = `${area.scrollHeight + border}px`;
};

const fitResolutionNote = (event: Event) => {
  const field = event.target;
  if (field instanceof HTMLTextAreaElement) {
    growNote(field);
  }
};

const fitResolutionNotes = () => {
  nextTick(() => {
    resolutionBody.value?.querySelectorAll('textarea').forEach(node => {
      growNote(node as HTMLTextAreaElement);
    });
  });
};

const nextResolutionKey = () => {
  resolutionKey += 1;
  return resolutionKey;
};

const resolutionAddressee = (id?: number, fio?: string, department?: string) => {
  if (!id) {
    return '[]';
  }
  return JSON.stringify([{ id, fio: fio || '', department: department || '' }]);
};

const oneAddressee = (raw: string) => {
  try {
    const parsed = JSON.parse(raw || '[]');
    if (!Array.isArray(parsed) || !parsed.length) {
      return '[]';
    }
    const first = parsed[0];
    const id = Number(first?.id);
    if (!id) {
      return '[]';
    }
    return JSON.stringify([{
      id,
      fio: first.fio || '',
      department: first.department || '',
    }]);
  } catch {
    return '[]';
  }
};

const employeeIdFrom = (raw: string) => {
  try {
    const parsed = JSON.parse(raw || '[]');
    const id = Number(Array.isArray(parsed) ? parsed[0]?.id : 0);
    return id > 0 ? id : 0;
  } catch {
    return 0;
  }
};

const blankResolutionRow = (): ResolutionFormRow => ({
  key: nextResolutionKey(),
  id: 0,
  note: '',
  addressee: '[]',
});

const closeResolution = () => {
  resolutionDocumentId.value = null;
  resolutionNumber.value = '';
  resolutionRows.value = [];
};

const addResolutionRow = () => {
  resolutionRows.value.push(blankResolutionRow());
};

const removeResolutionRow = (index: number) => {
  resolutionRows.value.splice(index, 1);
};

const onResolutionAddressee = (key: number, value: string) => {
  const current = resolutionRows.value.find(item => item.key === key);
  if (current) {
    current.addressee = oneAddressee(value);
  }
};

const resolutionRowsFrom = (rows: {
  id: number;
  note?: string;
  employeeId?: number;
  employeeFio?: string;
  employeeDepartment?: string;
}[]) => (rows || []).map(item => ({
  key: nextResolutionKey(),
  id: item.id,
  note: item.note || '',
  addressee: resolutionAddressee(item.employeeId, item.employeeFio, item.employeeDepartment),
}));

const openResolution = async (row: { id: number; registrationNumber?: string }) => {
  resolutionDocumentId.value = row.id;
  resolutionNumber.value = row.registrationNumber || '';
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/documents/resolutions', { id: row.id });
    if (!result?.ok) {
      closeResolution();
      root.$emit('msg', 'error', result?.message || 'Резолюции не найдены');
      return;
    }
    resolutionRows.value = resolutionRowsFrom(result.rows || []);
    if (!resolutionRows.value.length) {
      addResolutionRow();
    }
    fitResolutionNotes();
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const saveResolutions = async () => {
  if (!resolutionDocumentId.value) {
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/documents/resolutions/save', {
      id: resolutionDocumentId.value,
      rows: resolutionRows.value.map(item => ({
        id: item.id,
        note: item.note,
        employeeId: employeeIdFrom(item.addressee),
      })),
    });
    if (!result?.ok) {
      root.$emit('msg', 'error', result?.message || 'Ошибка сохранения');
      return;
    }
    resolutionRows.value = resolutionRowsFrom(result.rows || []);
    fitResolutionNotes();
    root.$emit('msg', 'ok', 'Сохранено');
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
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
  return documents.value.filter(row => {
    const haystack = [
      row.title, row.number, row.typeTitle, row.department, row.signedBy, row.confirmedBy, row.registrationNumber,
    ].join(' ');
    return folded(haystack).includes(filterText);
  });
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

const visibleTests = computed(() => {
  const filterText = folded(listQuery.value.trim());
  if (!filterText) {
    return tests.value;
  }
  return tests.value.filter(row => folded(row.shortTitle || row.title).includes(filterText)
    || folded(row.title).includes(filterText));
});

const selectTest = (id: number) => {
  selectedTest.value = id;
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

const runCreate = async (payload: CreatePayload) => {
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/documents/create', {
      typeId: payload.typeId,
      caseId: payload.caseId,
      topic: payload.topic || '',
      periodParams: payload.periodParams || null,
    });
    if (result?.ok) {
      if (result.emptyCase) {
        root.$emit('msg', 'ok', 'Дело создано');
      } else {
        root.$emit('msg', 'ok', 'Документ создан');
      }
      clearSelection();
    } else {
      root.$emit('msg', 'error', result?.message || 'Ошибка создания');
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const monitoringParamsOf = (pk: number) => {
  const row = overrideResearches.value.find(item => Number(item.pk) === Number(pk));
  const value = Number(row?.monitoringDirectionParams);
  return value > 0 ? value : 0;
};

const openMonitoringModal = (payload: CreatePayload) => {
  pendingCreate.value = payload;
  monitoringDirectionParamsId.value = payload.monitoringDirectionParams || 0;
  monitoringModalOpen.value = true;
};

const closeMonitoringModal = () => {
  monitoringModalOpen.value = false;
  pendingCreate.value = null;
};

const confirmMonitoringPeriod = async (periodParams: Record<string, unknown>) => {
  if (!pendingCreate.value) {
    return;
  }
  const payload = { ...pendingCreate.value, periodParams };
  monitoringModalOpen.value = false;
  pendingCreate.value = null;
  await runCreate(payload);
};

const createDocument = async () => {
  if (!canCreate.value) {
    return;
  }
  const pk = selectedResearches.value[0];
  const resolved: CreatePayload = {
    ...resolveCreate(pk),
    monitoringDirectionParams: monitoringParamsOf(pk),
  };
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
  if ((resolved.monitoringDirectionParams || 0) > 0) {
    openMonitoringModal(resolved);
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
  caseTopicModalOpen.value = false;
  caseTopicDraft.value = '';
  if (payload.typeId && (payload.monitoringDirectionParams || 0) > 0) {
    openMonitoringModal(payload);
    return;
  }
  pendingCreate.value = null;
  await runCreate(payload);
};

const applyJournalWidth = () => {
  if (tableMode.value) {
    const width = splitEl.value?.clientWidth || window.innerWidth;
    leftWidthPx.value = tableWidthPx.value ?? Math.max(MIN_SIDE_WIDTH_PX, Math.round(width * (2 / 3)));
    return;
  }
  leftWidthPx.value = plainWidthPx.value;
};

const onLeftWidthChange = (value: number) => {
  leftWidthPx.value = value;
  const key = tableMode.value ? TABLE_LEFT_WIDTH_STORAGE_KEY : LEFT_WIDTH_STORAGE_KEY;
  if (tableMode.value) {
    tableWidthPx.value = value;
  } else {
    plainWidthPx.value = value;
  }
  try {
    localStorage.setItem(key, String(value));
  } catch {
    // ignore storage errors
  }
};

const loadJournals = async () => {
  const data = await api('document-manager/journals/list');
  journals.value = data?.result || [];
  const current = journals.value.find(row => row.title === direction.value);
  if (!current && journals.value.length) {
    direction.value = journals.value[0].title;
    return;
  }
  await loadDocuments();
};

onMounted(async () => {
  if (storedLeftWidth == null) {
    await nextTick();
    const width = splitEl.value?.clientWidth || window.innerWidth;
    plainWidthPx.value = issuingButtonCenter(width);
    leftWidthPx.value = plainWidthPx.value;
  }
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
  await loadJournals();
});

watch(roleFilter, () => {
  loadDocuments();
});

watch(internalJournal, (value) => {
  if (!value) {
    closeResolution();
  }
});

watch(direction, async () => {
  if (tableMode.value) {
    clearSelection();
  }
  await nextTick();
  applyJournalWidth();
  loadDocuments();
});

watch(tableMode, async () => {
  await nextTick();
  applyJournalWidth();
});

watch([roleFilter, showHidden, showMyCases, showTopics, showTests], () => {
  try {
    localStorage.setItem(LIST_FILTER_STORAGE_KEY, JSON.stringify({
      role: roleFilter.value,
      hidden: showHidden.value,
      myCases: showMyCases.value,
      topics: showTopics.value,
      tests: showTests.value,
    }));
  } catch {
    // ignore storage errors
  }
});
</script>

<style scoped lang="scss">
.root {
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  height: calc(100% - 4px);
  margin-bottom: 4px;
  min-height: 0;
  background-color: #f8f7f7;
}

.top-panel {
  display: flex;
  align-items: stretch;
  flex: 0 0 34px;
  width: 100%;
  height: 34px;
  min-height: 34px;
  overflow: hidden;
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
  flex: 1 1 120px;
  min-width: 80px;
  width: 0;
  height: 34px;
  border-radius: 0;
  padding-left: 10px;
}

.top-panel .btn {
  height: 34px;
  border-radius: 0;
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

.filter-check,
.mode-check {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 0 0 auto;
  width: max-content;
  height: 34px;
  margin: 0;
  padding: 0 8px;
  font-size: 12px;
  font-weight: normal;
  cursor: pointer;
  white-space: nowrap;

  input {
    flex: 0 0 auto;
    margin: 0;
    pointer-events: none;
  }
}

.direction-row {
  flex: 0 0 34px;
  width: 100%;
  height: 34px;
}

.split {
  position: relative;
  flex: 1 1 auto;
  width: 100%;
  min-height: 0;
}

.doc-list,
.split-right {
  height: 100%;
  min-height: 0;
  background-color: #fff;
}

.split-right {
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.doc-pane {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  background-color: #fff;
}

.doc-pane .doc-list {
  flex: 1 1 auto;
  height: auto;
}

.list-filter {
  flex: 0 0 34px;
  width: 100%;
  height: 34px;
  border-color: #b1b1b1;
  border-right: 0;
  border-bottom: 0;
  border-radius: 0;
}

.doc-list {
  overflow-y: auto;
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

.incoming-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  line-height: 16px;
  color: #434a54;

  th,
  td {
    padding: 6px 8px;
    border-bottom: 1px solid #b1b1b1;
    text-align: left;
    vertical-align: top;
  }

  th {
    position: sticky;
    top: 0;
    background: #f5f5f5;
    font-weight: 600;
  }

  tbody tr {
    cursor: default;
  }

  tbody tr:hover {
    background: #f3f3f3;
    color: #434a54;
  }

  tbody tr.incoming-table__active,
  tbody tr.incoming-table__active:hover {
    background: #049372;
    color: #fff;
  }

  &__eye {
    width: 34px;
    text-align: center;
  }

  &__reg {
    width: 1%;
    text-align: center;
    white-space: nowrap;
  }
}

.doc-reg {
  box-sizing: border-box;
  min-width: 22px;
  width: 22px;
  height: 22px;
  margin: 0;
  padding: 0;
  border: 1px solid #aab2bd;
  border-radius: 0;
  background: #aab2bd;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  line-height: 20px;

  &:hover {
    background: #434a54;
    border-color: #434a54;
    color: #fff;
  }
}

.doc-resolution {
  box-sizing: border-box;
  min-width: 22px;
  width: 22px;
  height: 22px;
  margin-left: 6px;
  padding: 0;
  border: 1px solid #aab2bd;
  border-radius: 0;
  background: #aab2bd;
  color: #fff;
  font-size: 12px;
  line-height: 20px;

  &:hover {
    background: #434a54;
    border-color: #434a54;
    color: #fff;
  }
}

.resolution-pane {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 4;
  display: flex;
  flex-direction: column;
  background: #f8f7f7;
}

.resolution-pane__title {
  flex: 0 0 34px;
  display: flex;
  align-items: center;
  padding: 0 10px;
  background: #aab2bd;
  color: #fff;
  font-size: 14px;
}

.resolution-pane__body {
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
  padding: 8px;
}

.resolution-pair {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
}

.resolution-note {
  flex: 1 1 40%;
  min-width: 0;
  min-height: 34px;
  height: 34px;
  padding-top: 6px;
  padding-bottom: 6px;
  overflow: hidden;
  line-height: 20px;
  resize: none;
  border-radius: 0;
}

.resolution-pair :deep(.addressee-field) {
  flex: 1 1 40%;
  min-width: 0;
}

.resolution-remove {
  flex: 0 0 34px;
  width: 34px;
  height: 34px;
  padding: 0;
  border: 1px solid #aab2bd;
  border-radius: 0;
  background: #aab2bd;
  color: #fff;
  font-size: 18px;
  line-height: 32px;

  &:hover {
    background: #434a54;
    border-color: #434a54;
    color: #fff;
  }
}

.resolution-add {
  height: 34px;
  border-radius: 0;
}

.resolution-pane__footer {
  flex: 0 0 34px;
  display: flex;
  justify-content: flex-end;
  background: #f4f4f4;
  border-top: 1px solid #b1b1b1;

  .btn {
    height: 34px;
    border-radius: 0;
  }
}

.doc-eye {
  width: 26px;
  height: 22px;
  padding: 0;
  border: none;
  border-radius: 0;
  background: transparent;
  color: inherit;
  line-height: 22px;
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
