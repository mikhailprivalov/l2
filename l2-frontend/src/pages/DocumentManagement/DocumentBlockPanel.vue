<template>
  <div class="block-panel">
    <div
      v-if="loading"
      class="empty"
    >
      Загрузка...
    </div>
    <template v-else-if="loaded">
      <label class="block-title">
        <span>Название</span>
        <input
          v-model="title"
          class="form-control"
          type="text"
          :disabled="!canEdit"
          @blur="saveSettings"
        >
      </label>
      <label
        class="block-publish"
        @click.prevent="togglePublished"
      >
        <input
          type="checkbox"
          :checked="isPublished"
          :disabled="!canEdit"
          tabindex="-1"
        >
        <span>Опубликовать</span>
      </label>
      <div class="block-access">
        <span>Чтение</span>
        <AddresseeField
          class="block-access__field"
          header="Доступ на чтение"
          :value="readAccess"
          :disabled="!canEdit"
          @input="onReadAccess"
        />
      </div>
      <div class="block-access">
        <span>Запись</span>
        <AddresseeField
          class="block-access__field"
          header="Доступ на запись"
          :value="writeAccess"
          :disabled="!canEdit"
          @input="onWriteAccess"
        />
      </div>
      <div class="block-note">
        Пустое чтение или «Опубликовать» — блок виден всем.
        Пустая запись — документы добавляет только создатель.
      </div>
      <div class="block-meta">
        Создатель: {{ creator || '—' }}
        <span class="block-gap" />
        {{ createdAt }}
      </div>
      <div
        v-if="documents.length"
        class="block-docs"
      >
        <div class="block-docs__head">
          <button
            class="block-docs__toggle"
            type="button"
            title="Развернуть все"
            @click="expandAllDocuments"
          >
            +
          </button>
          <button
            class="block-docs__toggle"
            type="button"
            title="Свернуть все"
            @click="collapseAllDocuments"
          >
            −
          </button>
          <span class="block-docs__title">Документы</span>
        </div>
        <div
          v-for="row in documents"
          :key="row.id"
          class="block-docs__item"
          :class="{ 'block-docs__item--open': row.expanded }"
        >
          <div class="block-docs__row">
            <button
              class="block-docs__toggle"
              type="button"
              :title="row.expanded ? 'Свернуть' : 'Развернуть'"
              @click="toggleDocumentBody(row.id)"
            >
              {{ row.expanded ? '−' : '+' }}
            </button>
            <span class="block-docs__line">{{ documentLine(row) }}</span>
            <a
              class="a-under block-docs__link"
              :href="documentHref(row.id)"
              target="_blank"
              rel="noopener"
            >Перейти</a>
          </div>
          <div
            v-if="row.expanded"
            class="block-docs__body"
          >
            <div
              v-if="row.loading"
              class="empty"
            >
              Загрузка...
            </div>
            <div
              v-else-if="row.loaded && !row.research"
              class="empty"
            >
              У вида не выбран шаблон
            </div>
            <template v-else-if="row.research">
              <DescriptiveForm
                :key="`${row.id}-${row.issPk}-${row.confirmed}`"
                :research="row.research"
                :confirmed="row.confirmed"
                :patient="patient"
                :pk="row.issPk"
              />
              <div
                v-if="row.whoConfirmed"
                class="group"
              >
                <div class="fields">
                  <div class="field">
                    <label class="field-title">Подтверждено</label>
                    <div class="field-value simple-value">
                      {{ row.whoConfirmed }}
                    </div>
                  </div>
                </div>
              </div>
              <div
                v-if="row.hasPrintTemplate"
                class="control-row"
              >
                <div class="res-title">
                  {{ row.typeTitle }}:
                </div>
                <a
                  class="print-link a-under"
                  :href="printHref(row.id, 'docx')"
                  download
                >docx</a>
                <a
                  class="print-link a-under"
                  :href="printHref(row.id, 'pdf')"
                  target="_blank"
                  rel="noopener"
                >pdf</a>
              </div>
            </template>
          </div>
        </div>
      </div>
      <div
        v-else
        class="empty"
      >
        Нет документов
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import {
  getCurrentInstance, ref, watch,
} from 'vue';

import api from '@/api';
import AddresseeField from '@/forms/Fields/AddresseeField.vue';
import DescriptiveForm from '@/forms/DescriptiveForm.vue';

type BlockDocumentRow = {
  id: number;
  topic: string;
  typeTitle: string;
  createdAt: string;
  creator: string;
  expanded: boolean;
  loading: boolean;
  loaded: boolean;
  research: any;
  issPk: number | null;
  confirmed: boolean;
  hasPrintTemplate: boolean;
  whoConfirmed: string;
};

