<template>
  <div class="viewer-root">
    <div class="filters-panel document-panel">
      <span class="document-title">{{ title || '' }}</span>
    </div>
    <div class="document-body">
      <div
        v-if="!documentId"
        class="empty"
      >
        Выберите документ
      </div>
      <template v-else>
        <div class="service-number field">
          <div class="field-title">
            Служебный номер
          </div>
          <div class="field-value simple-value">
            {{ documentId }}
          </div>
        </div>
        <div
          v-if="loaded && !research"
          class="empty"
        >
          У вида не выбран шаблон
        </div>
        <DescriptiveForm
          v-else-if="research"
          :key="`${documentId}-${confirmed}`"
          :research="research"
          :confirmed="confirmed"
          :patient="patient"
          :pk="documentId"
        />
      </template>
    </div>
    <div
      v-if="research"
      class="control-row"
    >
      <div class="res-title">
        {{ title }}
      </div>
      <button
        v-if="!confirmed"
        class="btn btn-blue-nb"
        type="button"
        @click="save"
      >
        Сохранить
      </button>
      <button
        v-if="!confirmed"
        class="btn btn-blue-nb"
        type="button"
        @click="confirm"
      >
        Подтвердить
      </button>
      <button
        v-if="confirmed"
        class="btn btn-blue-nb"
        type="button"
        @click="resetConfirm"
      >
        Сброс подтверждения
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  getCurrentInstance, ref, watch,
} from 'vue';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';
import DescriptiveForm from '@/forms/DescriptiveForm.vue';

const props = defineProps<{
  documentId?: number | null;
}>();

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const title = ref('');
const research = ref(null);
const loaded = ref(false);
const confirmed = ref(false);
const patient = {};

const groupsPayload = () => (research.value?.groups || []).map(group => ({
  pk: group.pk,
  fields: (group.fields || []).map(field => ({
    pk: field.pk,
    value: field.value,
  })),
}));

const load = async () => {
  title.value = '';
  research.value = null;
  loaded.value = false;
  confirmed.value = false;
  if (!props.documentId) {
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/documents/details', { id: props.documentId });
    if (result?.ok) {
      title.value = result.title || '';
      research.value = result.research || null;
      confirmed.value = Boolean(result.confirmed);
    } else {
      root.$emit('msg', 'error', result?.message || 'Ошибка загрузки');
    }
  } finally {
    loaded.value = true;
    await store.dispatch(actions.DEC_LOADING);
  }
};

const save = async () => {
  if (!props.documentId || !research.value) {
    return false;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/documents/save', {
      id: props.documentId,
      groups: groupsPayload(),
    });
    if (result?.ok) {
      root.$emit('msg', 'ok', 'Сохранено');
      return true;
    }
    root.$emit('msg', 'error', result?.message || 'Ошибка сохранения');
    return false;
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const confirm = async () => {
  if (!props.documentId || !research.value) {
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/documents/confirm', {
      id: props.documentId,
      groups: groupsPayload(),
    });
    if (result?.ok) {
      confirmed.value = true;
      root.$emit('msg', 'ok', 'Подтверждено');
    } else {
      root.$emit('msg', 'error', result?.message || 'Ошибка подтверждения');
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const resetConfirm = async () => {
  if (!props.documentId) {
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/documents/confirm-reset', { id: props.documentId });
    if (result?.ok) {
      confirmed.value = false;
      root.$emit('msg', 'ok', 'Подтверждение сброшено');
    } else {
      root.$emit('msg', 'error', result?.message || 'Ошибка сброса');
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

watch(() => props.documentId, load, { immediate: true });
</script>

<style scoped lang="scss">
.viewer-root {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.filters-panel {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  background-color: #f8f7f7;
}

.document-panel {
  flex: 0 0 34px;
  height: 34px;
  border-top: 1px solid #b1b1b1;
  border-bottom: 1px solid #b1b1b1;
}

.document-title {
  flex: 1;
  display: flex;
  align-items: center;
  padding: 0 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.document-body {
  flex: 1 1 0;
  min-height: 0;
  overflow-y: auto;
  background: #fff;
}

.service-number {
  padding: 5px 5px 5px 10px;
  border-bottom: 1px solid #eaeaea;
}

.simple-value {
  padding: 5px;
}

.empty {
  padding: 16px 10px;
  color: #656d78;
}

.control-row {
  flex: 0 0 34px;
  height: 34px;
  background-color: #f3f3f3;
  display: flex;
  flex-direction: row;
  border-top: 1px solid #b1b1b1;

  button {
    align-self: stretch;
    border-radius: 0;
  }
}

.res-title {
  flex: 1;
  padding: 5px 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
