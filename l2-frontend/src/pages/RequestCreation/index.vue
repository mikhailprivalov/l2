<template>
  <PageInnerLayout>
    <TwoSidedLayout :left-width-px="800">
      <template #left>
        <TopBottomLayout :top-height-px="200">
          <template #top>
            <PatientCompactPicker
              v-model="cardId"
              :title-for-base="'Пациент'"
            />
          </template>
          <template #bottom>
            <TopBottomLayout
              split-half
              bottom-scrollable
            >
              <template #top>
                <ResearchesPicker
                  v-model="research"
                  :hidetemplates="true"
                  oneselect
                  :autoselect="false"
                  kk="request_creation"
                  just_search
                  :types-only="[3]"
                  hide-type-picker
                />
              </template>
              <template #bottom>
                <RequestFields
                  v-if="cardId && cardId !== -1 && research && research !== -1"
                  v-model="requestFields"
                  @create:request="createRequest"
                />
              </template>
            </TopBottomLayout>
          </template>
        </topbottomlayout>
        <div
          v-if="isSelectionMode"
          class="selection-overlay"
        />
      </template>
      <template #right>
        <TwoSidedLayout :left-width-px="300">
          <template #left>
            <RequestHistory
              ref="requestHistoryRef"
              key="requestHistoryKey"
              :card-id="cardId"
              :highlighted-request-id="hoveredImageId"
              @request-selected="onRequestSelectedForLink"
              @cancel-selection="onCancelSelection"
              @request-hover="onRequestHover"
            />
          </template>
          <template #right>
            <RequestImageBinding
              ref="requestImageBindingRef"
              key="requestImageBindingKey"
              :is-selection-mode="isSelectionMode"
              :current-image-for-link="currentImageForLink"
              :highlighted-image-id="hoveredRequestId"
              @image-linked="onImageLinked"
              @image-unlinked="onImageUnlinked"
              @request-link-needed="onRequestLinkNeeded"
              @cancel-selection="onCancelSelection"
              @image-hover="onImageHover"
            />
          </template>
        </TwoSidedLayout>
      </template>
    </TwoSidedLayout>
  </PageInnerLayout>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import moment from 'moment';

import PageInnerLayout from '@/layouts/PageInnerLayout.vue';
import TwoSidedLayout from '@/layouts/TwoSidedLayout.vue';
import TopBottomLayout from '@/layouts/TopBottomLayout.vue';
import PatientCompactPicker from '@/ui-cards/PatientCompactPicker.vue';
import ResearchesPicker from '@/ui-cards/ResearchesPicker.vue';
import useLoader from '@/hooks/useLoader';
import useNotify from '@/hooks/useNotify';
import api from '@/api';

import RequestFields from './RequestFields.vue';
import RequestHistory from './RequestHistory.vue';
import RequestImageBinding from './RequestImageBinding.vue';

const cardId = ref(null);
const research = ref(null);
const requestHistoryRef = ref();
const requestImageBindingRef = ref();
const isSelectionMode = ref(false);
const currentImageForLink = ref(null);
const hoveredRequestId = ref(null);
const hoveredImageId = ref(null);

const loader = useLoader();
const notify = useNotify();

const defaultRequestFields = () => ({
  date: moment().format('YYYY-MM-DD'),
  modality: '',
  anatomy: '',
  side: '',
  contrast: '',
  contrastAmount: '',
  dose: '',
  cito: false,
  anamnesis: '',
  comment: '',
  files: [] as any[],
});

const requestFields = ref(defaultRequestFields());

async function createRequest() {
  loader.inc();
  try {
    const files = requestFields.value.files || [];

    const { ok, message } = await api('requests/create', {
      patientId: cardId.value,
      researchId: research.value,
      requestFields: {
        ...requestFields.value,
        files,
      },
    });
    if (!ok) {
      notify.error(message);
    } else {
      notify.ok(message || 'Заявка успешно создана');
      requestFields.value = defaultRequestFields();

      if (requestHistoryRef.value?.refreshRequests) {
        await requestHistoryRef.value.refreshRequests();
      }
    }
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error(error);
    notify.error('Ошибка при создании заявки');
  } finally {
    loader.dec();
  }
}

const onImageLinked = (requestId: number | string) => {
  if (requestHistoryRef.value?.updateRequestImageStatus) {
    requestHistoryRef.value.updateRequestImageStatus(requestId, true);
  }
};

const onImageUnlinked = (requestId: number | string) => {
  if (requestHistoryRef.value?.updateRequestImageStatus) {
    requestHistoryRef.value.updateRequestImageStatus(requestId, false);
  }
};

const onRequestLinkNeeded = (image: any) => {
  if (requestHistoryRef.value?.enterSelectionMode) {
    isSelectionMode.value = true;
    currentImageForLink.value = image;
    requestHistoryRef.value.enterSelectionMode(image);
  }
};

const onRequestSelectedForLink = (request: any) => {
  if (requestHistoryRef.value?.currentImageForLink && requestImageBindingRef.value?.linkImageToRequest) {
    requestImageBindingRef.value.linkImageToRequest(requestHistoryRef.value.currentImageForLink, request);
    requestHistoryRef.value.exitSelectionMode();
    isSelectionMode.value = false;
    currentImageForLink.value = null;
  }
};

const onCancelSelection = () => {
  if (requestHistoryRef.value?.exitSelectionMode) {
    requestHistoryRef.value.exitSelectionMode();
    isSelectionMode.value = false;
    currentImageForLink.value = null;
  }
};

const onRequestHover = (request: any) => {
  if (request?.hasImage) {
    hoveredRequestId.value = request.id;
  } else {
    hoveredRequestId.value = null;
  }
};

const onImageHover = (image: any) => {
  if (image?.linked && image?.requestId) {
    hoveredImageId.value = image.requestId;
  } else {
    hoveredImageId.value = null;
  }
};

watch(cardId, () => {
  requestFields.value = defaultRequestFields();
});
</script>

<style scoped>
.selection-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.7);
  z-index: 1000;
  pointer-events: all;
}
</style>
