<template>
  <div
    class="addressee-field"
    :class="{ 'addressee-field--button-only': hidePreview }"
  >
    <div
      v-if="!hidePreview"
      class="addressee-field__preview"
    >
      {{ preview || 'Не выбрано' }}
    </div>
    <button
      v-if="!disabled"
      class="btn btn-blue-nb addressee-field__btn"
      type="button"
      @click="openModal"
    >
      Выбрать
    </button>
    <Modal
      v-if="opened"
      show-footer="true"
      white-bg="true"
      width="920px"
      max-width="96vw"
      height="560px"
      margin-left-right="auto"
      @close="opened = false"
    >
      <span slot="header">{{ header }}</span>
      <div
        slot="body"
        class="addressee-modal"
      >
        <div class="addressee-modal__groups">
          <div
            v-for="group in groups"
            :key="group.id"
            class="addressee-modal__group-row"
          >
            <button
              class="addressee-modal__group"
              :class="{ 'addressee-modal__group--active': selectedGroupId === group.id }"
              type="button"
              @click="selectGroup(group.id)"
            >
              {{ group.title }}
            </button>
            <button
              v-if="group.own"
              class="addressee-modal__group-del"
              type="button"
              title="Удалить набор"
              @click="deletePersonalSet(group)"
            >
              &times;
            </button>
          </div>
        </div>
        <div class="addressee-modal__list">
          <input
            v-model="query"
            type="text"
            class="form-control"
            placeholder="Поиск по ФИО"
          >
          <label class="addressee-modal__select-all">
            <input
              ref="selectAllEl"
              type="checkbox"
              :checked="allLoadedSelected"
              :disabled="isTogglingAll || (employees.length === 0 && !hasMore)"
              @change="toggleSelectAll"
            >
            Выделить все
          </label>
          <div
            ref="rowsEl"
            class="addressee-modal__rows"
            @scroll="onRowsScroll"
          >
            <label
              v-for="row in employees"
              :key="row.id"
              class="addressee-modal__row"
            >
              <input
                type="checkbox"
                :checked="isSelected(row.id)"
                @change="toggleEmployee(row)"
              >
              <span>{{ row.fio }}</span>
              <span
                v-if="row.department"
                class="addressee-modal__dep"
              >{{ row.department }}</span>
            </label>
            <div
              v-if="isLoadingMore"
              class="addressee-modal__empty"
            >
              Загрузка...
            </div>
            <div
              v-else-if="employees.length === 0"
              class="addressee-modal__empty"
            >
              Нет сотрудников
            </div>
          </div>
        </div>
        <div class="addressee-modal__selected">
          <div class="addressee-modal__selected-title">
            Выбрано: {{ draft.length }}
          </div>
          <div class="addressee-modal__save-set">
            <input
              v-model="newSetTitle"
              type="text"
              class="form-control"
              placeholder="Название набора"
            >
            <button
              class="btn btn-blue-nb"
              type="button"
              :disabled="!draft.length || !newSetTitle.trim() || isSavingSet"
              @click="savePersonalSet"
            >
              Сохранить набор
            </button>
          </div>
          <div
            v-for="row in draft"
            :key="row.id"
            class="addressee-modal__picked"
          >
            <span>{{ row.fio }}</span>
            <button
              type="button"
              class="addressee-modal__remove"
              title="Убрать"
              @click="removeEmployee(row.id)"
            >
              &times;
            </button>
          </div>
        </div>
      </div>
      <div
        slot="footer"
        class="addressee-modal__footer"
      >
        <button
          class="btn btn-blue-nb"
          type="button"
          :disabled="selectedGroupId === 0"
          @click="addCurrentSet"
        >
          Добавить набор
        </button>
        <button
          class="btn btn-blue-nb"
          type="button"
          @click="apply"
        >
          Готово
        </button>
        <button
          class="btn btn-blue-nb"
          type="button"
          @click="opened = false"
        >
          Отмена
        </button>
      </div>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import {
  computed, nextTick, ref, watch,
} from 'vue';
import debounce from 'lodash/debounce';

import api from '@/api';
import Modal from '@/ui-cards/Modal.vue';

type Employee = {
  id: number;
  fio: string;
  department?: string;
};

type Group = {
  id: number;
  title: string;
  own?: boolean;
};

const props = withDefaults(defineProps<{
  value?: string;
  disabled?: boolean;
  header?: string;
  hidePreview?: boolean;
}>(), {
  header: 'Адресаты',
  hidePreview: false,
});

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'input', value: string): void;
}>();

