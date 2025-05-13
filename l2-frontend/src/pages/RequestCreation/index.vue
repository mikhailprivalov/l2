<template>
  <PageInnerLayout>
    <TwoSidedLayout :left-width-px="800">
      <template #left>
        <TopBottomLayout :top-height-px="300">
          <template #top>
            <PatientCompactPicker
              v-model="cardId"
              :title-for-base="'Пациент'"
            >
              <template #for_card>
                <PatientExtraFields v-model="patientExtraFields" />
              </template>
            </PatientCompactPicker>
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
      </template>
      <template #right>
        <TwoSidedLayout :left-width-px="300">
          <template #left>
            <RequestHistory :card-id="cardId" />
          </template>
          <template #right>
            <RequestImageBinding />
          </template>
        </TwoSidedLayout>
      </template>
    </TwoSidedLayout>
  </PageInnerLayout>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

import PageInnerLayout from '@/layouts/PageInnerLayout.vue';
import TwoSidedLayout from '@/layouts/TwoSidedLayout.vue';
import TopBottomLayout from '@/layouts/TopBottomLayout.vue';
import PatientCompactPicker from '@/ui-cards/PatientCompactPicker.vue';
import ResearchesPicker from '@/ui-cards/ResearchesPicker.vue';
import useLoader from '@/hooks/useLoader';
import useNotify from '@/hooks/useNotify';
import api from '@/api';

import PatientExtraFields from './PatientExtraFields.vue';
import RequestFields from './RequestFields.vue';
import RequestHistory from './RequestHistory.vue';
import RequestImageBinding from './RequestImageBinding.vue';

const cardId = ref(null);
const research = ref(null);

const loader = useLoader();
const notify = useNotify();

const defaultPatientExtraFields = () => ({ clinic: '' });
const defaultRequestFields = () => ({
  date: '',
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

const patientExtraFields = ref(defaultPatientExtraFields());
const requestFields = ref(defaultRequestFields());

const fileSizeToString = (size: number) => {
  if (size < 1024) {
    return `${size} байт`;
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} Кб`;
  }
  return `${(size / 1024 / 1024).toFixed(1)} Мб`;
};

function processFile(file: File) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      resolve({
        name: file.name,
        size: fileSizeToString(file.size),
        url: e.target?.result,
      });
    };
    reader.readAsDataURL(file);
  });
}

async function createRequest() {
  loader.inc();
  try {
    const files: any[] = [];

    // @ts-ignore
    for (const { file } of requestFields.value.files.files) {
      files.push(await processFile(file));
    }

    const { ok, message } = await api('requests/create', {
      patientId: cardId.value,
      researchId: research.value,
      requestFields: {
        ...requestFields.value,
        files,
      },
      patientExtraFields: patientExtraFields.value,
    });
    if (!ok) {
      notify.error(message);
    } else {
      notify.ok(message || 'Заявка успешно создана');
    }
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error(error);
    notify.error('Ошибка при создании заявки');
  } finally {
    loader.dec();
  }
}

watch(cardId, () => {
  patientExtraFields.value = defaultPatientExtraFields();
  requestFields.value = defaultRequestFields();
});
</script>