const props = defineProps<{
  blockId: number | null;
}>();

const root = getCurrentInstance().proxy.$root;
const loading = ref(false);
const loaded = ref(false);
const title = ref('');
const savedTitle = ref('');
const isPublished = ref(false);
const canEdit = ref(false);
const creator = ref('');
const createdAt = ref('');
const readAccess = ref('[]');
const writeAccess = ref('[]');
const documents = ref<BlockDocumentRow[]>([]);
const patient = {};

const blankDocumentBody = () => ({
  expanded: false,
  loading: false,
  loaded: false,
  research: null,
  issPk: null as number | null,
  confirmed: false,
  hasPrintTemplate: false,
  whoConfirmed: '',
});

const documentLine = (row: { id: number; topic: string; typeTitle: string; createdAt: string; creator: string }) => (
  [String(row.id), row.topic, row.typeTitle, row.createdAt, row.creator].map(part => (part || '').trim() || '—').join(', ')
);

const documentHref = (id: number) => `${window.location.origin}/ui/document-manager-2?document=${id}`;

const printHref = (id: number, format: 'docx' | 'pdf') => (
  `${window.location.origin}/api/document-manager/documents/print?id=${id}&format=${format}`
);

const documentById = (id: number) => documents.value.find(item => item.id === id);

const patchDocument = (id: number, patch: Partial<BlockDocumentRow>) => {
  documents.value = documents.value.map(item => (
    item.id === id ? { ...item, ...patch } : item
  ));
};

const loadDocumentBody = async (id: number) => {
  const current = documentById(id);
  if (!current || current.loaded || current.loading) {
    return;
  }
  patchDocument(id, { loading: true });
  try {
    const result = await api('document-manager/documents/details', { id });
    if (!result?.ok) {
      patchDocument(id, { expanded: false, loading: false });
      root.$emit('msg', 'error', result?.message || 'Ошибка загрузки');
      return;
    }
    patchDocument(id, {
      research: result.research || null,
      issPk: result.issPk || null,
      confirmed: Boolean(result.confirmed),
      hasPrintTemplate: Boolean(result.hasPrintTemplate),
      whoConfirmed: result.whoConfirmed || '',
      loaded: true,
      loading: false,
    });
  } catch (error) {
    patchDocument(id, { expanded: false, loading: false });
    throw error;
  }
};

const toggleDocumentBody = (id: number) => {
  const current = documentById(id);
  if (!current) {
    return;
  }
  const expanded = !current.expanded;
  patchDocument(id, { expanded });
  if (expanded) {
    loadDocumentBody(id);
  }
};

const expandAllDocuments = () => {
  const ids = documents.value.map(item => item.id);
  documents.value = documents.value.map(item => ({ ...item, expanded: true }));
  ids.forEach(id => {
    loadDocumentBody(id);
  });
};

const collapseAllDocuments = () => {
  documents.value = documents.value.map(item => ({ ...item, expanded: false }));
};

const loadBlock = async (id: number) => {
  loading.value = true;
  loaded.value = false;
  try {
    const result = await api('document-manager/blocks/details', { id });
    if (!result?.ok) {
      root.$emit('msg', 'error', result?.message || 'Блок не найден');
      return;
    }
    title.value = result.title || '';
    savedTitle.value = title.value;
    isPublished.value = Boolean(result.isPublished);
    canEdit.value = Boolean(result.canEdit);
    creator.value = result.creator || '';
    createdAt.value = result.createdAt || '';
    readAccess.value = JSON.stringify(result.readAccess || []);
    writeAccess.value = JSON.stringify(result.writeAccess || []);
    documents.value = (result.documents || []).map(row => ({
      id: row.id,
      topic: row.topic || '',
      typeTitle: row.typeTitle || '',
      createdAt: row.createdAt || '',
      creator: row.creator || '',
      ...blankDocumentBody(),
    }));
    loaded.value = true;
  } finally {
    loading.value = false;
  }
};

const saveSettings = async () => {
  if (!canEdit.value || !props.blockId) {
    return;
  }
  const nextTitle = title.value.trim();
  if (!nextTitle) {
    title.value = savedTitle.value;
    root.$emit('msg', 'error', 'Укажите название блока');
    return;
  }
  if (nextTitle === savedTitle.value) {
    return;
  }
  title.value = nextTitle;
  const result = await api('document-manager/blocks/update', {
    id: props.blockId,
    title: nextTitle,
    isPublished: isPublished.value,
  });
  if (!result?.ok) {
    title.value = savedTitle.value;
    root.$emit('msg', 'error', result?.message || 'Не удалось сохранить');
    return;
  }
  savedTitle.value = result.title || nextTitle;
  root.$emit('msg', 'ok', 'Блок сохранён');
};

