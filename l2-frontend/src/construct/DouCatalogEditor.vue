<template>
  <div class="root">
    <div
      class="top-editor"
      :class="{ oneLine: kind === 'group' }"
    >
      <div class="left">
        <div class="input-group">
          <span class="input-group-addon">Название</span>
          <input
            v-model="title"
            type="text"
            class="form-control"
          >
        </div>
        <div
          v-if="kind === 'type'"
          class="input-group"
        >
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
        </div>
      </div>
    </div>
    <div class="content-editor" />
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
.root {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  height: 100%;
  background-color: #f8f7f7;
}

.top-editor {
  display: flex;
  flex: 0 0 68px;
  align-self: stretch;

  &.oneLine {
    flex: 0 0 34px;
  }

  .left {
    flex: 0 0 45%;
    border-right: 1px solid #96a0ad;
  }

  .input-group {
    margin-bottom: 0;
  }

  .input-group-addon {
    border-top: none;
    border-left: none;
    border-right: none;
    border-radius: 0;
  }

  .form-control {
    height: 34px;
    border-top: none;
    border-radius: 0;
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

.footer-editor {
  flex: 0 0 34px;
  display: flex;
  justify-content: flex-end;
  align-self: stretch;
  background-color: #f4f4f4;
  border-top: 1px solid #b1b1b1;

  .btn {
    border-radius: 0;
    height: 34px;
  }
}
</style>
