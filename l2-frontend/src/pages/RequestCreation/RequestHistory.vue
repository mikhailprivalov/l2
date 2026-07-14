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
          v-if="searchMode === 'card'"
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
        :class="{ 'with-filter': searchMode === 'card' }"
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
              <br>
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
              <button
                v-if="!item.hasResult && 'cancel'!==searchMode && !item.acceptWhoDoctor"
                class="cancel-direction-btn"
                title="Отменить направление"
                @click.stop="cancelDirection(item.id)"
              >
                Скрыть
              </button>
              <button
                v-if="searchMode === 'cancel'"
                class="cancel-direction-btn"
                title="Вернуть направление"
                @click.stop="cancelDirection(item.id)"
              >
                В работу
              </button>
              <span
                v-if="item.acceptWhoDoctor && !item.hasResult"
                class="accept-badge"
              >Принято</span>
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
                <template v-if="requestDetails.editable">
                  <div class="detail-research-labels">
                    <div class="detail-research-row">
                      <span class="detail-label">текущее</span>
                      <span class="detail-value">{{ currentResearchTitle || '—' }}</span>
                    </div>
                    <div class="detail-research-row">
                      <span class="detail-label">новое</span>
                      <span class="detail-value">{{ newResearchTitle || '—' }}</span>
                    </div>
                  </div>
                  <div class="research-picker-wrap">
                    <ResearchesPicker
                      v-model="editForm.researchId"
                      :hidetemplates="true"
                      oneselect
                      :autoselect="false"
                      kk="request_details_edit"
                      just_search
                      :types-only="[3]"
                      hide-type-picker
                    />
                  </div>
                </template>
                <div
                  v-else-if="requestDetails.researches && requestDetails.researches.length > 0"
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
                  v-else-if="!requestDetails.editable"
                  class="no-files"
                >
                  Файлы не прикреплены
                </div>
                <div
                  v-if="requestDetails.editable"
                  class="file-upload-edit"
                >
                  <input
                    ref="detailFileInput"
                    type="file"
                    style="display: none"
                    @change="handleDetailFileChange"
                  >
                  <div
                    v-if="!selectedDetailFile"
                    class="file-drop-zone"
                    @click="openDetailFileDialog"
                    @dragover.prevent
                    @drop.prevent="handleDetailFileDrop"
                  >
                    <div class="file-drop-content">
                      <i class="fa fa-cloud-upload" />
                      <span>Добавить файл (до 10 МБ)</span>
                    </div>
                  </div>
                  <div
                    v-else
                    class="selected-file"
                  >
                    <div class="file-info">
                      <div class="file-icon">
                        <i class="fa fa-file" />
                      </div>
                      <div class="file-details">
                        <div class="file-name">
                          {{ selectedDetailFile.name }}
                        </div>
                        <div class="file-size">
                          {{ formatFileSize(selectedDetailFile.size) }}
                        </div>
                      </div>
                    </div>
                    <div class="file-actions">
                      <button
                        type="button"
                        class="btn-change"
                        title="Заменить файл"
                        @click="openDetailFileDialog"
                      >
                        <i class="fa fa-refresh" />
                      </button>
                      <button
                        type="button"
                        class="btn-remove"
                        title="Удалить файл"
                        @click="removeDetailFile"
                      >
                        <i class="fa fa-times" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="right-column">
              <div class="detail-section">
                <h4 class="detail-section-title">
                  Параметры исследования
                </h4>
                <template v-if="requestDetails.editable">
                  <div class="detail-params-row">
                    <div class="detail-params-field detail-params-field--datetime">
                      <label class="detail-params-label">Дата и время исследования</label>
                      <div class="detail-params-datetime">
                        <input
                          v-model="editForm.date"
                          type="date"
                          class="form-control detail-edit-input detail-edit-input--date"
                        >
                        <input
                          v-model="editForm.time"
                          type="time"
                          class="form-control detail-edit-input detail-edit-input--time"
                        >
                      </div>
                    </div>
                    <div class="detail-params-field detail-params-field--dose">
                      <label class="detail-params-label">Доза</label>
                      <input
                        v-model="editForm.dose"
                        type="number"
                        class="form-control detail-edit-input detail-edit-input--dose"
                        placeholder="мЗв"
                      >
                    </div>
                    <div class="detail-params-field detail-params-field--checkboxes">
                      <label class="detail-checkbox">
                        <input
                          v-model="editForm.cito"
                          type="checkbox"
                        >
                        Cito
                      </label>
                      <label class="detail-checkbox">
                        <input
                          v-model="editForm.isDynamic"
                          type="checkbox"
                        >
                        Динамика
                      </label>
                    </div>
                  </div>
                  <div class="detail-params-row">
                    <div class="detail-params-field detail-params-field--contrast">
                      <label class="detail-params-label">Контраст</label>
                      <Treeselect
                        v-model="editForm.currentContrast"
                        :multiple="false"
                        :options="contrastOptions"
                        :append-to-body="true"
                        placeholder="Выберите контраст"
                        class="detail-edit-treeselect"
                      />
                    </div>
                    <div class="detail-params-field detail-params-field--volume">
                      <label class="detail-params-label">Объём</label>
                      <input
                        v-model="editForm.contrastAmount"
                        type="number"
                        class="form-control detail-edit-input detail-edit-input--volume"
                        placeholder="мг"
                      >
                    </div>
                  </div>
                </template>
                <template v-else>
                  <div class="detail-row">
                    <span class="detail-label">Дата исследования:</span>
                    <span
                      class="detail-value"
                      :class="{ 'empty-value': !requestDetails.factResearchDate }"
                    >{{ requestDetails.factResearchDate || '(не указана)' }}</span>
                  </div>
                  <div class="detail-row">
                    <span class="detail-label">Время исследования:</span>
                    <span
                      class="detail-value"
                      :class="{ 'empty-value': !requestDetails.factResearchTime }"
                    >{{ requestDetails.factResearchTime || '(не указано)' }}</span>
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
                    <span class="detail-label">Контраст:</span>
                    <span
                      class="detail-value"
                      :class="{ 'empty-value': !requestDetails.contrastText }"
                    >{{ requestDetails.contrastText || '(не указан)' }}</span>
                  </div>
                  <div class="detail-row">
                    <span class="detail-label">Срочность:</span>
                    <span class="detail-value">{{ requestDetails.isCito ? 'Cito' : 'Обычное' }}</span>
                  </div>
                  <div class="detail-row">
                    <span class="detail-label">Динамика:</span>
                    <span class="detail-value">{{ requestDetails.isDynamic ? 'Да' : 'Нет' }}</span>
                  </div>
                </template>
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
                  <textarea
                    v-if="requestDetails.editable"
                    v-model="editForm.anamnesis"
                    class="form-control detail-edit-textarea"
                    placeholder="Анамнез"
                  />
                  <div
                    v-else
                    class="detail-textarea-value"
                    :class="{ 'empty-value': !requestDetails.anamnesis }"
                    v-text="requestDetails.anamnesis || '(не указан)'"
                  />
                </div>
                <div class="detail-textarea-row">
                  <span class="detail-label">Комментарий:</span>
                  <textarea
                    v-if="requestDetails.editable"
                    v-model="editForm.comment"
                    class="form-control detail-edit-textarea"
                    placeholder="Комментарий"
                  />
                  <div
                    v-else
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
          <div class="col-xs-4 text-right">
            <div class="detail-modal-footer-buttons">
              <button
                class="btn btn-primary-nb btn-blue-nb"
                type="button"
                @click="hideRequestDetailsModal"
              >
                Закрыть
              </button>
              <button
                v-if="requestDetails && requestDetails.editable"
                class="btn btn-primary-nb btn-blue-nb"
                type="button"
                :disabled="isSavingDetails"
                @click="saveRequestDetails"
              >
                {{ isSavingDetails ? 'Сохранение...' : 'Сохранить' }}
              </button>
            </div>
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
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import api from '@/api';
import researchesPoint from '@/api/researches-point';
import useNotify from '@/hooks/useNotify';
import useLoader from '@/hooks/useLoader';
import usePrint from '@/hooks/usePrint';
import { useStore } from '@/store';
import DateRange from '@/ui-cards/DateRange.vue';
import Modal from '@/ui-cards/Modal.vue';
import ResearchesPicker from '@/ui-cards/ResearchesPicker.vue';

