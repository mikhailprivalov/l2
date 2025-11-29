<template>
  <div class="request-history-root">
    <div class="request-history-sidebar">
      <div class="sidebar-top">
        <div class="input-group">
          <span class="input-group-btn relative">
            <button
              class="btn btn-blue-nb btn-ell dropdown-toggle bt1"
              type="button"
              @click="showModes = !showModes"
            >
              <span class="caret" />
              {{ SEARCH_MODES_MAP.get(searchMode) }}
              <i
                v-if="isLoading"
                class="fa fa-spinner"
              />
            </button>
            <ul
              v-show="showModes"
              class="dropdown-menu min-width-160 margin-top-1"
            >
              <li
                v-for="row in availableSearchModes"
                :key="row.id"
              >
                <a
                  href="#"
                  :class="{ 'mode-active': searchMode === row.id }"
                  @click.prevent="selectMode(row.id)"
                >{{ row.title }}</a>
              </li>
            </ul>
          </span>
          <div>
            <DateRange v-model="dateRange" />
          </div>
        </div>
        <label
          v-if="searchMode === 'card' || searchMode === 'search'"
          class="only-mine-filter"
        >
          <input
            v-model="onlyMine"
            type="checkbox"
          >
          Только созданные мной
        </label>
      </div>
      <div
        class="directions"
        :class="{ 'with-filter': searchMode === 'card' || searchMode === 'search' }"
      >
        <div
          ref="listContainer"
          class="inner"
          :class="{ 'with-bottom-header': isSelectionMode }"
          @scroll="onListScroll"
        >
          <div
            v-if="showNewItemsBanner"
            class="new-items-banner"
          >
            <span>Есть новые заявки</span>
            <button
              class="new-items-button"
              type="button"
              @click="showPendingItems"
            >
              Показать
            </button>
          </div>
          <div
            v-for="item in requests"
            :key="item.id"
            class="direction"
            :class="{
              'selectable': isSelectionMode && !item.hasImage,
              'selection-disabled': isSelectionMode && item.hasImage,
              'highlighted': isHighlighted(item),
            }"
            @click="onRequestClick(item)"
            @mouseenter="onRequestMouseEnter(item)"
            @mouseleave="onRequestMouseLeave"
          >
            <div>
              <span class="request-id">{{ item.id }}</span> {{ item.patient }}
            </div>
            <div
              v-if="item.researchTitle"
              class="research-title"
            >
              {{ item.researchTitle }}
              <span
                v-if="item.isCito"
                class="cito-badge"
              >CITO</span>
              <button
                v-if="item.hasResult"
                class="print-result-btn"
                title="Печать результата"
                @click.stop="printResult(item.id)"
              >
                <i class="fa fa-print" /> Результат
              </button>
            </div>
            <div class="research-row">
              <div class="row">
                <div class="col-xs-7">
                  {{ formatDateTime(item.datetime) }}
                </div>
                <div class="col-xs-5 text-right">
                  <span
                    class="image-status"
                    :class="item.hasImage ? 'image-status--yes' : 'image-status--no'"
                  >
                    {{ item.hasImage ? 'Снимок есть' : 'Без снимка' }}
                  </span>
                </div>
              </div>
            </div>
            <div
              v-if="item.creator"
              class="creator-row"
            >
              <i class="fa fa-user-md" />
              {{ item.creator }}
            </div>
            <div
              v-if="item.files && item.files.length > 0"
              class="files-section"
              :class="{ 'selection-mode-disabled': isSelectionMode }"
            >
              <div class="files-list">
                <a
                  v-for="file in item.files"
                  :key="file.id"
                  :href="isSelectionMode ? '#' : file.url"
                  target="_blank"
                  class="file-link"
                  @click.stop="onFileClick($event, item)"
                >
                  <i class="fa fa-paperclip" />
                  {{ file.name }}
                </a>
              </div>
            </div>
          </div>
          <div
            v-if="requests.length === 0 && !isLoading"
            class="text-center margin-5"
          >
            Нет данных
          </div>
          <div
            ref="loadMoreTrigger"
            class="load-more-trigger"
          >
            <div
              v-if="isLoadingMore"
              class="loading-more"
            >
              <i class="fa fa-spinner fa-spin" />
              Загрузка...
            </div>
          </div>
        </div>
        <div
          v-if="isSelectionMode"
          class="selection-mode-footer"
        >
          <div class="selection-image-info">
            <div class="image-info-title">
              Привязка изображения:
            </div>
            <div class="image-info-details">
              <span class="image-patient">{{ currentImageForLink?.patient || 'Пациент неизвестен' }}</span>
              <span class="image-datetime">{{ currentImageForLink?.datetime || '' }}</span>
            </div>
          </div>
          <button
            class="btn btn-secondary btn-sm cancel-selection"
            @click="exitSelectionMode"
          >
            <i class="fa fa-times" />
            Отмена
          </button>
        </div>
      </div>
    </div>
    <Modal
      v-if="showRequestDetailsModal"
      show-footer="true"
      white-bg="true"
      min-width="90%"
      height="80%"
      margin-left-right="20px"
      margin-top="40px"
      @close="hideRequestDetailsModal"
    >
      <span slot="header">Детали заявки</span>
      <div
        slot="body"
        class="request-details-body"
      >
        <div
          v-if="isLoadingDetails"
          class="loading-details"
        >
          <div class="spinner-small" />
          <span>Загрузка...</span>
        </div>
        <div
          v-else-if="requestDetails"
          class="request-details-fullscreen"
        >
          <div class="request-details-content">
            <div class="left-column">
              <div class="detail-section">
                <h4 class="detail-section-title">
                  Основная информация
                </h4>
                <div class="detail-row">
                  <span class="detail-label">Номер заявки:</span>
                  <span class="detail-value">{{ requestDetails.id }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Пациент:</span>
                  <span class="detail-value">{{ requestDetails.patient }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Карта пациента:</span>
                  <span class="detail-value">{{ requestDetails.cardId }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Дата создания:</span>
                  <span class="detail-value">{{ requestDetails.datetime }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Создал:</span>
                  <span class="detail-value">{{ requestDetails.doctor }}</span>
                </div>
              </div>

              <div class="detail-section">
                <h4 class="detail-section-title">
                  Исследования
                </h4>
                <div
                  v-if="requestDetails.researches && requestDetails.researches.length > 0"
                  class="researches-list"
                >
                  <div
                    v-for="research in requestDetails.researches"
                    :key="research.id"
                    class="research-item"
                  >
                    <div class="research-title-full">
                      {{ research.title }}
                    </div>
                  </div>
                </div>
                <div
                  v-else
                  class="no-researches"
                >
                  Исследования не указаны
                </div>
              </div>

              <div class="detail-section">
                <h4 class="detail-section-title">
                  Привязанные файлы
                </h4>
                <div
                  v-if="requestDetails.files && requestDetails.files.length > 0"
                  class="files-list-modal"
                >
                  <a
                    v-for="file in requestDetails.files"
                    :key="file.id"
                    :href="file.url"
                    target="_blank"
                    class="file-link-modal"
                  >
                    <i class="fa fa-paperclip" />
                    {{ file.name }}
                  </a>
                </div>
                <div
                  v-else
                  class="no-files"
                >
                  Файлы не прикреплены
                </div>
              </div>
            </div>

            <div class="right-column">
              <div class="detail-section">
                <h4 class="detail-section-title">
                  Параметры исследования
                </h4>
                <div class="detail-row">
                  <span class="detail-label">Дата исследования:</span>
                  <span
                    class="detail-value"
                    :class="{ 'empty-value': !requestDetails.factResearchDate }"
                  >{{ requestDetails.factResearchDate || '(не указана)' }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Доза:</span>
                  <span
                    class="detail-value"
                    :class="{ 'empty-value': !requestDetails.dose }"
                  >{{ requestDetails.dose || '(не указана)' }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Объем контраста:</span>
                  <span
                    class="detail-value"
                    :class="{ 'empty-value': !requestDetails.contrastAmount }"
                  >{{ requestDetails.contrastAmount || '(не указан)' }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Срочность:</span>
                  <span class="detail-value">{{ requestDetails.isCito ? 'Cito' : 'Обычное' }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Привязанное изображение:</span>
                  <span class="detail-value">{{ requestDetails.hasImage ? 'Есть' : 'Отсутствует' }}</span>
                </div>
              </div>

              <div class="detail-section">
                <h4 class="detail-section-title">
                  Клинические данные
                </h4>
                <div class="detail-textarea-row">
                  <span class="detail-label">Краткий анамнез:</span>
                  <div
                    class="detail-textarea-value"
                    :class="{ 'empty-value': !requestDetails.anamnesis }"
                    v-text="requestDetails.anamnesis || '(не указан)'"
                  />
                </div>
                <div class="detail-textarea-row">
                  <span class="detail-label">Комментарий:</span>
                  <div
                    class="detail-textarea-value"
                    :class="{ 'empty-value': !requestDetails.comment }"
                    v-text="requestDetails.comment || '(не указан)'"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-8" />
          <div class="col-xs-4">
            <button
              class="btn btn-primary-nb btn-blue-nb"
              type="button"
              @click="hideRequestDetailsModal"
            >
              Закрыть
            </button>
          </div>
        </div>
      </div>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import {
  computed, onMounted, onUnmounted, ref, watch,
} from 'vue';
import moment from 'moment';

import api from '@/api';
import DateRange from '@/ui-cards/DateRange.vue';
import useNotify from '@/hooks/useNotify';
import usePrint from '@/hooks/usePrint';
import Modal from '@/ui-cards/Modal.vue';

const props = defineProps<{
  cardId?: number | null;
  highlightedRequestId?: number | string | null;
}>();
const notify = useNotify();
const { printResults } = usePrint();

const printResult = (id: number) => {
  printResults([id]);
};

const emit = defineEmits(['request-selected', 'cancel-selection', 'request-hover']);

const SEARCH_MODES = [
  { id: 'all', title: 'Созданные' },
  { id: 'card', title: 'Пациент' },
  { id: 'search', title: 'Организация' },
];

const SEARCH_MODES_MAP = new Map(SEARCH_MODES.map((m) => [m.id, m.title]));

const searchMode = ref(SEARCH_MODES[0].id);
const availableSearchModes = computed(() => SEARCH_MODES.filter((mode) => mode.id !== searchMode.value));
const dateRange = ref([moment().format('DD.MM.YYYY'), moment().format('DD.MM.YYYY')]);
const isMultipleDays = computed(() => dateRange.value[0] !== dateRange.value[1]);
const showModes = ref(false);
const isLoading = ref(false);
const onlyMine = ref(false);
const isSelectionMode = ref(false);
const currentImageForLink = ref<any>(null);
const showRequestDetailsModal = ref(false);
const requestDetails = ref<any>(null);
const isLoadingDetails = ref(false);

const selectMode = (id: string) => {
  searchMode.value = id;
  showModes.value = false;
};

const formatDateTime = (datetime: string) => {
  if (isMultipleDays.value) {
    return datetime;
  }
  return datetime.split(' ')[1] || datetime;
};

type File = {
  id: number;
  name: string;
  url: string;
};

type Request = {
  id: number;
  patient: string;
  datetime: string;
  hasImage: boolean;
  hasResult: boolean;
  cardId: number;
  files: File[];
  researchTitle: string;
  isCito: boolean;
  creator?: string;
};

let autoRefreshTimer: ReturnType<typeof setTimeout> | null = null;
const PAGE_SIZE = 10;

const requests = ref<Request[]>([]);
const hasMore = ref(false);
const currentOffset = ref(0);
const isLoadingMore = ref(false);
const isRefreshing = ref(false);
const listContainer = ref<HTMLElement | null>(null);
const isAtTop = ref(true);
const pendingNewItems = ref(false);

const actualCardId = computed(() => {
  if (searchMode.value === 'card' && props.cardId && props.cardId > 0) {
    return props.cardId;
  }
  return null;
});

const existingIds = computed(() => new Set(requests.value.map(r => r.id)));

const getRequests = async () => {
  currentOffset.value = 0;
  isLoading.value = true;
  try {
    const params: Record<string, any> = {
      searchType: searchMode.value,
      cardId: actualCardId.value,
      offset: 0,
      limit: PAGE_SIZE,
      onlyMine: onlyMine.value,
    };
    [params.dateFrom, params.dateTo] = dateRange.value;
    const { rows, hasMore: more } = await api('requests/list', params);
    requests.value = rows;
    hasMore.value = more;
    currentOffset.value = rows.length;
  } catch (error) {
    notify.error('Ошибка при получении заявок');
  } finally {
    isLoading.value = false;
  }
};

const loadMore = async () => {
  if (!hasMore.value || isLoadingMore.value || isLoading.value || isRefreshing.value) return;
  isLoadingMore.value = true;
  try {
    const params: Record<string, any> = {
      searchType: searchMode.value,
      cardId: actualCardId.value,
      offset: currentOffset.value,
      limit: PAGE_SIZE,
      onlyMine: onlyMine.value,
    };
    [params.dateFrom, params.dateTo] = dateRange.value;
    const { rows, hasMore: more } = await api('requests/list', params);
    const newRows = rows.filter((r: Request) => !existingIds.value.has(r.id));
    requests.value = [...requests.value, ...newRows];
    hasMore.value = more;
    currentOffset.value += rows.length;
  } catch (error) {
    notify.error('Ошибка при загрузке');
  } finally {
    isLoadingMore.value = false;
  }
};

const refreshNewItems = async () => {
  if (isLoading.value || isLoadingMore.value || isRefreshing.value) return;
  isRefreshing.value = true;
  try {
    const params: Record<string, any> = {
      searchType: searchMode.value,
      cardId: actualCardId.value,
      offset: 0,
      limit: PAGE_SIZE,
      onlyMine: onlyMine.value,
    };
    [params.dateFrom, params.dateTo] = dateRange.value;
    const { rows } = await api('requests/list', params);
    const newRows = rows.filter((r: Request) => !existingIds.value.has(r.id));
    if (newRows.length > 0) {
      requests.value = [...newRows, ...requests.value];
      currentOffset.value += newRows.length;
    }
    const existingIdsSet = existingIds.value;
    for (const row of rows) {
      if (existingIdsSet.has(row.id)) {
        const existing = requests.value.find(r => r.id === row.id);
        if (existing) {
          existing.hasImage = row.hasImage;
          existing.hasResult = row.hasResult;
          existing.files = row.files;
        }
      }
    }
  } catch (error) {
    console.error('Auto-refresh error:', error);
  } finally {
    isRefreshing.value = false;
  }
};

watch([searchMode, actualCardId, dateRange, onlyMine], async () => {
  await getRequests();
}, { immediate: true, deep: true });

const showNewItemsBanner = computed(() => pendingNewItems.value && !isAtTop.value);

const onListScroll = () => {
  if (!listContainer.value) return;
  isAtTop.value = listContainer.value.scrollTop <= 50;
  if (isAtTop.value && pendingNewItems.value) {
    pendingNewItems.value = false;
    refreshNewItems();
  }
};

const handleNewRequestCreated = async () => {
  if (listContainer.value) {
    isAtTop.value = listContainer.value.scrollTop <= 50;
  }
  if (isAtTop.value) {
    await refreshNewItems();
  } else {
    pendingNewItems.value = true;
  }
};

const showPendingItems = async () => {
  pendingNewItems.value = false;
  if (listContainer.value) {
    listContainer.value.scrollTo({ top: 0, behavior: 'smooth' });
  }
  await refreshNewItems();
};

const updateRequestImageStatus = (requestId: number | string, hasImage: boolean) => {
  const request = requests.value.find(r => r.id.toString() === requestId.toString());
  if (request) {
    request.hasImage = hasImage;
  }
};

const enterSelectionMode = (image: any) => {
  isSelectionMode.value = true;
  currentImageForLink.value = image;
};

const exitSelectionMode = () => {
  isSelectionMode.value = false;
  currentImageForLink.value = null;
  emit('cancel-selection');
};

const isHighlighted = (item: Request) => (
  props.highlightedRequestId
  && item.id
  && item.id.toString() === props.highlightedRequestId.toString()
);

const showRequestDetails = async (requestId: number) => {
  isLoadingDetails.value = true;
  showRequestDetailsModal.value = true;
  requestDetails.value = null;

  try {
    const response = await api('requests/request-details', { requestId });
    if (response.success) {
      requestDetails.value = response.data;
    } else {
      notify.error(response.message || 'Ошибка при получении деталей заявки');
      showRequestDetailsModal.value = false;
    }
  } catch (error) {
    notify.error('Ошибка при загрузке деталей заявки');
    showRequestDetailsModal.value = false;
  } finally {
    isLoadingDetails.value = false;
  }
};

const hideRequestDetailsModal = () => {
  showRequestDetailsModal.value = false;
  requestDetails.value = null;
};

const onRequestClick = (request: Request) => {
  if (isSelectionMode.value && !request.hasImage) {
    emit('request-selected', request);
  } else if (!isSelectionMode.value) {
    showRequestDetails(request.id);
  }
};

const onFileClick = (event: Event, item: Request) => {
  if (isSelectionMode.value) {
    event.preventDefault();
    if (!item.hasImage) {
      emit('request-selected', item);
    }
  }
};

const onRequestMouseEnter = (item: Request) => {
  emit('request-hover', item);
};

const onRequestMouseLeave = () => {
  emit('request-hover', null);
};

const refreshRequests = async () => {
  await getRequests();
};

const startAutoRefresh = () => {
  if (autoRefreshTimer) {
    clearTimeout(autoRefreshTimer);
  }
  autoRefreshTimer = setTimeout(async () => {
    try {
      const today = moment().format('DD.MM.YYYY');
      const includestoday = dateRange.value[1] === today;
      const canRefresh = !isSelectionMode.value && !isLoading.value && includestoday;
      if (canRefresh) {
        await refreshNewItems();
      }
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error(error);
    }
    startAutoRefresh();
  }, 10000);
};

const stopAutoRefresh = () => {
  if (autoRefreshTimer) {
    clearTimeout(autoRefreshTimer);
    autoRefreshTimer = null;
  }
};

const loadMoreTrigger = ref<HTMLElement | null>(null);
let observer: IntersectionObserver | null = null;

watch(loadMoreTrigger, (el) => {
  if (observer && el) {
    observer.observe(el);
  }
});

onMounted(() => {
  startAutoRefresh();
  observer = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting) {
        loadMore();
      }
    },
    { threshold: 0.1 },
  );
  if (loadMoreTrigger.value) {
    observer.observe(loadMoreTrigger.value);
  }
});

onUnmounted(() => {
  stopAutoRefresh();
  if (observer) {
    observer.disconnect();
  }
});

defineExpose({
  updateRequestImageStatus,
  enterSelectionMode,
  exitSelectionMode,
  currentImageForLink,
  refreshRequests,
  handleNewRequestCreated,
});
</script>

<style scoped lang="scss">
.request-history-root {
  display: flex;
  flex-direction: row;
  height: 100%;
}
.request-history-sidebar {
  width: 100%;
  display: flex;
  flex-direction: column;
}
.sidebar-top {
  background: #eaeaea;

  ::v-deep input {
    border-bottom: 1px solid #b1b1b1;
  }
}
.only-mine-filter {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  font-size: 12px;
  color: #555;
  cursor: pointer;
  background: #f5f5f5;
  border-top: 1px solid #ddd;

  input[type="checkbox"] {
    margin: 0;
    cursor: pointer;
  }

  &:hover {
    background: #eee;
  }
}
.input-group {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.input-group-btn {
  position: relative;
  display: flex;
  align-items: center;
  width: 119px;

  button {
    width: 100%;
    text-align: left;
  }
}
.relative {
  position: relative;
}
.btn {
  border-radius: 0;
  padding: 6px;
  font-size: 12px;
  height: 34px;
  background: #049372;
  color: #fff;
  border: none;
}
.dropdown-toggle {
  cursor: pointer;
}
.dropdown-menu {
  position: absolute;
  left: 0;
  top: 100%;
  z-index: 1000;
  display: block;
  float: left;
  min-width: 160px;
  padding: 5px 0;
  margin: 2px 0 0;
  font-size: 14px;
  text-align: left;
  list-style: none;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-shadow: 0 6px 12px rgba(0,0,0,.175);
}
.min-width-160 {
  min-width: 160px;
}
.margin-top-1 {
  margin-top: 1px;
}
.dropdown-menu li a {
  display: block;
  padding: 3px 20px;
  clear: both;
  font-weight: 400;
  white-space: nowrap;
  text-decoration: none;
}
.mode-active {
  font-weight: bold !important;
}
.sidebar-bottom-top {
  background-color: #eaeaea;
  flex: 0 0 34px;
  display: flex;
  justify-content: flex-start;
  align-items: center;
  padding: 0 8px;
  height: 34px;
}
.directions {
  position: absolute;
  top: 34px;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;

  &.with-filter {
    top: 60px;
  }
}

.directions .inner {
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  padding-bottom: 110px;
  flex: 1;
}

.new-items-banner {
  position: sticky;
  top: 0;
  z-index: 5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  background: #fff3cd;
  border: 1px solid #ffeeba;
  border-radius: 4px;
  padding: 6px 10px;
  margin: 8px;
  color: #856404;
  font-size: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
}

.new-items-button {
  background: transparent;
  border: none;
  color: #856404;
  font-weight: 600;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s;
}

.new-items-button:hover {
  background: rgba(133, 100, 4, 0.1);
}

.direction {
  padding: 5px;
  margin: 5px;
  border-radius: 5px;
  border: 1px solid rgba(0, 0, 0, 0.14);
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);
  cursor: pointer;
}
.research-row {
  margin-top: 3px;
  margin-bottom: 3px;
  padding: 3px;
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);
}
.research-title {
  font-size: 12px;
  color: #666;
  margin-top: 2px;
  margin-bottom: 2px;
}
.print-result-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 600;
  color: #fff;
  background: #049372;
  border: none;
  padding: 2px 6px;
  border-radius: 4px;
  margin-left: 6px;
  cursor: pointer;
  transition: background 0.2s;

  &:hover {
    background: #037a5a;
  }

  i {
    font-size: 10px;
  }
}
.image-status {
  font-size: 12px;
  font-weight: 500;
}
.image-status--yes {
  color: #2ecc40;
}
.image-status--no {
  color: #888;
}
.creator-row {
  font-size: 11px;
  color: #666;
  margin-top: 3px;
  padding: 2px 4px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 3px;

  i {
    margin-right: 4px;
    color: #049372;
  }
}
.load-more-trigger {
  min-height: 20px;
  padding: 5px;
}
.loading-more {
  text-align: center;
  color: #888;
  font-size: 12px;
  padding: 10px;

  i {
    margin-right: 5px;
  }
}
.text-center {
  color: #aaa;
  font-style: italic;
  padding: 10px 0;
}
.margin-5 {
  margin: 5px;
}
.files-section {
  margin-top: 5px;
  padding: 3px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 3px;
}
.files-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.file-link {
  font-size: 11px;
  color: #049372;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 4px;
  border-radius: 2px;
  transition: background-color 0.2s;
}
.file-link:hover {
  background-color: rgba(4, 147, 114, 0.1);
  text-decoration: none;
  color: #037a5a;
}
.file-link i {
  font-size: 10px;
}

.files-section.selection-mode-disabled {
  opacity: 0.5;
}

.files-section.selection-mode-disabled .file-link {
  color: #999;
}

.files-section.selection-mode-disabled .file-link:hover {
  background-color: transparent;
  color: #999;
}

.request-id {
  font-size: 13px;
  color: #049372;
  font-weight: 600;
  background: #f0f9f7;
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
}

.direction.selectable {
  cursor: pointer;
  border-color: #049372;
  background: linear-gradient(to bottom, rgba(4, 147, 114, 0.05) 0%, rgba(4, 147, 114, 0.1) 100%);
  transition: all 0.2s ease;
  position: relative;
}

.direction.selectable:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(4, 147, 114, 0.2);
  border-color: #037a5a;
  background: linear-gradient(to bottom, rgba(4, 147, 114, 0.1) 0%, rgba(4, 147, 114, 0.15) 100%);
}

.direction.selection-disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.02) 0%, rgba(0, 0, 0, 0.05) 100%);
}

