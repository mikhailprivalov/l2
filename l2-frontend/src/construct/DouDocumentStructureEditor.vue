<template>
  <div class="root">
    <div class="top-editor">
      <div class="input-group">
        <span class="input-group-addon">Вид документа ({{ typeDocumentId }})</span>
        <input
          :value="typeTitle"
          type="text"
          class="form-control"
          disabled
        >
      </div>
    </div>
    <div
      v-if="typeCode"
      class="code-row"
    >
      <span class="input-group-addon">Код</span>
      <input
        :value="typeCode"
        type="text"
        class="form-control"
        disabled
      >
    </div>
    <div class="content-editor">
      <div
        v-for="group in orderedGroups"
        :key="group.pk === -1 ? `new-${group.order}` : group.pk"
        class="ed-group"
      >
        <div class="input-group">
          <span class="input-group-btn">
            <button
              class="btn btn-blue-nb lob"
              type="button"
              :disabled="isFirstGroup(group)"
              @click="decGroupOrder(group)"
            >
              <i class="glyphicon glyphicon-arrow-up" />
            </button>
          </span>
          <span class="input-group-btn">
            <button
              class="btn btn-blue-nb nob"
              type="button"
              :disabled="isLastGroup(group)"
              @click="incGroupOrder(group)"
            >
              <i class="glyphicon glyphicon-arrow-down" />
            </button>
          </span>
          <span class="input-group-addon">Название группы ({{ group.pk === -1 ? 'новое' : group.pk }})</span>
          <input
            v-model="group.title"
            type="text"
            class="form-control"
            :class="{ 'hide-background': group.hide }"
            :disabled="group.hide"
            placeholder="Название"
          >
        </div>
        <div class="row group-flags">
          <div class="col-xs-8">
            <label v-if="!group.hide">
              Отображать название
              <input
                v-model="group.show_title"
                type="checkbox"
              >
            </label>
            <label v-if="!group.hide">
              Поля в одну строку
              <input
                v-model="group.fieldsInline"
                type="checkbox"
              >
            </label>
          </div>
          <div class="col-xs-4 text-right">
            <label>
              Скрыть группу
              <input
                v-model="group.hide"
                type="checkbox"
              >
            </label>
          </div>
        </div>
        <template v-if="!group.hide">
          <div>
            <strong>Поля ввода</strong>
          </div>
          <div
            v-for="row in orderedFields(group)"
            :key="row.pk === -1 ? `new-field-${group.order}-${row.order}` : row.pk"
            class="ed-field"
          >
            <div class="ed-field-inner">
              <div>
                <button
                  class="btn btn-default btn-sm btn-block"
                  type="button"
                  :disabled="isFirstField(group, row)"
                  @click="decOrder(group, row)"
                >
                  <i class="glyphicon glyphicon-arrow-up" />
                </button>
                <button
                  class="btn btn-default btn-sm btn-block"
                  type="button"
                  :disabled="isLastField(group, row)"
                  @click="incOrder(group, row)"
                >
                  <i class="glyphicon glyphicon-arrow-down" />
                </button>
              </div>
              <div>
                <div class="input-group">
                  <span class="input-group-addon">Название поля ({{ row.pk === -1 ? 'новое' : row.pk }})</span>
                  <input
                    v-model="row.title"
                    type="text"
                    class="form-control"
                    :disabled="row.hide"
                    :class="{ 'hide-background': row.hide }"
                  >
                  <span class="input-group-addon">Синоним</span>
                  <input
                    v-model="row.short_title"
                    type="text"
                    class="form-control"
                    :disabled="row.hide"
                    :class="{ 'hide-background': row.hide }"
                  >
                </div>
                <div
                  v-if="!row.hide"
                  class="input-group"
                >
                  <span class="input-group-addon">Значение по умолчанию</span>
                  <input
                    v-model="row.default"
                    type="text"
                    class="form-control"
                  >
                </div>
                <div
                  v-if="!row.hide && [0, 3, 4, 5].includes(Number(row.field_type))"
                  class="templates"
                >
                  <div class="input-group">
                    <input
                      v-model="row.new_value"
                      type="text"
                      class="form-control"
                      placeholder="Новый шаблон / вариант"
                      @keyup.enter="addTemplateValue(row)"
                    >
                    <span class="input-group-btn">
                      <button
                        class="btn last btn-blue-nb"
                        type="button"
                        :disabled="row.new_value === ''"
                        @click="addTemplateValue(row)"
                      >
                        Добавить
                      </button>
                    </span>
                  </div>
                  <div
                    v-for="(v, i) in row.values_to_input"
                    :key="i"
                    class="input-group"
                  >
                    <span class="input-group-btn">
                      <button
                        class="btn btn-blue-nb lob"
                        type="button"
                        :disabled="i === 0"
                        @click="upTemplate(row, i)"
                      >
                        <i class="glyphicon glyphicon-arrow-up" />
                      </button>
                    </span>
                    <span class="input-group-btn">
                      <button
                        class="btn btn-blue-nb nob"
                        type="button"
                        :disabled="i === row.values_to_input.length - 1"
                        @click="downTemplate(row, i)"
                      >
                        <i class="glyphicon glyphicon-arrow-down" />
                      </button>
                    </span>
                    <input
                      v-model="row.values_to_input[i]"
                      class="form-control"
                      type="text"
                    >
                    <span class="input-group-btn">
                      <button
                        class="btn btn-blue-nb"
                        type="button"
                        @click="removeTemplate(row, i)"
                      >
                        <i class="glyphicon glyphicon-remove" />
                      </button>
                    </span>
                  </div>
                </div>
                <TableConstructor
                  v-if="!row.hide && Number(row.field_type) === 9"
                  :row="row"
                />
                <div
                  v-if="!row.hide && Number(row.field_type) === 7"
                  class="input-group"
                >
                  <span class="input-group-addon">Мин</span>
                  <input
                    v-model="row.values_to_input[0]"
                    class="form-control"
                  >
                  <span class="input-group-addon">Макс</span>
                  <input
                    v-model="row.values_to_input[1]"
                    class="form-control"
                  >
                  <span class="input-group-addon">Шаг</span>
                  <input
                    v-model="row.values_to_input[2]"
                    class="form-control"
                  >
                  <span class="input-group-addon">Ед.</span>
                  <input
                    v-model="row.values_to_input[3]"
                    class="form-control"
                  >
                </div>
              </div>
              <div>
                <label>
                  Тип поля:<br>
                  <select
                    v-model.number="row.field_type"
                    class="form-control"
                    @change="onFieldTypeChange(row)"
                  >
                    <option
                      v-for="option in fieldTypes"
                      :key="option.id"
                      :value="option.id"
                    >
                      {{ option.title }}
                    </option>
                  </select>
                </label>
                <label v-show="Number(row.field_type) === 0">
                  Число строк:<br>
                  <input
                    v-model.number="row.lines"
                    class="form-control"
                    type="number"
                    min="1"
                  >
                </label>
                <label>
                  <input
                    v-model="row.hide"
                    type="checkbox"
                  > скрыть поле
                </label>
                <label v-if="!row.hide">
                  <input
                    v-model="row.required"
                    type="checkbox"
                  > запрет пустого
                </label>
                <label v-if="!row.hide">
                  <input
                    v-model="row.is_meta_attributes"
                    type="checkbox"
                  > мета-реквизит
                </label>
                <label v-if="!row.hide">
                  <input
                    v-model="row.is_content_attributes"
                    type="checkbox"
                  > содержание
                </label>
              </div>
            </div>
          </div>
          <button
            class="btn btn-blue-nb"
            type="button"
            @click="addField(group)"
          >
            <i class="glyphicon glyphicon-plus" />
            Добавить поле
          </button>
        </template>
      </div>
      <button
        class="btn btn-blue-nb add-group"
        type="button"
        @click="addGroup()"
      >
        <i class="glyphicon glyphicon-plus" />
        Добавить группу
      </button>
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
        @click="save"
      >
        Сохранить
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed, getCurrentInstance, ref, watch,
} from 'vue';
import { orderBy } from 'lodash';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';
import TableConstructor from '@/construct/TableConstructor.vue';

