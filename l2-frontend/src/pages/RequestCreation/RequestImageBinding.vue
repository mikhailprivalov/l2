<template>
  <div class="image-binding-root">
    <div class="image-binding-header">
      <div class="equipment-select-wrap">
        <Treeselect
          v-model="selectedEquipment"
          :options="equipmentList"
          :multiple="false"
          :disable-branch-nodes="true"
          class="equipment-select"
          :append-to-body="true"
          :clearable="false"
          :z-index="5001"
          :disabled="props.isSelectionMode"
        />
      </div>
      <div class="date-select-wrap">
        <DateFieldNav
          :def="selectedDate"
          :val.sync="selectedDate"
          w="100px"
          light
          class="date-select"
          :disabled="props.isSelectionMode"
        />
      </div>
      <div
        v-if="props.isSelectionMode"
        class="header-selection-overlay"
      />
    </div>
    <div class="image-list">
      <div
        v-if="!equipmentLoaded"
        class="image-list-overlay"
      >
        <div class="spinner" />
      </div>
      <div
        v-else-if="equipmentList.length === 0"
        class="no-equipment"
      >
        <div class="no-equipment-icon">
          <i class="fa fa-exclamation-triangle" />
        </div>
        <div class="no-equipment-title">
          Нет доступного оборудования
        </div>
        <div class="no-equipment-text">
          Обратитесь к администратору для настройки доступа к оборудованию
        </div>
      </div>
      <template v-else>
        <div
          v-if="isLoading"
          class="image-list-overlay"
        >
          <div class="spinner" />
        </div>
        <div
          v-for="image in images"
          :key="image.id"
          class="image-item"
          :class="{
            'highlighted': isImageHighlighted(image)
          }"
          @mouseenter="onImageMouseEnter(image)"
          @mouseleave="onImageMouseLeave"
        >
          <div
            class="status-indicator"
            :class="image.linked ? 'linked' : 'unlinked'"
          />
          <div class="image-info">
            <div class="image-date">
              {{ image.datetime }}
            </div>
            <div class="image-patient">
              {{ image.patient }}
            </div>
            <div
              v-if="image.patientId || image.orderId"
              class="image-ids"
            >
              <span v-if="image.patientId">ID пациента: {{ image.patientId }}</span>
              <span v-if="image.orderId">{{ image.patientId ? ' • ' : '' }}ID заказа: {{ image.orderId }}</span>
            </div>
          </div>
          <div class="image-actions">
            <button
              class="btn btn-blue-nb btn-xs"
              :disabled="props.isSelectionMode && (!props.currentImageForLink || props.currentImageForLink.id !== image.id)"
              @click="handleButtonClick(image)"
            >
              {{ getButtonText(image) }}
            </button>
            <div class="bottom-row">
              <div
                v-if="image.linked && image.requestId"
                class="image-request-number"
              >
                {{ image.requestId }}
              </div>
              <a
                href="#"
                class="a-under-reversed details-link"
                :class="{ 'disabled': props.isSelectionMode }"
                @click.prevent="!props.isSelectionMode && showImageDetails(image)"
              >
                <i class="fa fa-info-circle" />
              </a>
            </div>
          </div>
        </div>
        <div
          v-if="images.length === 0 && selectedEquipment"
          class="no-images"
        >
          Нет снимков
        </div>
        <div
          v-if="isLoadingMore"
          class="loading-more"
        >
          <div class="spinner-small" />
          <span>Загрузка...</span>
        </div>
      </template>
    </div>
    <Modal
      v-if="showImageDetailsModal"
      show-footer="true"
      white-bg="true"
      min-width="90%"
      height="80%"
      margin-left-right="20px"
      margin-top="40px"
      @close="hideImageDetailsModal"
    >
      <span slot="header">Детали изображения</span>
      <div slot="body">
        <div
          v-if="isLoadingDetails"
          class="loading-details"
        >
          <div class="spinner-small" />
          <span>Загрузка...</span>
        </div>
        <div
          v-else-if="imageDetails"
          class="image-details-fullscreen"
        >
          <div
            class="row"
            style="height: 100%;"
          >
            <div class="col-xs-6 left-column">
              <div class="detail-section">
                <h4 class="detail-section-title">
                  Основная информация
                </h4>
                <div class="detail-row">
                  <span class="detail-label">ID записи:</span>
                  <span class="detail-value">{{ imageDetails.id }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Фамилия:</span>
                  <span
                    class="detail-value"
                    :class="{ 'empty-value': !imageDetails.family }"
                  >{{ imageDetails.family || '(не указана)' }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Имя:</span>
                  <span
                    class="detail-value"
                    :class="{ 'empty-value': !imageDetails.name }"
                  >{{ imageDetails.name || '(не указано)' }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Отчество:</span>
                  <span
                    class="detail-value"
                    :class="{ 'empty-value': !imageDetails.patronymic }"
                  >{{ imageDetails.patronymic || '(не указано)' }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Дата рождения:</span>
                  <span
                    class="detail-value"
                    :class="{ 'empty-value': !imageDetails.birthday }"
                  >{{ imageDetails.birthday || '(не указана)' }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Пол:</span>
                  <span
                    class="detail-value"
                    :class="{ 'empty-value': !imageDetails.sex }"
                  >{{ imageDetails.sex || '(не указан)' }}</span>
                </div>
              </div>

              <div class="detail-section">
                <h4 class="detail-section-title">
                  Идентификаторы
                </h4>
                <div class="detail-row">
                  <span class="detail-label">ID пациента:</span>
                  <span
                    class="detail-value"
                    :class="{ 'empty-value': !imageDetails.patientId }"
                  >{{ imageDetails.patientId || '(отсутствует)' }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">ID заказа:</span>
                  <span
                    class="detail-value"
                    :class="{ 'empty-value': !imageDetails.orderId }"
                  >{{ imageDetails.orderId || '(отсутствует)' }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">ID направления:</span>
                  <span
                    class="detail-value"
                    :class="{ 'empty-value': !imageDetails.napravleniyeId }"
                  >{{ imageDetails.napravleniyeId || '(не привязано)' }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Study Instance UID Tag:</span>
                  <span
                    class="detail-value small-text"
                    :class="{ 'empty-value': !imageDetails.studyInstanceUidTag }"
                  >{{ imageDetails.studyInstanceUidTag || '(отсутствует)' }}</span>
                </div>
              </div>

              <div class="detail-section">
                <h4 class="detail-section-title">
                  Оборудование
                </h4>
                <div class="detail-row">
                  <span class="detail-label">Название:</span>
                  <span
                    class="detail-value"
                    :class="{ 'empty-value': !imageDetails.equipmentTitle }"
                  >{{ imageDetails.equipmentTitle || '(не определено)' }}</span>
                </div>
              </div>
            </div>

            <div class="col-xs-6 right-column">
              <div class="detail-section">
                <h4 class="detail-section-title">
                  Временные метки
                </h4>
                <div class="detail-row">
                  <span class="detail-label">Создано:</span>
                  <span class="detail-value">{{ imageDetails.createdAt }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Обновлено:</span>
                  <span
                    class="detail-value"
                    :class="{ 'empty-value': !imageDetails.updatedAt }"
                  >{{ imageDetails.updatedAt || '(не обновлялось)' }}</span>
                </div>
              </div>

              <div class="detail-section">
                <h4 class="detail-section-title">
                  История привязки
                </h4>
                <div class="detail-row">
                  <span class="detail-label">Статус:</span>
                  <span class="detail-value">{{ imageDetails.linked ? 'Привязано' : 'Не привязано' }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Привязал:</span>
                  <span
                    class="detail-value"
                    :class="{ 'empty-value': !imageDetails.docSaveLink }"
                  >{{ imageDetails.docSaveLink || '(никто)' }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Время привязки:</span>
                  <span
                    class="detail-value"
                    :class="{ 'empty-value': !imageDetails.timeSaveLink }"
                  >{{ imageDetails.timeSaveLink || '(не привязывалось)' }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Отвязал:</span>
                  <span
                    class="detail-value"
                    :class="{ 'empty-value': !imageDetails.docResetLink }"
                  >{{ imageDetails.docResetLink || '(никто)' }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Время отвязки:</span>
                  <span
                    class="detail-value"
                    :class="{ 'empty-value': !imageDetails.timeResetLink }"
                  >{{ imageDetails.timeResetLink || '(не отвязывалось)' }}</span>
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
              @click="hideImageDetailsModal"
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
  getCurrentInstance, nextTick, onMounted, onUnmounted, ref, watch,
} from 'vue';
import moment from 'moment';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import DateFieldNav from '@/fields/DateFieldNav.vue';
import Modal from '@/ui-cards/Modal.vue';
import api from '@/api';
import useLoader from '@/hooks/useLoader';
import useNotify from '@/hooks/useNotify';

type Equipment = {
  id: number;
  name: string;
};
type Image = {
  id: number;
  family: string;
  name: string;
  patronymic: string;
  birthday: string;
  sex: string;
  patientId: string | null;
  orderId: string | null;
  patient: string;
  datetime: string;
  equipmentId: string;
  linked: boolean;
  requestId: string | null;
};

const emit = defineEmits(['image-linked', 'image-unlinked', 'request-link-needed', 'cancel-selection', 'image-hover']);

const props = defineProps<{
  isSelectionMode?: boolean;
  currentImageForLink?: any;
  highlightedImageId?: number | string | null;
}>();

const root = getCurrentInstance().proxy.$root;
const loader = useLoader();
const notify = useNotify();

const equipmentList = ref<Equipment[]>([]);
const equipmentLoaded = ref(false);
const selectedEquipment = ref(equipmentList.value?.[0]?.id || null);
const selectedDate = ref(moment().format('DD.MM.YYYY'));
const images = ref<Image[]>([]);
const isLoading = ref(false);
const isLoadingMore = ref(false);

const showImageDetailsModal = ref(false);
const imageDetails = ref<any>(null);
const isLoadingDetails = ref(false);

const currentPage = ref(1);
const pageSize = ref(50);
const hasMore = ref(false);
const total = ref(0);
const lastId = ref<number | null>(null);

let autoRefreshTimer: ReturnType<typeof setInterval> | null = null;
const imageListElement = ref<HTMLElement | null>(null);

const getEquipmentList = async () => {
  loader.inc();
  try {
    const { rows } = await api('requests/equipment');
    equipmentList.value = rows;
    if (rows.length > 0) {
      selectedEquipment.value = rows[0].id;
    }
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error(error);
    notify.error('Ошибка при получении оборудования');
  } finally {
    equipmentLoaded.value = true;
    loader.dec();
  }
};

const getImages = async (page = 1, append = false) => {
  if (!selectedEquipment.value || !equipmentLoaded.value) {
    images.value = [];
    return;
  }

  if (page === 1) {
    isLoading.value = true;
    currentPage.value = 1;
    lastId.value = null;
  } else {
    isLoadingMore.value = true;
  }

  try {
    const params: any = {
      equipmentId: selectedEquipment.value,
      date: selectedDate.value,
      page,
      pageSize: pageSize.value,
    };

    if (lastId.value && append) {
      params.lastId = lastId.value;
    }

    const { rows, hasMore: responseHasMore, total: responseTotal } = await api('requests/images', params);

    if (append && page > 1) {
      const newImages = rows.filter((newImg: Image) => !images.value.some(existingImg => existingImg.id === newImg.id));
      images.value = [...images.value, ...newImages];
    } else {
      images.value = rows;
    }

    hasMore.value = responseHasMore;
    total.value = responseTotal;

    if (rows.length > 0) {
      lastId.value = rows[rows.length - 1].id;
    }

    currentPage.value = page;
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error(error);
    root.$emit('msg', 'error', 'Ошибка при получении снимков');
  } finally {
    isLoading.value = false;
    isLoadingMore.value = false;
  }
};

const loadMoreImages = async () => {
  if (hasMore.value && !isLoadingMore.value) {
    await getImages(currentPage.value + 1, true);
  }
};

const checkForNewImages = async () => {
  if (!selectedEquipment.value || !equipmentLoaded.value || isLoading.value) {
    return;
  }

  try {
    const { rows } = await api('requests/images', {
      equipmentId: selectedEquipment.value,
      date: selectedDate.value,
      page: 1,
      pageSize: pageSize.value,
    });

    if (rows.length > 0) {
      const newImages = rows.filter((newImg: Image) => !images.value.some(existingImg => existingImg.id === newImg.id));

      if (newImages.length > 0) {
        images.value = [...newImages, ...images.value];
        total.value += newImages.length;
      }
    }
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error('Ошибка при проверке новых изображений:', error);
  }
};

const onScroll = (event: Event) => {
  const target = event.target as HTMLElement;
  const { scrollTop } = target;
  const { scrollHeight } = target;
  const { clientHeight } = target;

  if (scrollHeight - scrollTop - clientHeight < 100 && hasMore.value && !isLoadingMore.value) {
    loadMoreImages();
  }
};

const setupScrollListener = () => {
  nextTick(() => {
    const imageList = document.querySelector('.image-list') as HTMLElement;
    if (imageList) {
      imageListElement.value = imageList;
      imageList.addEventListener('scroll', onScroll);
    }
  });
};

const removeScrollListener = () => {
  if (imageListElement.value) {
    imageListElement.value.removeEventListener('scroll', onScroll);
  }
};

const startAutoRefresh = () => {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer);
  }
  autoRefreshTimer = setInterval(checkForNewImages, 5000);
};

const stopAutoRefresh = () => {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer);
    autoRefreshTimer = null;
  }
};

const toggleLink = async (image: Image) => {
  if (image.linked) {
    try {
      await root.$dialog.confirm('Вы уверены, что хотите отвязать это изображение от заявки?');
    } catch (_) {
      return;
    }

    try {
      const response = await api('requests/link-image', {
        imageId: image.id,
        requestId: null,
      });

      if (response.ok) {
        notify.ok(response.message || 'Изображение отвязано');
        if (image.requestId) {
          emit('image-unlinked', image.requestId);
        }
        await getImages();
      } else {
        notify.error(response.message || 'Ошибка при отвязывании изображения');
      }
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error(error);
      notify.error('Ошибка при отвязывании изображения');
    }
  } else {
    emit('request-link-needed', image);
  }
};

const linkImageToRequest = async (image: Image, request: any) => {
  try {
    const response = await api('requests/link-image', {
      imageId: image.id,
      requestId: request.id,
    });

    if (response.ok) {
      notify.ok(response.message || 'Изображение привязано к заявке');
      emit('image-linked', request.id);
      await getImages();
    } else {
      notify.error(response.message || 'Ошибка при привязывании изображения');
    }
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error(error);
    notify.error('Ошибка при привязывании изображения');
  }
};

const showImageDetails = async (image: Image) => {
  isLoadingDetails.value = true;
  showImageDetailsModal.value = true;
  imageDetails.value = null;

  const response = await api('requests/image-details', { imageId: image.id });
  if (response.success) {
    imageDetails.value = response.data;
  } else {
    notify.error(response.message || 'Ошибка при получении деталей изображения');
    showImageDetailsModal.value = false;
  }
  isLoadingDetails.value = false;
};

const hideImageDetailsModal = () => {
  showImageDetailsModal.value = false;
  imageDetails.value = null;
};

const handleButtonClick = (image: Image) => {
  if (props.currentImageForLink && props.currentImageForLink.id === image.id) {
    emit('cancel-selection');
  } else {
    toggleLink(image);
  }
};

const getButtonText = (image: Image) => {
  if (props.currentImageForLink && props.currentImageForLink.id === image.id) {
    return 'Отмена';
  }
  return image.linked ? 'Отвязать' : 'Привязать';
};

const isImageHighlighted = (image: Image) => (
  props.highlightedImageId && image.requestId && image.requestId.toString() === props.highlightedImageId.toString()
);

const onImageMouseEnter = (image: Image) => {
  emit('image-hover', image);
};

const onImageMouseLeave = () => {
  emit('image-hover', null);
};

onMounted(async () => {
  await getEquipmentList();
  if (equipmentList.value.length > 0) {
    await getImages();
    setupScrollListener();
    startAutoRefresh();
  }
});

onUnmounted(() => {
  removeScrollListener();
  stopAutoRefresh();
});

watch([selectedEquipment, selectedDate], async () => {
  if (equipmentLoaded.value && selectedEquipment.value) {
    await getImages();
    setupScrollListener();
  }
});

watch(equipmentLoaded, async (newVal) => {
  if (newVal && selectedEquipment.value) {
    await getImages();
    setupScrollListener();
    startAutoRefresh();
  }
});

defineExpose({
  linkImageToRequest,
});
</script>

<style scoped lang="scss">
.image-binding-root {
  display: flex;
  flex-direction: column;
  max-width: 600px;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
}
.image-binding-header {
  position: relative;
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
}
.equipment-select-wrap {
  flex: 1 1 0;
  min-width: 0;
}
.date-select-wrap {
  width: 180px;
  display: flex;
  align-items: center;
}
.equipment-select {
  width: 100%;
}
.date-select {
  width: 100%;
}
.image-list {
  position: absolute;
  top: 46px;
  left: 0;
  right: 0;
  bottom: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 8px;
  overflow-y: auto;
  overflow-x: hidden;
}
.image-list-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255,255,255,0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}
.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f5fffb;
  border-top: 4px solid #049372;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
.image-item {
  position: relative;
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  justify-content: space-between;
  padding: 10px 14px 8px 14px;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
  background: #fff;
  box-shadow: 0 1px 4px 0 rgba(60,60,60,0.04);
  gap: 24px;
  min-width: 180px;
}

.image-item.highlighted {
  border-color: #049372;
  box-shadow: 0 4px 12px rgba(4, 147, 114, 0.2);
}
.status-indicator {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  z-index: 1;
  border: 2px solid #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
.status-indicator.linked {
  background: #049372;
}
.status-indicator.unlinked {
  background: #ffa500;
}
.image-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  width: 100%;
  flex: 1 1 auto;
}
.image-date {
  font-size: 15px;
  color: #333;
  font-weight: 500;
  margin-bottom: 0;
}
.image-patient {
  font-size: 14px;
  color: #222;
  font-weight: 500;
}
.image-ids {
  font-size: 12px;
  color: #666;
  line-height: 1.2;
}
.image-request-number {
  font-size: 12px;
  color: #049372;
  font-weight: 600;
  background: #f0f9f7;
  padding: 1px 4px;
  border-radius: 3px;
  display: inline-block;
}
.image-actions {
  width: 110px;
  min-width: 90px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: flex-start;
  margin-top: 0;
  gap: 6px;
}

.bottom-row {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
}
.btn.btn-blue-nb.btn-xs {
  padding: 2px 12px;
  font-size: 13px;
  height: 26px;
  min-width: 70px;
}

.btn.btn-blue-nb.btn-xs:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #ccc;
  border-color: #ccc;
}

.details-link {
  color: #a8a8a8;
  font-size: 16px;
  align-self: flex-end;
  margin-top: 2px;
}

.details-link:hover {
  color: #049372;
}

.details-link.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.details-link.disabled:hover {
  color: #a8a8a8;
}

.equipment-select:disabled,
.date-select:disabled {
  opacity: 0.6;
  pointer-events: none;
}

.loading-details {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  color: #666;
  font-size: 14px;
}
.image-details {
  max-height: 400px;
  overflow-y: auto;
}
.image-details-fullscreen {
  height: 100%;
  overflow: hidden;
}
.left-column {
  height: 100%;
  border-right: 1px solid #e0e0e0;
  padding-right: 20px;
  overflow-y: auto;
}
.right-column {
  height: 100%;
  padding-left: 20px;
  overflow-y: auto;
}
.detail-section {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #f0f0f0;
}
.detail-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}
.detail-section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 10px;
  padding-left: 5px;
}
.detail-row {
  display: flex;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}
.detail-row:last-child {
  border-bottom: none;
}
.detail-label {
  font-weight: 600;
  color: #333;
  min-width: 140px;
  flex-shrink: 0;
  font-size: 13px;
}
.detail-value {
  color: #666;
  margin-left: 8px;
  flex: 1;
  font-size: 13px;
  word-break: break-word;
}
.detail-value.small-text {
  font-size: 11px;
  font-family: 'Courier New', monospace;
}
.detail-value.empty-value {
  color: #999;
  font-style: italic;
}
.no-images {
  color: #aaa;
  font-style: italic;
  padding: 10px 0;
  text-align: center;
}
.no-equipment {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  height: 200px;
}
.no-equipment-icon {
  font-size: 48px;
  color: #888;
  margin-bottom: 16px;
}
.no-equipment-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}
.no-equipment-text {
  font-size: 14px;
  color: #666;
  max-width: 300px;
  line-height: 1.4;
}
.loading-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  color: #666;
  font-size: 14px;
}
.spinner-small {
  width: 20px;
  height: 20px;
  border: 2px solid #f5fffb;
  border-top: 2px solid #049372;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
.header-selection-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  z-index: 1000;
  pointer-events: all;
  border-radius: 4px;
}
</style>
