<template>
  <div class="root">
    <div class="top-editor oneLine">
      <div class="left">
        <div class="input-group">
          <span class="input-group-addon">Название</span>
          <input
            v-model="title"
            type="text"
            class="form-control"
          >
          <template v-if="kind === 'type'">
            <span class="input-group-addon">Короткое</span>
            <input
              v-model="code"
              type="text"
              class="form-control"
            >
            <span class="input-group-addon">Группа</span>
            <select
              v-model.number="groupId"
              class="form-control"
            >
              <option :value="-1">
                Не выбрана
              </option>
              <option
                v-for="group in groups || []"
                :key="group.id"
                :value="group.id"
              >
                {{ group.title }}
              </option>
            </select>
          </template>
        </div>
      </div>
    </div>
    <div class="content-editor">
      <div
        v-if="kind === 'type'"
        class="template-row"
      >
        <span class="input-group-addon">Шаблон документа</span>
        <Treeselect
          v-model="layoutTemplateId"
          class="treeselect-wide treeselect-34px template-select"
          :multiple="false"
          :disable-branch-nodes="true"
          :options="layoutTemplates"
          placeholder="Шаблон не выбран"
          :append-to-body="true"
          :clearable="true"
        />
      </div>
    </div>
    <div class="footer-editor">
      <button
        class="btn btn-blue-nb"
        type="button"
        @click="$emit('cancel')"
      >
        Отмена
      </button>
      <button
        class="btn btn-blue-nb"
        type="button"
        :disabled="!title.trim()"
        @click="save"
      >
        Сохранить
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  getCurrentInstance, onMounted, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

interface CatalogGroup {
  id: number;
  title: string;
}

const props = defineProps<{
  kind: 'group' | 'type';
  itemId: number;
  titleValue?: string;
  codeValue?: string;
  groupIdValue?: number | null;
  layoutTemplateIdValue?: number | null;
  groups?: CatalogGroup[];
}>();

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'saved', payload: { id: number }): void;
  (e: 'cancel'): void;
}>();

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const title = ref('');
const code = ref('');
const groupId = ref<number>(-1);
const layoutTemplateId = ref<number | null>(null);
const layoutTemplates = ref<{ id: number; label: string }[]>([]);

const fill = () => {
  title.value = props.titleValue || '';
  code.value = props.codeValue || '';
  groupId.value = props.groupIdValue ?? -1;
  layoutTemplateId.value = props.layoutTemplateIdValue ?? null;
};

watch(
  () => [props.itemId, props.titleValue, props.codeValue, props.groupIdValue, props.layoutTemplateIdValue],
  fill,
  { immediate: true },
);

const loadLayoutTemplates = async () => {
  if (props.kind !== 'type') {
    return;
  }
  const { rows } = await api('layout-template/list-treeselect', { pk: -1 });
  layoutTemplates.value = rows || [];
};

onMounted(loadLayoutTemplates);

const save = async () => {
  const endpoint = props.kind === 'group' ? 'document-manager/groups/update' : 'document-manager/types/update';
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api(endpoint, {
      id: props.itemId,
      title: title.value,
      code: code.value,
      groupId: groupId.value,
      layoutTemplateId: layoutTemplateId.value,
    });
    if (result?.ok) {
      root.$emit('msg', 'ok', 'Сохранено');
      emit('saved', { id: result.id });
    } else {
      root.$emit('msg', 'error', result?.message || 'Ошибка сохранения');
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};
</script>

<style scoped lang="scss">
.root {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  height: 100%;
  background-color: #f8f7f7;
}

.top-editor {
  display: flex;
  flex: 0 0 34px;
  align-self: stretch;
  width: 100%;
  min-width: 0;
  height: 34px;
  border-bottom: 1px solid #b1b1b1;

  .left {
    flex: 1 1 auto;
    width: 100%;
    min-width: 0;
  }

  .input-group {
    display: flex !important;
    flex-wrap: nowrap;
    align-items: stretch;
    width: 100%;
    margin-bottom: 0;
    height: 34px;
  }

  .input-group-addon {
    display: flex !important;
    align-items: center;
    flex: 0 0 auto;
    float: none !important;
    width: auto;
    height: 34px;
    padding: 0 10px;
    line-height: 22px;
    font-size: 14px;
    font-weight: normal;
    color: #FFF;
    white-space: nowrap;
    background-color: #aab2bd;
    border-top: none;
    border-left: none;
    border-right: 1px solid #aab2bd;
    border-bottom: none;
    border-radius: 0 !important;
  }

  .form-control {
    flex: 1 1 0;
    float: none !important;
    width: auto !important;
    min-width: 0;
    height: 34px;
    padding: 0 10px;
    line-height: 22px;
    font-size: 14px;
    color: #434A54;
    border-top: none;
    border-bottom: none;
    border-radius: 0 !important;
    display: block !important;
    box-shadow: none;
  }

  .input-group > .form-control:last-child {
    border-right: none;
  }
}

.content-editor {
  flex: 1;
  min-height: 0;
  align-self: stretch;
}

.template-row {
  display: flex;
  align-items: stretch;
  height: 34px;
  border-bottom: 1px solid #b1b1b1;

  .input-group-addon {
    display: flex;
    align-items: center;
    flex: 0 0 auto;
    flex-shrink: 0;
    width: auto !important;
    height: 34px;
    padding: 0 10px;
    line-height: 22px;
    font-size: 14px;
    font-weight: normal;
    color: #FFF;
    white-space: nowrap;
    background-color: #aab2bd;
    border: none;
    border-right: 1px solid #aab2bd;
    border-radius: 0 !important;
  }
}

.template-select {
  flex: 1 1 0;
  min-width: 0;
}

:deep(.template-select .vue-treeselect__control) {
  height: 34px;
  border: none;
  border-radius: 0;
}

.footer-editor {
  flex: 0 0 34px;
  display: flex;
  justify-content: flex-end;
  align-self: stretch;
  background-color: #f4f4f4;
  border-top: 1px solid #b1b1b1;

  .btn {
    border-radius: 0 !important;
    height: 34px;
    padding: 0 10px;
    line-height: 22px;
    font-size: 14px;
  }
}
</style>
