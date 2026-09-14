<template>
  <div class="root">
    <div class="top-editor">
      <div class="field-slot">
        <span class="input-group-addon">Название</span>
        <input
          v-model="title"
          type="text"
          class="form-control"
        >
      </div>
      <label class="hide-slot">
        <input
          v-model="hide"
          type="checkbox"
        >
        Скрыт
      </label>
    </div>
    <div class="content-editor">
      <div class="search-row">
        <input
          v-model="query"
          type="text"
          class="form-control"
          placeholder="Найти сотрудника и добавить"
        >
      </div>
      <div class="found-list">
        <button
          v-for="row in found"
          :key="row.id"
          class="found-row"
          type="button"
          :disabled="members.some(item => item.id === row.id)"
          @click="addMember(row)"
        >
          {{ row.fio }}
          <span
            v-if="row.department"
            class="dep"
          >{{ row.department }}</span>
        </button>
      </div>
      <div class="members-title">
        Сотрудники набора
      </div>
      <div class="members-list">
        <div
          v-if="members.length === 0"
          class="empty"
        >
          Набор пуст
        </div>
        <div
          v-for="row in members"
          :key="row.id"
          class="member-row"
        >
          <span>{{ row.fio }}</span>
          <button
            class="btn btn-blue-nb"
            type="button"
            title="Удалить"
            @click="removeMember(row.id)"
          >
            <i class="glyphicon glyphicon-remove" />
          </button>
        </div>
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
import debounce from 'lodash/debounce';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';

type Employee = {
  id: number;
  fio: string;
  department?: string;
};

const props = defineProps<{
  itemId: number;
}>();

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'saved', payload: { id: number }): void;
  (e: 'cancel'): void;
}>();

const store = useStore();
const root = getCurrentInstance().proxy.$root;
const title = ref('');
const hide = ref(false);
const members = ref<Employee[]>([]);
const query = ref('');
const found = ref<Employee[]>([]);

const loadDetails = async () => {
  title.value = '';
  hide.value = false;
  members.value = [];
  if (!props.itemId || props.itemId < 1) {
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/addressees/groups/details', { id: props.itemId });
    if (result?.ok) {
      title.value = result.title || '';
      hide.value = Boolean(result.hide);
      members.value = result.members || [];
    } else {
      root.$emit('msg', 'error', result?.message || 'Ошибка загрузки');
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const searchEmployees = async () => {
  if (!query.value.trim()) {
    found.value = [];
    return;
  }
  const { result } = await api('document-manager/addressees/employees', {
    groupId: 0,
    query: query.value,
  });
  found.value = result || [];
};

const debouncedSearch = debounce(searchEmployees, 250);

const addMember = (row: Employee) => {
  if (members.value.some(item => item.id === row.id)) {
    return;
  }
  members.value = [...members.value, row];
};

const removeMember = (id: number) => {
  members.value = members.value.filter(row => row.id !== id);
};

const save = async () => {
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/addressees/groups/update', {
      id: props.itemId,
      title: title.value,
      hide: hide.value,
      memberIds: members.value.map(row => row.id),
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

watch(() => props.itemId, loadDetails);
watch(query, debouncedSearch);

onMounted(loadDetails);
</script>

<style scoped lang="scss">
.root {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #f8f7f7;
}

.top-editor {
  display: flex;
  flex: 0 0 34px;
  align-items: stretch;
  border-bottom: 1px solid #b1b1b1;
}

.field-slot {
  display: flex;
  flex: 1;
  min-width: 0;
}

.input-group-addon {
  display: flex;
  align-items: center;
  padding: 0 10px;
  background: #eee;
  border-right: 1px solid #b1b1b1;
  white-space: nowrap;
}

.form-control {
  border: none;
  box-shadow: none;
  height: 34px;
  border-radius: 0;
}

.hide-slot {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 10px;
  margin: 0;
  font-weight: normal;
  white-space: nowrap;
}

.content-editor {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 8px 10px;
  gap: 8px;
}

.search-row .form-control {
  border: 1px solid #ccc;
  height: 34px;
}

.found-list,
.members-list {
  overflow-y: auto;
  min-height: 0;
}

.found-list {
  max-height: 140px;
  border: 1px solid #ddd;
  background: #fff;
}

.found-row,
.member-row {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-height: 34px;
  padding: 0 8px;
  border: none;
  border-bottom: 1px solid #eee;
  background: transparent;
  text-align: left;
}

.found-row {
  cursor: pointer;
}

.found-row:disabled {
  opacity: 0.5;
  cursor: default;
}

.dep {
  margin-left: auto;
  color: #888;
  font-size: 12px;
}

.members-title {
  font-weight: 600;
}

.members-list {
  flex: 1;
  background: #fff;
  border: 1px solid #ddd;
}

.member-row .btn {
  margin-left: auto;
  border-radius: 0;
}

.empty {
  padding: 12px;
  color: #888;
}

.footer-editor {
  display: flex;
  gap: 0;
  flex: 0 0 34px;
  border-top: 1px solid #b1b1b1;

  .btn {
    border-radius: 0;
  }
}
</style>