const props = defineProps<{
  cardId?: number | null;
  highlightedRequestId?: number | string | null;
}>();
const notify = useNotify();
const loader = useLoader();
const { printResults } = usePrint();
const store = useStore();

const printResult = (id: number) => {
  printResults([id]);
};

const emit = defineEmits(['request-selected', 'cancel-selection', 'request-hover']);

const SEARCH_MODES = [
  { id: 'all', title: 'Мои заявки' },
  { id: 'card', title: 'Пациент' },
  { id: 'search', title: 'Организация' },
  { id: 'cancel', title: 'Скрытые' },
];

const SEARCH_MODES_MAP = new Map(SEARCH_MODES.map((m) => [m.id, m.title]));

const searchMode = ref(SEARCH_MODES[0].id);
const availableSearchModes = computed(() => SEARCH_MODES.filter((mode) => mode.id !== searchMode.value));
const dateRange = ref([moment().format('DD.MM.YYYY'), moment().format('DD.MM.YYYY')]);
const dateRangeKey = computed(() => dateRange.value.join('|'));
const isMultipleDays = computed(() => dateRange.value[0] !== dateRange.value[1]);
const showModes = ref(false);
const isLoading = ref(false);
const onlyMine = ref(false);
const isSelectionMode = ref(false);
const currentImageForLink = ref<any>(null);
const showRequestDetailsModal = ref(false);
const requestDetails = ref<any>(null);
const isLoadingDetails = ref(false);
const isSavingDetails = ref(false);
const detailFileInput = ref<HTMLInputElement>();
const selectedDetailFile = ref<File | null>(null);
const contrastOptions = ref([]);

