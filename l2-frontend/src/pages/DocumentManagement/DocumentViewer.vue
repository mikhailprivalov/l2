<template>
  <div class="viewer-root">
    <div
      v-if="!documentId"
      class="empty"
    >
      Выберите документ
    </div>
    <div
      v-else
      class="results-content"
    >
      <div class="research-title">
        <div class="research-left">
          {{ title || '' }}
        </div>
        <div class="research-right">
          <button
            v-if="research && !confirmed"
            v-tippy
            class="btn btn-blue-nb"
            type="button"
            title="Сохранить без подтверждения"
            @click="save"
          >
            &nbsp;<i class="fa fa-save" />&nbsp;
          </button>
        </div>
      </div>
      <div class="group">
        <div class="fields">
          <div class="field">
            <div class="field-title">
              Служебный номер
            </div>
            <div class="field-value simple-value">
              {{ documentId }}
            </div>
          </div>
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
        :key="`${documentId}-${issPk}-${confirmed}`"
        :research="research"
        :confirmed="confirmed"
        :patient="patient"
        :pk="issPk"
      />
      <div
        v-if="research"
        class="control-row"
      >
        <div class="res-title">
          {{ title }}:
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
          Сохранить и подтвердить
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
  </div>
</template>

<script setup lang="ts">
import {
  getCurrentInstance, ref, watch,
} from 'vue';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';
import { buildParaclinicResultFormData } from '@/api/buildParaclinicResultFormData';
import { vField, vGroup } from '@/components/visibility-triggers';
import DescriptiveForm from '@/forms/DescriptiveForm.vue';

const props = defineProps<{
  documentId?: number | null;
}>();

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const title = ref('');
const research = ref(null);
const issPk = ref<number | null>(null);
const loaded = ref(false);
const confirmed = ref(false);
const patient = {};

const visibilityState = () => {
  const groups = {};
  const fields = {};
  const igroups = research.value?.groups || [];
  for (const group of igroups) {
    if (!vGroup(group, igroups, patient)) {
      groups[group.pk] = false;
    } else {
      groups[group.pk] = true;
      for (const field of group.fields || []) {
        fields[field.pk] = vField(group, igroups, field.visibility, patient);
      }
    }
  }
  return { groups, fields };
};

const applyFilesByField = (filesByField) => {
  if (!filesByField || !research.value?.groups) {
    return;
  }
  for (const group of research.value.groups) {
    for (const field of group.fields || []) {
      if (field.field_type === 42 && filesByField[field.pk]) {
        field.files = filesByField[field.pk];
      }
    }
  }
};

const savePayload = (withConfirm: boolean) => ({
  data: {
    pk: issPk.value,
    research: research.value,
  },
  with_confirm: withConfirm,
  visibility_state: visibilityState(),
});

const saveRequest = async (payload) => {
  const { jsonPayload, formData } = buildParaclinicResultFormData(payload);
  if (formData) {
    return api('document-manager/documents/save', null, null, jsonPayload, formData);
  }
  return api('document-manager/documents/save', payload);
};

const load = async () => {
  title.value = '';
  research.value = null;
  issPk.value = null;
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
      issPk.value = result.issPk || null;
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
  if (!props.documentId || !research.value || !issPk.value) {
    return false;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await saveRequest(savePayload(false));
    if (result?.ok) {
      applyFilesByField(result.files_by_field);
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
  if (!props.documentId || !research.value || !issPk.value) {
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await saveRequest(savePayload(true));
    if (result?.ok) {
      applyFilesByField(result.files_by_field);
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
  overflow: hidden;
  background: #fff;
}

.results-content {
  flex: 1 1 0;
  min-height: 0;
  overflow-y: auto;
}

.research-title {
  position: sticky;
  top: 0;
  background-color: #ddd;
  text-align: center;
  padding: 5px;
  font-weight: bold;
  z-index: 4;
  display: flex;
}

.research-left {
  position: relative;
  text-align: left;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.research-right {
  text-align: right;
  flex: 0 0 auto;
  margin-top: -5px;
  margin-right: -5px;
  margin-bottom: -5px;
  white-space: nowrap;

  .btn {
    border-radius: 0;
    padding: 5px 4px;
  }
}

.empty {
  padding: 16px 10px;
  color: #656d78;
}

.simple-value {
  padding: 5px;
}

.control-row {
  height: 34px;
  background-color: #f3f3f3;
  display: flex;
  flex-direction: row;
  margin-bottom: 10px;

  button {
    align-self: stretch;
    border-radius: 0;
  }

  div {
    align-self: stretch;
  }
}

.res-title {
  flex: 1;
  padding: 5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