.direction.highlighted {
  border-color: #049372;
  box-shadow: 0 4px 12px rgba(4, 147, 114, 0.2);
}

.cito-badge {
  display: inline-block;
  background: #5d7ce1;
  color: #fff;
  font-size: 10px;
  font-weight: bold;
  border-radius: 4px;
  padding: 2px 6px;
  margin-left: 6px;
  margin-right: 2px;
  letter-spacing: 1px;
  vertical-align: middle;
}

.cancel-selection {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cancel-selection:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
}

.selection-mode-footer {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(135deg, #049372, #037a5a);
  color: white;
  padding: 12px;
  border-radius: 6px 6px 0 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 -2px 8px rgba(4, 147, 114, 0.3);
  z-index: 10;
  height: 100px;
}

.selection-image-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.image-info-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
  opacity: 0.9;
}

.image-info-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
  width: 200px;
}

.image-patient {
  font-weight: 600;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  max-height: 40px;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.image-datetime {
  font-size: 12px;
  opacity: 0.8;
}

.request-details-fullscreen {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  padding: 0;
}

.request-details-body {
  height: 100%;
  height: calc(100vh - 200px);
  overflow: hidden;
}

.request-details-content {
  display: flex;
  height: 100%;
  gap: 20px;
  padding: 20px;
  overflow: hidden;
}

.left-column {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  padding-right: 10px;
  border-right: 1px solid #e0e0e0;
}

.right-column {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  padding-left: 10px;
}

.loading-details {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #049372;
}

.spinner-small {
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top: 4px solid #049372;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.detail-section {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.detail-section-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 10px;
  color: #333;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
  font-size: 14px;
  color: #555;
}

.detail-label {
  font-weight: 500;
  color: #666;
  min-width: 150px;
}

.detail-value {
  font-weight: 600;
  color: #333;
  flex: 1;
  text-align: right;
}

.detail-value.empty-value {
  color: #888;
  font-style: italic;
}

.researches-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.research-item {
  padding: 8px 12px;
  background-color: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #e9ecef;
}

.research-title-full {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  line-height: 1.4;
}

.research-short-title {
  font-size: 12px;
  color: #666;
  margin-top: 2px;
}

.no-researches {
  font-size: 14px;
  color: #888;
  text-align: center;
  padding: 10px 0;
}

.files-list-modal {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.file-link-modal {
  font-size: 13px;
  color: #049372;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 10px;
  border-radius: 5px;
  transition: background-color 0.2s;
  background-color: #f0f9f7;
}

.file-link-modal:hover {
  background-color: rgba(4, 147, 114, 0.1);
  text-decoration: none;
  color: #037a5a;
}

.file-link-modal i {
  font-size: 14px;
}

.no-files {
  font-size: 14px;
  color: #888;
  text-align: center;
  padding: 10px 0;
}

.detail-textarea-row {
  display: flex;
  flex-direction: column;
  margin-bottom: 15px;
}

.detail-textarea-row .detail-label {
  margin-bottom: 5px;
  min-width: auto;
}

.detail-textarea-value {
  font-size: 14px;
  color: #333;
  padding: 8px 12px;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  background-color: #f8f9fa;
  min-height: 60px;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.4;
}

.detail-textarea-value.empty-value {
  color: #888;
  font-style: italic;
}
</style>