const togglePublished = async () => {
  if (!canEdit.value || !props.blockId) {
    return;
  }
  const next = !isPublished.value;
  isPublished.value = next;
  const result = await api('document-manager/blocks/update', {
    id: props.blockId,
    title: savedTitle.value,
    isPublished: next,
  });
  if (!result?.ok) {
    isPublished.value = !next;
    root.$emit('msg', 'error', result?.message || 'Не удалось сохранить');
  }
};

const saveAccess = async (kind: 'read' | 'write', value: string) => {
  if (!canEdit.value || !props.blockId) {
    return;
  }
  const previous = kind === 'read' ? readAccess.value : writeAccess.value;
  if (value === previous) {
    return;
  }
  let members = [];
  try {
    members = JSON.parse(value || '[]');
  } catch {
    return;
  }
  if (kind === 'read') {
    readAccess.value = value;
  } else {
    writeAccess.value = value;
  }
  const point = kind === 'read' ? 'document-manager/blocks/read-access' : 'document-manager/blocks/write-access';
  const result = await api(point, { id: props.blockId, members });
  if (!result?.ok) {
    if (kind === 'read') {
      readAccess.value = previous;
    } else {
      writeAccess.value = previous;
    }
    root.$emit('msg', 'error', result?.message || 'Не удалось сохранить доступ');
    return;
  }
  const saved = kind === 'read' ? result.readAccess : result.writeAccess;
  const nextValue = JSON.stringify(saved || members);
  if (kind === 'read') {
    readAccess.value = nextValue;
  } else {
    writeAccess.value = nextValue;
  }
};

const onReadAccess = (value: string) => {
  saveAccess('read', value);
};

const onWriteAccess = (value: string) => {
  saveAccess('write', value);
};

watch(() => props.blockId, (id) => {
  if (id) {
    loadBlock(id);
    return;
  }
  loaded.value = false;
}, { immediate: true });
</script>

<style scoped lang="scss">
.block-panel {
  height: 100%;
  overflow: auto;
  padding: 10px 12px;
  background: #fff;
}

.block-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
  font-size: 12px;
}

.block-publish {
  display: flex;
  align-items: center;
  gap: 6px;
  width: max-content;
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: normal;
  cursor: pointer;

  input {
    margin: 0;
    pointer-events: none;
  }
}

.block-access {
  display: flex;
  align-items: stretch;
  gap: 8px;
  margin-bottom: 8px;

  > span {
    flex: 0 0 64px;
    padding-top: 6px;
    font-size: 12px;
  }
}

.block-access__field {
  flex: 1;
  min-width: 0;
}

.block-meta,
.block-docs-title,
.block-note {
  font-size: 13px;
  line-height: 1.4;
}

.block-note {
  margin-bottom: 8px;
  color: #656d78;
  font-size: 12px;
}

.block-docs {
  margin-top: 10px;
  border-top: 1px solid #ccd1d9;
}

.block-docs__head,
.block-docs__row {
  display: flex;
  flex-direction: row;
  align-items: baseline;
  gap: 6px;
  padding: 4px 0;
  font-size: 13px;
}

.block-docs__item {
  border-bottom: 1px solid #e6e9ed;
}

.block-docs__title {
  font-weight: bold;
}

.block-docs__toggle {
  flex: 0 0 auto;
  width: 16px;
  padding: 0;
  border: 0;
  background: transparent;
  color: #434a54;
  font-size: 16px;
  font-weight: bold;
  line-height: 1;
  cursor: pointer;
}

.block-docs__line {
  flex: 1;
  min-width: 0;
}

.block-docs__link {
  flex: 0 0 auto;
  white-space: nowrap;
}

.block-docs__item--open {
  margin: 4px 0;
  background: #fff;
  border: 1px solid #ccd1d9;
}

.block-docs__body {
  padding: 0 8px 8px;

  .control-row {
    height: auto;
    min-height: 34px;
    flex-wrap: wrap;
    padding-right: 0;
  }
}

.simple-value {
  padding: 5px;
}

.control-row {
  min-height: 34px;
  background-color: #f3f3f3;
  display: flex;
  flex-direction: row;
  margin-bottom: 10px;
}

.res-title {
  flex: 1;
  padding: 5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.print-link {
  align-self: center;
  margin-right: 12px;
  white-space: nowrap;
}

.block-gap {
  display: inline-block;
  width: 16px;
}

.empty {
  padding: 8px 0;
  color: #656d78;
  font-size: 12px;
}
</style>