type EditForm = {
  researchId: number | null;
  date: string;
  time: string;
  dose: string;
  cito: boolean;
  isDynamic: boolean;
  currentContrast: number;
  contrastAmount: string;
  anamnesis: string;
  comment: string;
  files: Array<{ url: string; name: string; type: string }>;
};

const defaultEditForm = (): EditForm => ({
  researchId: null,
  date: '',
  time: '',
  dose: '',
  cito: false,
  isDynamic: false,
  currentContrast: -1,
  contrastAmount: '',
  anamnesis: '',
  comment: '',
  files: [],
});

const editForm = ref<EditForm>(defaultEditForm());
const currentResearchTitle = ref('');

const getResearchTitle = (researchId: number | null) => {
  if (!researchId || researchId === -1) {
    return '';
  }

  const fromStore = store.getters.researches_obj?.[researchId];
  if (fromStore?.title) {
    return fromStore.short_title || fromStore.title;
  }

  const fromDetails = requestDetails.value?.researches?.find(
    (research: { id: number }) => research.id === researchId,
  );
  return fromDetails?.short_title || fromDetails?.title || '';
};

const newResearchTitle = computed(() => getResearchTitle(editForm.value.researchId));

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

type RequestFile = {
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
  acceptWhoDoctor: boolean;
  cardId: number;
  files: RequestFile[];
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

const scrollListToTop = (smooth = false) => {
  if (!listContainer.value) return;
  listContainer.value.scrollTo({
    top: 0,
    behavior: smooth ? 'smooth' : 'auto',
  });
};

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
    // eslint-disable-next-line no-console
    console.error(error);
  } finally {
    isRefreshing.value = false;
  }
};

watch([searchMode, actualCardId, dateRange, onlyMine], async () => {
  await getRequests();
}, { immediate: true, deep: true });

watch(searchMode, (newMode, prevMode) => {
  if (!prevMode) return;
  scrollListToTop();
});

watch(dateRangeKey, (newKey, prevKey) => {
  if (!prevKey || newKey === prevKey) return;
  scrollListToTop();
});

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

