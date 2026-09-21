<template>
  <div class="root">
    <div class="top-editor oneLine">
      <div class="left">
        <div class="input-group">
          <div class="field-slot">
            <span class="input-group-addon">Название</span>
            <input
              v-model="title"
              type="text"
              class="form-control"
            >
          </div>
          <template v-if="kind === 'type' || kind === 'case'">
            <div class="field-slot">
              <span class="input-group-addon">Код</span>
              <input
                v-model="code"
                type="text"
                class="form-control"
              >
            </div>
            <div
              v-if="kind === 'type'"
              class="field-slot"
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
          </template>
        </div>
      </div>
    </div>
    <div class="content-editor">
      <div
        v-if="kind === 'type'"
        class="templates-block"
      >
        <div class="template-row">
          <span class="input-group-addon">Шаблоны документа</span>
          <Treeselect
            v-model="templateToAdd"
            class="treeselect-wide treeselect-34px template-select"
            :multiple="false"
            :disable-branch-nodes="true"
            :options="availableTemplates"
            placeholder="Добавить шаблон"
            :append-to-body="true"
            :clearable="true"
            @select="onSelectTemplate"
          />
        </div>
        <div
          v-if="selectedTemplates.length === 0"
          class="empty-templates"
        >
          Шаблоны не выбраны
        </div>
        <div
          v-for="(row, index) in selectedTemplates"
          :key="row.id"
          class="template-item"
        >
          <span class="template-item-title">{{ row.label }}</span>
          <button
            class="btn btn-blue-nb template-item-btn"
            type="button"
            :disabled="index === 0"
            title="Выше"
            @click="moveTemplate(index, -1)"
          >
            <i class="glyphicon glyphicon-arrow-up" />
          </button>
          <button
            class="btn btn-blue-nb template-item-btn"
            type="button"
            :disabled="index === selectedTemplates.length - 1"
            title="Ниже"
            @click="moveTemplate(index, 1)"
          >
            <i class="glyphicon glyphicon-arrow-down" />
          </button>
          <button
            class="btn btn-blue-nb template-item-btn"
            type="button"
            title="Удалить"
            @click="removeTemplate(index)"
          >
            <i class="glyphicon glyphicon-remove" />
          </button>
        </div>
        <div class="template-row">
          <span class="input-group-addon">Создатели</span>
          <AddresseeField
            class="creators-field"
            header="Создатели"
            hide-preview
            :value="creatorsJson"
            @input="onCreatorsInput"
          />
        </div>
        <div
          v-if="creators.length === 0"
          class="empty-templates"
        >
          Создатели не указаны — доступен всем
        </div>
        <div
          v-for="row in creators"
          :key="row.id"
          class="template-item"
        >
          <span class="template-item-title">{{ row.fio }}</span>
          <button
            class="btn btn-blue-nb template-item-btn"
            type="button"
            title="Удалить"
            @click="removeCreator(row.id)"
          >
            <i class="glyphicon glyphicon-remove" />
          </button>
        </div>
      </div>
      <div
        v-else-if="kind === 'case'"
        class="templates-block"
      >
        <div class="template-row">
          <span class="input-group-addon">Документ по умолчанию</span>
          <Treeselect
            v-model="defaultTypeDocumentId"
            class="treeselect-wide treeselect-34px template-select"
            :multiple="false"
            :disable-branch-nodes="true"
            :options="documentTypeOptions"
            placeholder="Выберите вид документа"
            :append-to-body="true"
            :clearable="true"
          />
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
        :disabled="!canSave"
        @click="save"
      >
        Сохранить
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed, getCurrentInstance, nextTick, onMounted, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';
import AddresseeField from '@/forms/Fields/AddresseeField.vue';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

interface CatalogGroup {
  id: number;
  title: string;
}

interface LayoutTemplateOption {
  id: number;
  label: string;
  hasNested?: boolean;
  isDisabled?: boolean;
}

interface CreatorPerson {
  id: number;
  fio: string;
  department?: string;
}