const opened = ref(false);
const groups = ref<Group[]>([]);
const selectedGroupId = ref(0);
const query = ref('');
const employees = ref<Employee[]>([]);
const draft = ref<Employee[]>([]);
const newSetTitle = ref('');
const page = ref(1);
const hasMore = ref(false);
const isLoading = ref(false);
const isLoadingMore = ref(false);
const isTogglingAll = ref(false);
const isSavingSet = ref(false);
const allMatchingSelected = ref(false);
const rowsEl = ref<HTMLElement | null>(null);
const selectAllEl = ref<HTMLInputElement | null>(null);
const PAGE_SIZE = 100;

const parseValue = (raw?: string): Employee[] => {
  if (!raw) {
    return [];
  }
  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed
      .map((item) => {
        if (!item || typeof item !== 'object') {
          return null;
        }
        const id = Number(item.id);
        if (!id) {
          return null;
        }
        return { id, fio: item.fio || '', department: item.department || '' };
      })
      .filter(Boolean) as Employee[];
  } catch {
    return [];
  }
};

const preview = computed(() => parseValue(props.value).map(row => row.fio).filter(Boolean).join(', '));

const isSelected = (id: number) => draft.value.some(row => row.id === id);

const allLoadedSelected = computed(() => {
  if (allMatchingSelected.value) {
    return true;
  }
  return employees.value.length > 0 && !hasMore.value && employees.value.every(row => isSelected(row.id));
});

const someLoadedSelected = computed(
  () => employees.value.some(row => isSelected(row.id)),
);

const mergeEmployees = (incoming: Employee[]) => {
  const byId = new Map(draft.value.map(row => [row.id, row]));
  for (const row of incoming) {
    byId.set(row.id, row);
  }
  draft.value = Array.from(byId.values());
};

const loadAllEmployees = async (groupId = selectedGroupId.value, search = query.value) => {
  const data = await api('document-manager/addressees/employees', {
    groupId,
    query: search,
    all: true,
  });
  return (data.result || []) as Employee[];
};

const toggleEmployee = (row: Employee) => {
  if (isSelected(row.id)) {
    allMatchingSelected.value = false;
    draft.value = draft.value.filter(item => item.id !== row.id);
    return;
  }
  draft.value = [...draft.value, { id: row.id, fio: row.fio, department: row.department }];
};

const removeEmployee = (id: number) => {
  allMatchingSelected.value = false;
  draft.value = draft.value.filter(row => row.id !== id);
};

const toggleSelectAll = async (event: Event) => {
  const { checked } = event.target as HTMLInputElement;
  isTogglingAll.value = true;
  try {
    const rows = (hasMore.value || employees.value.length === 0)
      ? await loadAllEmployees()
      : employees.value;
    if (!checked) {
      allMatchingSelected.value = false;
      const removeIds = new Set(rows.map(row => row.id));
      draft.value = draft.value.filter(item => !removeIds.has(item.id));
      return;
    }
    mergeEmployees(rows);
    allMatchingSelected.value = rows.length > 0;
  } finally {
    isTogglingAll.value = false;
  }
};

const loadEmployees = async (append = false) => {
  if (append) {
    if (!hasMore.value || isLoadingMore.value || isLoading.value) {
      return;
    }
    isLoadingMore.value = true;
  } else {
    isLoading.value = true;
    page.value = 1;
    hasMore.value = false;
  }
  try {
    const nextPage = append ? page.value + 1 : 1;
    const data = await api('document-manager/addressees/employees', {
      groupId: selectedGroupId.value,
      query: query.value,
      page: nextPage,
      pageSize: PAGE_SIZE,
    });
    const rows = data.result || [];
    page.value = data.page || nextPage;
    hasMore.value = Boolean(data.hasMore);
    employees.value = append ? [...employees.value, ...rows] : rows;
  } finally {
    isLoading.value = false;
    isLoadingMore.value = false;
  }
};

const onRowsScroll = () => {
  const el = rowsEl.value;
  if (!el || !hasMore.value || isLoadingMore.value) {
    return;
  }
  if (el.scrollHeight - el.scrollTop - el.clientHeight < 80) {
    loadEmployees(true);
  }
};

const debouncedLoad = debounce(() => loadEmployees(false), 250);

const selectGroup = (id: number) => {
  selectedGroupId.value = id;
  allMatchingSelected.value = false;
  loadEmployees(false);
};

const reloadGroups = async () => {
  const { result } = await api('document-manager/addressees/groups/list', { includeAll: true, includeHidden: false });
  groups.value = result || [];
};