interface DocumentField {
  pk: number;
  order: number;
  title: string;
  short_title: string;
  default: string;
  values_to_input: any[];
  new_value: string;
  hide: boolean;
  lines: number;
  field_type: number;
  required: boolean;
  is_meta_attributes: boolean;
  is_content_attributes: boolean;
}

interface DocumentGroup {
  pk: number;
  order: number;
  title: string;
  show_title: boolean;
  hide: boolean;
  visibility: string;
  fieldsInline: boolean;
  fields: DocumentField[];
}

const props = defineProps<{
  typeDocumentId: number;
}>();

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'saved'): void;
  (e: 'cancel'): void;
}>();

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const typeTitle = ref('');
const typeCode = ref('');
const groups = ref<DocumentGroup[]>([]);

const fieldTypes = [
  { id: 0, title: 'Строка' },
  { id: 1, title: 'Дата' },
  { id: 2, title: 'Расчётное' },
  { id: 3, title: 'Список' },
  { id: 4, title: 'Справочник' },
  { id: 5, title: 'Радио' },
  { id: 6, title: 'Число' },
  { id: 7, title: 'Число range' },
  { id: 8, title: 'Время ЧЧ:ММ' },
  { id: 9, title: 'Таблица' },
  { id: 10, title: 'Исполнитель' },
];

