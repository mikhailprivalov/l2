<template>
  <div class="editor">
    <div class="content">
      <div class="form-box">
        <div class="input-group">
          <span class="input-group-addon">Название</span>
          <input
            v-model="title"
            type="text"
            class="form-control"
          >
        </div>
        <template v-if="kind === 'type'">
          <div class="input-group">
            <span class="input-group-addon">Группа</span>
            <select
              v-model.number="groupId"
              class="form-control"
            >
              <option :value="-1">
                Не выбрана
              </option>
              <option
                v-for="group in groups"
                :key="group.id"
                :value="group.id"
              >
                {{ group.title }}
              </option>
            </select>
          </div>
          <div class="input-group">
            <span class="input-group-addon">Код</span>
            <input
              v-model="code"
              type="text"
              class="form-control"
            >
          </div>
        </template>
      </div>
    </div>
    <div class="footer">
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
  getCurrentInstance, ref, watch,
} from 'vue';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';

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

const fill = () => {
  title.value = props.titleValue || '';
  code.value = props.codeValue || '';
  groupId.value = props.groupIdValue ?? -1;
};

watch(
  () => [props.itemId, props.titleValue, props.codeValue, props.groupIdValue],
  fill,
  { immediate: true },
);

const save = async () => {
  const endpoint = props.kind === 'group' ? 'document-manager/groups/update' : 'document-manager/types/update';
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api(endpoint, {
      id: props.itemId,
      title: title.value,
      code: code.value,
      groupId: groupId.value,
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
.editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #f8f7f7;
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.form-box {
  background-color: #fff;
  border: 1px solid #b1b1b1;
  padding: 8px;
}

.input-group {
  margin-bottom: 5px;
  display: flex;
  width: 100%;
}

.input-group:last-child {
  margin-bottom: 0;
}

.input-group-addon {
  display: flex;
  align-items: center;
  background-color: #AAB2BD;
  border: 1px solid #96a0ad;
  color: #FFF;
  min-width: 88px;
  padding: 6px 10px;
  line-height: 20px;
  white-space: nowrap;
  border-radius: 4px 0 0 4px;
}

.form-control {
  height: 34px;
  flex: 1;
  border-radius: 0 4px 4px 0;
  border-left: none;
}

.footer {
  flex: 0 0 34px;
  display: flex;
  justify-content: flex-end;
  background-color: #f4f4f4;
  border-top: 1px solid #b1b1b1;

  .btn {
    border-radius: 0;
    height: 34px;
  }
}
</style>
