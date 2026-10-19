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
      width="1200px"
      max-width="96vw"
      height="620px"
      margin-left-right="auto"
      @close="opened = false"
    >
      <span slot="header">{{ header }}</span>
      <div
        slot="body"
        class="addressee-modal-wrap"
      >
        <Treeselect
          class="treeselect-wide treeselect-34px addressee-modal__hospital"
          :multiple="false"
          :options="hospitalOptions"
          :append-to-body="true"
          :clearable="false"
          :value="hospitalId"
          :z-index="5001"
          placeholder="Организация"
          no-results-text="Не найдено"
          no-options-text="Нет организаций"
          @input="onHospitalInput"
        />
        <div class="addressee-modal">
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
          <div
            class="addressee-modal__columns"
            :class="{ 'addressee-modal__columns--split': showSetSplit }"
          >
            <div
              v-if="showSetSplit"
              class="addressee-modal__col"
            >
              <div class="addressee-modal__col-title">
                Все
              </div>
              <div
                ref="allRowsEl"
                class="addressee-modal__rows"
                @scroll="onAllRowsScroll"
              >
                <div
                  v-for="row in allEmployees"
                  :key="row.id"
                  class="addressee-modal__row"
                >
                  <span class="addressee-modal__fio">{{ row.fio }}</span>
                  <span class="addressee-modal__tail">
                    <span
                      v-if="row.department"
                      class="addressee-modal__dep"
                    >{{ row.department }}</span>
                    <button
                      v-if="canAddToSelectedSet && !isInSet(row.id)"
                      class="addressee-modal__to-set"
                      type="button"
                      title="Включить в набор"
                      :disabled="addingMemberId === row.id"
                      @click="addToSelectedSet(row)"
                    >
                      <i class="fa fa-arrow-right" />
                    </button>
                  </span>
                </div>
                <div
                  v-if="isLoadingAllMore"
                  class="addressee-modal__empty"
                >
                  Загрузка...
                </div>
                <div
                  v-else-if="allEmployees.length === 0"
                  class="addressee-modal__empty"
                >
                  Нет сотрудников
                </div>
              </div>
            </div>
            <div class="addressee-modal__col">
              <div
                v-if="showSetSplit"
                class="addressee-modal__col-title"
              >
                {{ selectedGroupTitle }}
              </div>
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
  computed, getCurrentInstance, nextTick, ref, watch,
} from 'vue';
import debounce from 'lodash/debounce';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

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

type Hospital = {
  id: number;
  title: string;
  isDefault?: boolean;
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

const root = getCurrentInstance().proxy.$root;

const opened = ref(false);
const hospitals = ref<Hospital[]>([]);
const hospitalId = ref<number | null>(null);
const hospitalOptions = computed(() => hospitals.value.map(row => ({
  id: row.id,
  label: row.title,
})));
const groups = ref<Group[]>([]);
const selectedGroupId = ref(0);
const query = ref('');
const employees = ref<Employee[]>([]);
const allEmployees = ref<Employee[]>([]);
const setMemberIds = ref<Set<number>>(new Set());
const draft = ref<Employee[]>([]);
const newSetTitle = ref('');
const page = ref(1);
const hasMore = ref(false);
const allPage = ref(1);
const allHasMore = ref(false);
const isLoading = ref(false);
const isLoadingMore = ref(false);
const isLoadingAll = ref(false);
const isLoadingAllMore = ref(false);
const isTogglingAll = ref(false);
const isSavingSet = ref(false);
const addingMemberId = ref<number | null>(null);
const allMatchingSelected = ref(false);
const rowsEl = ref<HTMLElement | null>(null);
const allRowsEl = ref<HTMLElement | null>(null);
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

const selectedGroup = computed(() => groups.value.find(row => row.id === selectedGroupId.value) || null);

const showSetSplit = computed(() => selectedGroupId.value > 0);

const selectedGroupTitle = computed(() => selectedGroup.value?.title || '');

const canAddToSelectedSet = computed(() => Boolean(selectedGroup.value?.own));

const isInSet = (id: number) => setMemberIds.value.has(id);

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
    hospitalId: hospitalId.value,
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
      hospitalId: hospitalId.value,
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

const loadEveryone = async (append = false) => {
  if (selectedGroupId.value <= 0) {
    allEmployees.value = [];
    allHasMore.value = false;
    return;
  }
  if (append) {
    if (!allHasMore.value || isLoadingAllMore.value || isLoadingAll.value) {
      return;
    }
    isLoadingAllMore.value = true;
  } else {
    isLoadingAll.value = true;
    allPage.value = 1;
    allHasMore.value = false;
  }
  try {
    const nextPage = append ? allPage.value + 1 : 1;
    const data = await api('document-manager/addressees/employees', {
      groupId: 0,
      hospitalId: hospitalId.value,
      hospitalScope: true,
      query: query.value,
      page: nextPage,
      pageSize: PAGE_SIZE,
    });
    const rows = data.result || [];
    allPage.value = data.page || nextPage;
    allHasMore.value = Boolean(data.hasMore);
    allEmployees.value = append ? [...allEmployees.value, ...rows] : rows;
  } finally {
    isLoadingAll.value = false;
    isLoadingAllMore.value = false;
  }
};

let memberRequest = 0;

const refreshMemberIds = async () => {
  const requestId = memberRequest + 1;
  memberRequest = requestId;
  const groupId = selectedGroupId.value;
  if (groupId <= 0) {
    setMemberIds.value = new Set();
    return;
  }
  const rows = await loadAllEmployees(groupId, '');
  if (requestId !== memberRequest || selectedGroupId.value !== groupId) {
    return;
  }
  setMemberIds.value = new Set(rows.map(row => row.id));
};

const reloadMiddle = () => {
  loadEmployees(false);
  if (selectedGroupId.value > 0) {
    loadEveryone(false);
    return;
  }
  allEmployees.value = [];
  allHasMore.value = false;
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

const onAllRowsScroll = () => {
  const el = allRowsEl.value;
  if (!el || !allHasMore.value || isLoadingAllMore.value) {
    return;
  }
  if (el.scrollHeight - el.scrollTop - el.clientHeight < 80) {
    loadEveryone(true);
  }
};

const debouncedLoad = debounce(() => reloadMiddle(), 250);

const selectGroup = (id: number) => {
  selectedGroupId.value = id;
  allMatchingSelected.value = false;
  setMemberIds.value = new Set();
  reloadMiddle();
  if (id > 0) {
    refreshMemberIds();
  }
};

const reloadGroups = async () => {
  const { result } = await api('document-manager/addressees/groups/list', { includeAll: true, includeHidden: false });
  groups.value = result || [];
};

const loadHospitals = async () => {
  const { result } = await api('document-manager/addressees/hospitals');
  hospitals.value = result || [];
  const preferred = hospitals.value.find(row => row.isDefault) || hospitals.value[0];
  hospitalId.value = preferred ? preferred.id : null;
};

const onHospitalInput = (value: number | null) => {
  if (value == null || value === hospitalId.value) {
    return;
  }
  hospitalId.value = value;
  if (!opened.value) {
    return;
  }
  allMatchingSelected.value = false;
  setMemberIds.value = new Set();
  reloadMiddle();
  if (selectedGroupId.value > 0) {
    refreshMemberIds();
  }
};

const openModal = async () => {
  draft.value = parseValue(props.value);
  query.value = '';
  newSetTitle.value = '';
  allMatchingSelected.value = false;
  employees.value = [];
  allEmployees.value = [];
  opened.value = true;
  await reloadGroups();
  await loadHospitals();
  selectedGroupId.value = groups.value[0] ? groups.value[0].id : -1;
  setMemberIds.value = new Set();
  await Promise.all([
    loadEmployees(false),
    selectedGroupId.value > 0 ? loadEveryone(false) : Promise.resolve(),
    selectedGroupId.value > 0 ? refreshMemberIds() : Promise.resolve(),
  ]);
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
        await Promise.all([loadEmployees(false), loadEveryone(false), refreshMemberIds()]);
      }
    }
  } finally {
    isSavingSet.value = false;
  }
};