const orderedGroups = computed(() => orderBy(groups.value, 'order'));

const orderedFields = (group: DocumentGroup) => orderBy(group.fields, 'order');

const minMaxGroupOrder = computed(() => {
  const orders = groups.value.map(row => row.order);
  return { min: Math.min(...orders), max: Math.max(...orders) };
});

const minMaxFieldOrder = (group: DocumentGroup) => {
  const orders = group.fields.map(row => row.order);
  return { min: Math.min(...orders), max: Math.max(...orders) };
};

const findGroupByOrder = (order: number) => groups.value.find(row => row.order === order);

const findFieldByOrder = (group: DocumentGroup, order: number) => group.fields.find(row => row.order === order);

const isFirstGroup = (group: DocumentGroup) => group.order === minMaxGroupOrder.value.min;
const isLastGroup = (group: DocumentGroup) => group.order === minMaxGroupOrder.value.max;
const isFirstField = (group: DocumentGroup, row: DocumentField) => row.order === minMaxFieldOrder(group).min;
const isLastField = (group: DocumentGroup, row: DocumentField) => row.order === minMaxFieldOrder(group).max;

const incGroupOrder = (row: DocumentGroup) => {
  if (isLastGroup(row)) return;
  const nextRow = findGroupByOrder(row.order + 1);
  if (nextRow) {
    nextRow.order -= 1;
  }
  // eslint-disable-next-line no-param-reassign
  row.order += 1;
};

const decGroupOrder = (row: DocumentGroup) => {
  if (isFirstGroup(row)) return;
  const prevRow = findGroupByOrder(row.order - 1);
  if (prevRow) {
    prevRow.order += 1;
  }
  // eslint-disable-next-line no-param-reassign
  row.order -= 1;
};

const incOrder = (group: DocumentGroup, row: DocumentField) => {
  if (isLastField(group, row)) return;
  const nextRow = findFieldByOrder(group, row.order + 1);
  if (nextRow) {
    nextRow.order -= 1;
  }
  // eslint-disable-next-line no-param-reassign
  row.order += 1;
};

const decOrder = (group: DocumentGroup, row: DocumentField) => {
  if (isFirstField(group, row)) return;
  const prevRow = findFieldByOrder(group, row.order - 1);
  if (prevRow) {
    prevRow.order += 1;
  }
  // eslint-disable-next-line no-param-reassign
  row.order -= 1;
};

const addField = (group: DocumentGroup, field: Partial<DocumentField> = {}) => {
  let order = 0;
  for (const row of group.fields) {
    order = Math.max(order, row.order);
  }
  const values = field.values_to_input ? [...field.values_to_input] : [];
  if ((field.field_type ?? 0) === 7) {
    while (values.length < 4) {
      values.push('');
    }
  }
  group.fields.push({
    pk: field.pk ?? -1,
    order: field.order ?? order + 1,
    title: field.title ?? '',
    short_title: field.short_title ?? '',
    default: field.default ?? '',
    values_to_input: values,
    new_value: '',
    hide: field.hide ?? false,
    lines: field.lines ?? 3,
    field_type: field.field_type ?? 0,
    required: field.required ?? false,
    is_meta_attributes: field.is_meta_attributes ?? false,
    is_content_attributes: field.is_content_attributes ?? false,
  });
};

const addGroup = (groupSettings: Partial<DocumentGroup> = {}) => {
  let order = 0;
  for (const row of groups.value) {
    order = Math.max(order, row.order);
  }
  const group: DocumentGroup = {
    pk: groupSettings.pk ?? -1,
    order: groupSettings.order ?? order + 1,
    title: groupSettings.title ?? '',
    show_title: groupSettings.show_title ?? true,
    hide: groupSettings.hide ?? false,
    visibility: groupSettings.visibility ?? '',
    fieldsInline: groupSettings.fieldsInline ?? false,
    fields: [],
  };
  if (groupSettings.fields?.length) {
    for (const currentField of groupSettings.fields) {
      addField(group, currentField);
    }
  } else {
    addField(group);
  }
  groups.value.push(group);
};