const openModal = async () => {
  draft.value = parseValue(props.value);
  query.value = '';
  newSetTitle.value = '';
  allMatchingSelected.value = false;
  employees.value = [];
  opened.value = true;
  await reloadGroups();
  selectedGroupId.value = groups.value[0] ? groups.value[0].id : -1;
  await loadEmployees(false);
};

const addCurrentSet = async () => {
  if (selectedGroupId.value <= 0) {
    return;
  }
  const incoming = await loadAllEmployees(selectedGroupId.value, '');
  mergeEmployees(incoming);
};

const savePersonalSet = async () => {
  const title = newSetTitle.value.trim();
  if (!title || !draft.value.length || isSavingSet.value) {
    return;
  }
  isSavingSet.value = true;
  try {
    const result = await api('document-manager/addressees/groups/save-personal', {
      title,
      memberIds: draft.value.map(row => row.id),
    });
    if (result?.ok) {
      newSetTitle.value = '';
      await reloadGroups();
      if (result.id) {
        selectedGroupId.value = result.id;
        await loadEmployees(false);
      }
    }
  } finally {
    isSavingSet.value = false;
  }
};

const deletePersonalSet = async (group: Group) => {
  if (!group.own) {
    return;
  }
  if (!window.confirm(`Удалить набор «${group.title}»?`)) {
    return;
  }
  const result = await api('document-manager/addressees/groups/delete', { id: group.id });
  if (!result?.ok) {
    return;
  }
  groups.value = groups.value.filter(row => row.id !== group.id);
  if (selectedGroupId.value === group.id) {
    selectedGroupId.value = 0;
    await loadEmployees(false);
  }
};

const apply = () => {
  emit('input', JSON.stringify(draft.value.map(row => ({ id: row.id, fio: row.fio }))));
  opened.value = false;
};

watch(query, () => {
  if (opened.value) {
    allMatchingSelected.value = false;
    debouncedLoad();
  }
});

watch([allLoadedSelected, someLoadedSelected, employees, draft], async () => {
  await nextTick();
  if (selectAllEl.value) {
    selectAllEl.value.indeterminate = someLoadedSelected.value && !allLoadedSelected.value;
  }
});
</script>

<style scoped lang="scss">
.addressee-field {
  display: flex;
  align-items: stretch;
  gap: 0;
  min-height: 34px;
}

.addressee-field__preview {
  flex: 1;
  min-width: 0;
  padding: 6px 8px;
  background: #fff;
  border: 1px solid #ccc;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.addressee-field__btn {
  border-radius: 0;
  flex: 0 0 auto;
}

.addressee-field--button-only {
  flex: 1 1 0;
  min-width: 0;
}

.addressee-field--button-only .addressee-field__btn {
  flex: 1 1 0;
  height: 34px;
}

.addressee-modal {
  display: grid;
  grid-template-columns: 180px 1fr 220px;
  gap: 8px;
  height: 430px;
  min-height: 0;
}

.addressee-modal__groups,
.addressee-modal__rows,
.addressee-modal__selected {
  overflow-y: auto;
  min-height: 0;
}

.addressee-modal__groups {
  border-right: 1px solid #ddd;
  padding-right: 6px;
}

.addressee-modal__group-row {
  display: flex;
  align-items: stretch;
}

.addressee-modal__group {
  display: block;
  width: 100%;
  text-align: left;
  border: none;
  background: transparent;
  padding: 6px 8px;
  cursor: pointer;
}

.addressee-modal__group-row .addressee-modal__group {
  flex: 1;
  min-width: 0;
}

.addressee-modal__group-del {
  flex: 0 0 24px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
}

.addressee-modal__group--active,
.addressee-modal__group:hover {
  background: #049372;
  color: #fff;
}

.addressee-modal__list {
  display: flex;
  flex-direction: column;
  min-height: 0;
  gap: 6px;
}

.addressee-modal__select-all {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  font-weight: normal;
  cursor: pointer;
}

.addressee-modal__rows {
  flex: 1;
}

.addressee-modal__row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
  font-weight: normal;
  cursor: pointer;
}

.addressee-modal__dep {
  margin-left: auto;
  color: #888;
  font-size: 12px;
}

.addressee-modal__empty {
  padding: 12px 0;
  color: #888;
}

.addressee-modal__selected {
  border-left: 1px solid #ddd;
  padding-left: 8px;
}

.addressee-modal__selected-title {
  font-weight: 600;
  margin-bottom: 6px;
}

.addressee-modal__save-set {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 8px;
}

.addressee-modal__picked {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
}

.addressee-modal__remove {
  margin-left: auto;
  border: none;
  background: transparent;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
}

.addressee-modal__footer {
  display: flex;
  gap: 6px;
}
</style>