const addToSelectedSet = async (row: Employee) => {
  if (!canAddToSelectedSet.value || selectedGroupId.value <= 0 || isInSet(row.id) || addingMemberId.value != null) {
    return;
  }
  addingMemberId.value = row.id;
  try {
    const result = await api('document-manager/addressees/groups/add-member', {
      id: selectedGroupId.value,
      memberId: row.id,
    });
    if (result?.ok) {
      const nextIds = new Set(setMemberIds.value);
      nextIds.add(row.id);
      setMemberIds.value = nextIds;
      await Promise.all([loadEmployees(false), refreshMemberIds()]);
    } else {
      root.$emit('msg', 'error', result?.message || 'Не удалось добавить в набор');
    }
  } finally {
    addingMemberId.value = null;
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
    setMemberIds.value = new Set();
    allEmployees.value = [];
    allHasMore.value = false;
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

.addressee-modal-wrap {
  display: flex;
  flex-direction: column;
  gap: 8px;
  height: 490px;
  min-height: 0;
}

.addressee-modal__hospital {
  flex: 0 0 34px;
  width: 100%;
  height: 34px;
}

.addressee-modal {
  display: grid;
  grid-template-columns: 180px 1fr 220px;
  gap: 8px;
  flex: 1 1 auto;
  height: auto;
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

.addressee-modal__columns {
  display: flex;
  flex: 1 1 auto;
  min-height: 0;
  gap: 8px;
}

.addressee-modal__columns--split .addressee-modal__col:first-child {
  flex: 1.35;
}

.addressee-modal__columns--split .addressee-modal__col + .addressee-modal__col {
  border-left: 1px solid #ddd;
  padding-left: 8px;
}

.addressee-modal__col {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  min-height: 0;
  gap: 6px;
}

.addressee-modal__col-title {
  flex: 0 0 auto;
  font-weight: 600;
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

.addressee-modal__fio {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.addressee-modal__tail {
  display: flex;
  align-items: center;
  flex: 0 0 auto;
  gap: 6px;
  margin-left: auto;
}

.addressee-modal__dep {
  margin-left: auto;
  color: #888;
  font-size: 12px;
}

.addressee-modal__tail .addressee-modal__dep {
  margin-left: 0;
}

.addressee-modal__to-set {
  flex: 0 0 auto;
  border: none;
  background: transparent;
  color: #049372;
  cursor: pointer;
  padding: 0 2px;
  line-height: 1;
}

.addressee-modal__to-set:disabled {
  cursor: default;
  opacity: 0.5;
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