const cancelDirection = async (pk: number) => {
  await api('directions/cancel', { pk });
  await getRequests();
};

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Б';
  const k = 1024;
  const sizes = ['Б', 'КБ', 'МБ', 'ГБ'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${Math.round((bytes / (k ** i)) * 100) / 100} ${sizes[i]}`;
};

const convertFileToBase64 = (
  file: File,
): Promise<{ url: string; name: string; type: string }> => new Promise((resolve, reject) => {
  const reader = new FileReader();
  reader.onload = (e) => {
    resolve({
      url: e.target?.result as string,
      name: file.name,
      type: file.type,
    });
  };
  reader.onerror = reject;
  reader.readAsDataURL(file);
});

const updateEditFormFiles = async () => {
  if (selectedDetailFile.value) {
    const fileData = await convertFileToBase64(selectedDetailFile.value);
    editForm.value.files = [fileData];
  } else {
    editForm.value.files = [];
  }
};

const handleDetailFileChange = async (event: Event) => {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];

  if (!file) {
    selectedDetailFile.value = null;
    await updateEditFormFiles();
    return;
  }

  if (file.size > 10 * 1024 * 1024) {
    notify.error('Размер файла больше 10 МБ');
    selectedDetailFile.value = null;
    await updateEditFormFiles();
    return;
  }

  selectedDetailFile.value = file;
  await updateEditFormFiles();
  input.value = '';
};

const handleDetailFileDrop = async (event: DragEvent) => {
  const file = event.dataTransfer?.files?.[0];
  if (!file) {
    return;
  }

  if (file.size > 10 * 1024 * 1024) {
    notify.error(`Размер файла "${file.name}" превышает установленный лимит в 10 МБ.`);
    selectedDetailFile.value = null;
    await updateEditFormFiles();
    return;
  }

  selectedDetailFile.value = file;
  await updateEditFormFiles();
};

const openDetailFileDialog = () => {
  detailFileInput.value?.click();
};

const removeDetailFile = async () => {
  selectedDetailFile.value = null;
  await updateEditFormFiles();
};

const populateEditForm = (details: any) => {
  editForm.value = {
    researchId: details.researchId || null,
    date: details.editDate || '',
    time: details.editTime || '',
    dose: details.dose || '',
    cito: details.isCito || false,
    isDynamic: details.isDynamic || false,
    currentContrast: details.currentContrast ?? -1,
    contrastAmount: details.contrastAmount || '',
    anamnesis: details.anamnesis || '',
    comment: details.comment || '',
    files: [],
  };
  currentResearchTitle.value = details.researches?.[0]?.short_title
    || details.researches?.[0]?.title
    || '';
  selectedDetailFile.value = null;
};

const loadContrastOptions = async () => {
  const response = await researchesPoint.getContrastCollect();
  contrastOptions.value = response.data;
};

const showRequestDetails = async (requestId: number) => {
  isLoadingDetails.value = true;
  showRequestDetailsModal.value = true;
  requestDetails.value = null;

  try {
    if (!contrastOptions.value.length) {
      await loadContrastOptions();
    }
    const response = await api('requests/request-details', { requestId });
    if (response.success) {
      requestDetails.value = response.data;
      if (response.data.editable) {
        populateEditForm(response.data);
      }
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
  editForm.value = defaultEditForm();
  currentResearchTitle.value = '';
  selectedDetailFile.value = null;
};

const saveRequestDetails = async () => {
  if (!requestDetails.value?.editable) {
    return;
  }

  if (!editForm.value.date || !editForm.value.time) {
    notify.error('Не указана дата или время исследования');
    return;
  }

  if (!editForm.value.researchId) {
    notify.error('Не указана услуга');
    return;
  }

  isSavingDetails.value = true;
  loader.inc();
  try {
    const response = await api('requests/update', {
      requestId: requestDetails.value.id,
      researchId: editForm.value.researchId,
      requestFields: {
        date: editForm.value.date,
        time: editForm.value.time,
        dose: editForm.value.dose,
        cito: editForm.value.cito,
        isDynamic: editForm.value.isDynamic,
        currentContrast: editForm.value.currentContrast,
        contrastAmount: editForm.value.contrastAmount,
        anamnesis: editForm.value.anamnesis,
        comment: editForm.value.comment,
        files: editForm.value.files,
      },
    });

    if (!response.ok) {
      notify.error(response.message || 'Ошибка при сохранении заявки');
      return;
    }

    notify.ok(response.message || 'Заявка успешно обновлена');
    await getRequests();
    hideRequestDetailsModal();
  } catch (error) {
    notify.error('Ошибка при сохранении заявки');
    // eslint-disable-next-line no-console
    console.error('Ошибка при сохранении заявки:', error);
  } finally {
    isSavingDetails.value = false;
    loader.dec();
  }
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
.cancel-direction-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 600;
  color: #fff;
  background: #6C7A89;
  border: none;
  padding: 2px 6px;
  border-radius: 4px;
  margin-left: 6px;
  cursor: pointer;
  transition: background 0.2s;

  &:hover {
    background: #494949;
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

.accept-badge {
  display: inline-block;
  background: #046d93;
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
  flex: 1 1 0;
  min-width: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 10px;
  border-right: 1px solid #e0e0e0;
}

.right-column {
  flex: 1 1 0;
  min-width: 0;
  overflow-x: hidden;
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

.detail-research-labels {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 10px;
}

.detail-research-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 14px;

  .detail-label {
    flex: 0 0 80px;
    min-width: 80px;
    margin-bottom: 0;
    font-weight: 500;
    color: #666;
  }

  .detail-value {
    flex: 1;
    text-align: left;
    font-weight: 600;
    color: #333;
    word-break: break-word;
  }
}

.detail-modal-footer-buttons {
  display: inline-flex;
  flex-wrap: nowrap;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  white-space: nowrap;
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

.research-picker-wrap {
  position: relative;
  height: 280px;
  margin-bottom: 8px;
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

.detail-edit-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;

  .detail-label {
    flex: 0 0 150px;
    margin-bottom: 0;
  }

  &--checkboxes {
    gap: 20px;
    margin-top: 4px;
  }
}

.detail-params-row {
  display: flex;
  flex-wrap: nowrap;
  align-items: flex-end;
  gap: 8px;
  margin-bottom: 10px;
  min-width: 0;
}

.detail-params-field {
  flex: 1 1 0;
  min-width: 0;

  &--datetime {
    flex: 0 0 auto;
    width: 248px;
  }

  &--dose {
    flex: 0 0 100px;
    width: 100px;
  }

  &--checkboxes {
    flex: 0 0 auto;
    display: flex;
    align-items: center;
    gap: 12px;
    padding-bottom: 6px;
    white-space: nowrap;
  }

  &--contrast,
  &--volume {
    flex: 1 1 0;
    min-width: 0;
  }
}

.detail-params-label {
  display: block;
  margin-bottom: 5px;
  font-weight: 600;
  font-size: 14px;
  color: #374151;
}

.detail-params-datetime {
  display: flex;
  gap: 6px;

  .detail-edit-input--date {
    flex: 1 1 0;
    min-width: 0;
    max-width: 128px;
  }

  .detail-edit-input--time {
    flex: 0 0 100px;
    width: 100px;
    min-width: 100px;
    padding-left: 4px;
    padding-right: 4px;
  }
}

.detail-edit-input {
  width: 100%;
  height: 34px;

  &--dose {
    padding-left: 6px;
    padding-right: 6px;
  }

  &--volume {
    padding-left: 6px;
    padding-right: 6px;
  }
}

.detail-edit-treeselect {
  width: 100%;
}

.detail-edit-textarea {
  min-height: 80px;
  resize: vertical;
}

.detail-checkbox {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  font-weight: normal;
  cursor: pointer;

  input {
    margin: 0;
  }
}

.file-upload-edit {
  margin-top: 10px;
}

.file-drop-zone {
  border: 2px dashed #ccc;
  border-radius: 6px;
  padding: 12px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.3s ease;
  background-color: #f8f9fa;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 50px;
  color: #666;
  font-size: 14px;
}

.file-drop-zone:hover {
  border-color: #6c757d;
  background-color: #e9ecef;
}

.file-drop-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.selected-file {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-icon {
  font-size: 24px;
  color: #049372;
}

.file-details {
  display: flex;
  flex-direction: column;
}

.file-name {
  font-weight: 600;
  color: #333;
}

.file-size {
  font-size: 14px;
  color: #666;
}

.file-actions {
  display: flex;
  gap: 5px;
}

.btn-change,
.btn-remove {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-change {
  color: #049372;
}

.btn-change:hover {
  color: #037a5a;
}

.btn-remove {
  color: #dc3545;
}

.btn-remove:hover {
  color: #c82333;
}
</style>