const addTemplateValue = (row: DocumentField) => {
  if (row.new_value === '') return;
  row.values_to_input.push(row.new_value);
  // eslint-disable-next-line no-param-reassign
  row.new_value = '';
};

const upTemplate = (row: DocumentField, i: number) => {
  if (i === 0) return;
  const values = [...row.values_to_input];
  [values[i - 1], values[i]] = [values[i], values[i - 1]];
  // eslint-disable-next-line no-param-reassign
  row.values_to_input = values;
};

const downTemplate = (row: DocumentField, i: number) => {
  if (i === row.values_to_input.length - 1) return;
  const values = [...row.values_to_input];
  [values[i + 1], values[i]] = [values[i], values[i + 1]];
  // eslint-disable-next-line no-param-reassign
  row.values_to_input = values;
};

const removeTemplate = (row: DocumentField, i: number) => {
  row.values_to_input.splice(i, 1);
};

const onFieldTypeChange = (row: DocumentField) => {
  if (Number(row.field_type) === 7) {
    while (row.values_to_input.length < 4) {
      row.values_to_input.push('');
    }
  }
};

const load = async () => {
  groups.value = [];
  typeTitle.value = '';
  typeCode.value = '';
  if (!props.typeDocumentId || props.typeDocumentId < 0) {
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    const data = await api('document-manager/structure/details', { id: props.typeDocumentId });
    if (!data?.ok) {
      root.$emit('msg', 'error', data?.message || 'Не удалось загрузить структуру');
      return;
    }
    typeTitle.value = data.title || '';
    typeCode.value = data.code || '';
    groups.value = [];
    if (data.groups?.length) {
      for (const group of data.groups) {
        addGroup(group);
      }
    } else {
      addGroup();
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const save = async () => {
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/structure/update', {
      id: props.typeDocumentId,
      groups: groups.value,
    });
    if (result?.ok) {
      root.$emit('msg', 'ok', 'Сохранено');
      emit('saved');
    } else {
      root.$emit('msg', 'error', result?.message || 'Ошибка сохранения');
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

watch(() => props.typeDocumentId, load, { immediate: true });
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
  height: 34px;
  width: 100%;
  min-width: 0;

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
    border-right: none;
    border-bottom: 1px solid #96a0ad;
    border-radius: 0;
    display: block !important;
    box-shadow: none;
  }
}

.code-row {
  display: flex;
  align-items: stretch;
  flex: 0 0 34px;
  height: 34px;

  .input-group-addon {
    display: flex;
    align-items: center;
    flex: 0 0 auto;
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
    min-width: 0;
    height: 34px;
    padding: 0 10px;
    line-height: 22px;
    font-size: 14px;
    color: #434A54;
    border-top: none;
    border-left: 1px solid #96a0ad;
    border-right: none;
    border-bottom: 1px solid #96a0ad;
    border-radius: 0;
    box-shadow: none;
  }
}

.footer-editor {
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

.content-editor {
  flex: 1;
  padding: 5px;
  overflow-y: auto;
  overflow-x: hidden;
}

.ed-group {
  padding: 5px;
  margin: 5px;
  border-radius: 0;
  background: #f0f0f0;
}

.group-flags {
  margin: 6px 0;
}

.group-flags label {
  margin-right: 12px;
}

.ed-field {
  padding: 5px;
  margin: 5px;
  border-radius: 0;
  background: #fff;
}

.ed-field-inner {
  display: flex;
  flex-direction: row;
  align-items: stretch;
}

.ed-field-inner > div:nth-child(1) {
  flex: 0 0 35px;
  padding-right: 5px;
}

.ed-field-inner > div:nth-child(2) {
  flex: 1;
}

.ed-field-inner > div:nth-child(3) {
  width: 180px;
  padding-left: 5px;
  white-space: nowrap;

  label {
    display: block;
    margin-bottom: 2px;
    width: 100%;
  }
}

.templates {
  margin-top: 5px;
}

.templates .input-group {
  margin-bottom: 1px;
}

.hide-background {
  background: #e8e8e8;
}

.add-group {
  margin: 5px;
}

.lob {
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
}

.nob {
  border-radius: 0;
}
</style>