const props = defineProps<{
  kind: 'group' | 'type' | 'case';
  itemId: number;
  titleValue?: string;
  codeValue?: string;
  groupIdValue?: number | null;
  layoutTemplateIdValue?: number | null;
  layoutTemplateIdsValue?: number[];
  layoutTemplatesValue?: LayoutTemplateOption[];
  creatorsValue?: CreatorPerson[];
  defaultTypeDocumentIdValue?: number | null;
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
const templateToAdd = ref<number | null>(null);
const layoutTemplates = ref<LayoutTemplateOption[]>([]);
const selectedTemplates = ref<LayoutTemplateOption[]>([]);
const creators = ref<CreatorPerson[]>([]);
const defaultTypeDocumentId = ref<number | null>(null);
const documentTypeOptions = ref<LayoutTemplateOption[]>([]);

const canSave = computed(() => {
  if (!title.value.trim()) {
    return false;
  }
  if (props.kind === 'case' && !defaultTypeDocumentId.value) {
    return false;
  }
  return true;
});

const creatorsJson = computed(() => JSON.stringify(creators.value.map(row => ({
  id: row.id,
  fio: row.fio,
}))));

const availableTemplates = computed(() => {
  const selected = new Set(selectedTemplates.value.map(row => row.id));
  return layoutTemplates.value
    .filter(row => !selected.has(row.id))
    .map(row => ({
      ...row,
      isDisabled: Boolean(row.isDisabled || row.hasNested),
    }));
});

const applySelectedTemplates = () => {
  if (props.layoutTemplatesValue?.length) {
    selectedTemplates.value = props.layoutTemplatesValue.map(row => ({
      id: row.id,
      label: row.label,
    }));
    return;
  }
  let ids = props.layoutTemplateIdsValue || [];
  if (!ids.length && props.layoutTemplateIdValue) {
    ids = [props.layoutTemplateIdValue];
  }
  selectedTemplates.value = ids.filter(Boolean).map((id) => {
    const option = layoutTemplates.value.find(row => row.id === id);
    return { id, label: option?.label || String(id) };
  });
};

const fill = () => {
  title.value = props.titleValue || '';
  code.value = props.codeValue || '';
  groupId.value = props.groupIdValue ?? -1;
  applySelectedTemplates();
  creators.value = (props.creatorsValue || []).map(row => ({
    id: row.id,
    fio: row.fio || '',
    department: row.department || '',
  }));
  defaultTypeDocumentId.value = props.defaultTypeDocumentIdValue || null;
};

watch(
  () => [
    props.itemId,
    props.titleValue,
    props.codeValue,
    props.groupIdValue,
    props.layoutTemplateIdValue,
    props.layoutTemplateIdsValue,
    props.layoutTemplatesValue,
    props.creatorsValue,
    props.defaultTypeDocumentIdValue,
  ],
  fill,
  { immediate: true },
);

const addTemplateById = (id: number) => {
  const option = layoutTemplates.value.find(row => row.id === id);
  if (!option) {
    root.$emit('msg', 'error', 'Шаблон не найден');
    return;
  }
  if (option.hasNested || option.isDisabled) {
    root.$emit('msg', 'error', 'Нельзя выбрать шаблон с вложенностью');
    return;
  }
  if (selectedTemplates.value.some(row => row.id === option.id)) {
    root.$emit('msg', 'error', 'Шаблон уже добавлен');
    return;
  }
  selectedTemplates.value = [
    ...selectedTemplates.value,
    { id: option.id, label: option.label },
  ];
};

const onSelectTemplate = (node: LayoutTemplateOption) => {
  if (node?.id) {
    addTemplateById(node.id);
  }
  nextTick(() => {
    templateToAdd.value = null;
  });
};

const moveTemplate = (index: number, delta: number) => {
  const nextIndex = index + delta;
  if (nextIndex < 0 || nextIndex >= selectedTemplates.value.length) {
    return;
  }
  const rows = [...selectedTemplates.value];
  const [row] = rows.splice(index, 1);
  rows.splice(nextIndex, 0, row);
  selectedTemplates.value = rows;
};

const removeTemplate = (index: number) => {
  selectedTemplates.value = selectedTemplates.value.filter((_, current) => current !== index);
};

const onCreatorsInput = (value: string) => {
  try {
    const parsed = JSON.parse(value || '[]');
    if (!Array.isArray(parsed)) {
      creators.value = [];
      return;
    }
    creators.value = parsed
      .map((item) => {
        const id = Number(item?.id);
        if (!id) {
          return null;
        }
        return {
          id,
          fio: item.fio || '',
          department: item.department || '',
        };
      })
      .filter(Boolean) as CreatorPerson[];
  } catch {
    creators.value = [];
  }
};

const removeCreator = (id: number) => {
  creators.value = creators.value.filter(row => row.id !== id);
};

const loadLayoutTemplates = async () => {
  if (props.kind !== 'type') {
    return;
  }
  const { rows } = await api('layout-template/list-treeselect', { pk: -1 });
  layoutTemplates.value = rows || [];
  applySelectedTemplates();
};

const loadDocumentTypes = async () => {
  if (props.kind !== 'case') {
    return;
  }
  const { result } = await api('document-manager/types/list');
  documentTypeOptions.value = (result || []).map((row: { id: number; title: string }) => ({
    id: row.id,
    label: row.title,
  }));
};

onMounted(() => {
  loadLayoutTemplates();
  loadDocumentTypes();
});

const save = async () => {
  let endpoint = 'document-manager/types/update';
  if (props.kind === 'group') {
    endpoint = 'document-manager/groups/update';
  } else if (props.kind === 'case') {
    endpoint = 'document-manager/cases/update';
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    const payload = props.kind === 'case'
      ? {
        id: props.itemId,
        title: title.value,
        code: code.value,
        defaultTypeDocumentId: defaultTypeDocumentId.value,
      }
      : {
        id: props.itemId,
        title: title.value,
        code: code.value,
        groupId: groupId.value,
        layoutTemplateId: selectedTemplates.value[0]?.id ?? null,
        layoutTemplateIds: selectedTemplates.value.map(row => row.id),
        creatorIds: creators.value.map(row => row.id),
      };
    const result = await api(endpoint, payload);
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
    border-right: none;
    border-bottom: 1px solid #96a0ad;
    border-radius: 0;
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
    border-left: 1px solid #96a0ad;
    border-right: 1px solid #96a0ad;
    border-bottom: 1px solid #96a0ad;
    border-radius: 0;
    display: block !important;
    box-shadow: none;
  }

  .field-slot {
    display: flex;
    flex: 1 1 0;
    min-width: 0;
    align-items: stretch;
  }

  .field-slot:last-child .form-control {
    border-right: none;
  }
}

.content-editor {
  flex: 1;
  min-height: 0;
  align-self: stretch;
  overflow-y: auto;
}

.templates-block {
  display: flex;
  flex-direction: column;
}

.template-row {
  display: flex;
  align-items: stretch;
  height: 34px;

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
    border-top: none;
    border-left: none;
    border-right: none;
    border-bottom: 1px solid #96a0ad;
    border-radius: 0;
  }
}

.template-select {
  flex: 1 1 0;
  min-width: 0;
}

.creators-field {
  flex: 1 1 0;
  min-width: 0;
}

:deep(.creators-field.addressee-field) {
  height: 34px;
}

:deep(.creators-field .addressee-field__btn) {
  border-top: none !important;
  border-bottom: none !important;
  border-right: none !important;
  border-left: 1px solid #96a0ad;
}

:deep(.template-select .vue-treeselect__control) {
  height: 34px;
  border-top: none;
  border-left: 1px solid #96a0ad;
  border-right: none;
  border-bottom: 1px solid #96a0ad;
  border-radius: 0;
}

.empty-templates {
  padding: 10px;
  color: #656d78;
}

.template-item {
  display: flex;
  align-items: stretch;
  min-height: 34px;
  border-bottom: 1px solid #b1b1b1;
}

.template-item-title {
  flex: 1 1 0;
  min-width: 0;
  display: flex;
  align-items: center;
  padding: 0 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.template-item-btn {
  flex: 0 0 34px;
  width: 34px;
  height: 34px;
  padding: 0;
  border-radius: 0 !important;
  border-top: none !important;
  border-bottom: none !important;
  border-right: none !important;
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
