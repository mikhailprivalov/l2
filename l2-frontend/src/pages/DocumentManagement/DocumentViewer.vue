<template>
  <div class="viewer-root">
    <div
      v-if="!documentId && !caseId"
      class="empty"
    >
      Выберите документ
    </div>
    <div
      v-else
      class="results-content"
    >
      <div
        v-if="!caseListMode"
        class="research-title"
      >
        <div class="research-left">
          <button
            class="favorite-star"
            :class="{ 'favorite-star--on': inFavorite }"
            type="button"
            :title="inFavorite ? 'Убрать из избранного' : 'В избранное'"
            @click="toggleRecordFavorite"
          >
            <i class="fa fa-star" />
          </button>
          <span class="research-title-text">{{ title || '' }}</span>
          <span
            v-if="anyApproverRejected"
            class="doc-agreed doc-agreed--no"
          >Не согласован</span>
          <span
            v-else-if="allApproversAgreed"
            class="doc-agreed"
          >Согласован</span>
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
      <div
        v-if="caseBlock"
        class="case-block"
      >
        <div class="case-block__label">
          <button
            class="favorite-star"
            :class="{ 'favorite-star--on': caseInFavorite }"
            type="button"
            :title="caseInFavorite ? 'Убрать из избранного' : 'В избранное'"
            @click="toggleCaseFavorite"
          >
            <i class="fa fa-star" />
          </button>
          Дело № {{ caseBlock.id }}
        </div>
        <label class="case-block__topic">
          <span>Тема</span>
          <input
            v-model="caseTopic"
            type="text"
            required
            :disabled="!canEditCaseTopic"
            @blur="saveCaseTopic"
          >
        </label>
        <div class="case-block__meta">
          Дата создания: {{ caseBlock.createdAt || '—' }}
          <span class="case-block__gap" />
          Создатель: {{ caseBlock.creator || '—' }}
        </div>
        <label class="case-block__topic">
          <span>Комментарий</span>
          <textarea
            v-model="caseComment"
            rows="2"
            :disabled="!canEditCase"
            @blur="saveCaseComment"
          />
        </label>
        <div
          v-if="caseClosedAt"
          class="case-block__meta"
        >
          Дата закрытия: {{ caseClosedAt }}
          <span class="case-block__gap" />
          Кто закрыл: {{ caseClosedBy || '—' }}
        </div>
        <div
          v-if="canCloseCase"
          class="case-block__close-row"
        >
          <button
            class="btn btn-blue-nb"
            type="button"
            @click="closeCase"
          >
            Закрыть дело
          </button>
        </div>
        <div class="case-block__access">
          <span>Доступ</span>
          <AddresseeField
            class="case-block__access-field"
            header="Доступ к делу"
            :value="caseAccess"
            :disabled="!canEditCaseAccess"
            @input="onCaseAccess"
          />
        </div>
        <div
          v-if="caseListMode && (caseDocuments.length || caseId)"
          class="case-docs"
        >
          <div class="case-docs__head">
            <button
              class="case-docs__toggle"
              type="button"
              title="Развернуть все"
              @click="expandAllDocuments"
            >
              +
            </button>
            <button
              class="case-docs__toggle"
              type="button"
              title="Свернуть все"
              @click="collapseAllDocuments"
            >
              −
            </button>
            <span class="case-docs__title">Документы</span>
          </div>
          <div
            v-for="row in caseDocuments"
            :key="row.id"
            class="case-docs__item"
            :class="{ 'case-docs__item--open': row.expanded }"
          >
            <div class="case-docs__row">
              <button
                class="case-docs__toggle"
                type="button"
                :title="row.expanded ? 'Свернуть' : 'Развернуть'"
                @click="toggleDocumentBody(row.id)"
              >
                {{ row.expanded ? '−' : '+' }}
              </button>
              <span class="case-docs__line">{{ caseDocumentLine(row) }}</span>
              <a
                class="case-docs__link"
                :href="caseDocumentHref(row.id)"
                target="_blank"
                rel="noopener"
              >Перейти</a>
            </div>
            <div
              v-if="row.expanded"
              class="case-docs__body"
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
                <div class="control-row">
                  <div class="res-title">
                    {{ row.typeTitle }}:
                  </div>
                  <a
                    v-if="row.hasPrintTemplate"
                    class="print-link a-under"
                    :href="printHref(row.id, 'docx')"
                    download
                  >docx</a>
                  <a
                    v-if="row.hasPrintTemplate"
                    class="print-link a-under"
                    :href="printHref(row.id, 'pdf')"
                    target="_blank"
                    rel="noopener"
                  >pdf</a>
                  <button
                    v-if="!row.confirmed"
                    class="btn btn-blue-nb"
                    type="button"
                    @click="saveDocument(row.id)"
                  >
                    Сохранить
                  </button>
                  <button
                    v-if="!row.confirmed"
                    class="btn btn-blue-nb"
                    type="button"
                    @click="confirmDocument(row.id)"
                  >
                    Сохранить и подтвердить
                  </button>
                  <button
                    v-if="row.confirmed && row.canReset"
                    class="btn btn-blue-nb"
                    type="button"
                    @click="resetDocument(row.id)"
                  >
                    Сброс подтверждения
                  </button>
                  <button
                    v-if="row.canHide && !row.isHidden"
                    class="btn btn-blue-nb"
                    type="button"
                    @click="setDocumentHidden(row.id, true)"
                  >
                    Скрыть
                  </button>
                  <button
                    v-if="row.canHide && row.isHidden"
                    class="btn btn-blue-nb"
                    type="button"
                    @click="setDocumentHidden(row.id, false)"
                  >
                    Показать
                  </button>
                </div>
                <div class="doc-case-select">
                  <span>Дело</span>
                  <Treeselect
                    :value="row.caseId"
                    class="doc-case-select__field"
                    :multiple="false"
                    :options="row.availableCases"
                    placeholder="Выберите дело"
                    no-options-text="Нет доступных дел"
                    :append-to-body="true"
                    @input="onRowCase(row.id, $event)"
                  />
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>
      <div
        v-if="!caseListMode && loaded && !research"
        class="empty"
      >
        У вида не выбран шаблон
      </div>
      <DescriptiveForm
        v-else-if="!caseListMode && research"
        :key="`${documentId}-${issPk}-${confirmed}`"
        :research="research"
        :confirmed="confirmed"
        :patient="patient"
        :pk="issPk"
      />
      <div
        v-if="!caseListMode && whoConfirmed"
        class="group"
      >
        <div class="fields">
          <div class="field">
            <label class="field-title">Подтверждено</label>
            <div class="field-value simple-value">
              {{ whoConfirmed }}
            </div>
          </div>
        </div>
      </div>
      <div
        v-if="!caseListMode && research"
        class="control-row"
      >
        <div class="res-title">
          {{ title }}:
        </div>
        <a
          v-if="hasPrintTemplate && documentId"
          class="print-link a-under"
          :href="printHref(documentId, 'docx')"
          download
        >docx</a>
        <a
          v-if="hasPrintTemplate && documentId"
          class="print-link a-under"
          :href="printHref(documentId, 'pdf')"
          target="_blank"
          rel="noopener"
        >pdf</a>
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
          v-if="confirmed && canReset"
          class="btn btn-blue-nb"
          type="button"
          @click="resetConfirm"
        >
          Сброс подтверждения
        </button>
        <button
          v-if="canHide && !isHidden"
          class="btn btn-blue-nb"
          type="button"
          @click="setHidden(true)"
        >
          Скрыть
        </button>
        <button
          v-if="canHide && isHidden"
          class="btn btn-blue-nb"
          type="button"
          @click="setHidden(false)"
        >
          Показать
        </button>
      </div>
      <div
        v-if="!caseListMode && approvalMode && (research || loaded)"
        class="group"
      >
        <div class="group-title">
          Согласование
        </div>
        <div class="fields">
          <div class="approval-status">
            <div
              v-for="row in approvalStatuses"
              :key="row.id"
              class="approval-status__row"
            >
              <span class="approval-status__fio">{{ row.fio }}</span>
              <span
                class="approval-status__state"
                :class="`approval-status__state--${row.status}`"
              >{{ approvalStatusText(row.status) }}</span>
              <span class="approval-status__date">{{ row.decidedAt }}</span>
              <span class="approval-status__comment">
                <input
                  v-if="canDecideRow(row)"
                  v-model="approvalComment"
                  class="approval-status__comment-input"
                  type="text"
                  maxlength="130"
                >
                <template v-else>{{ row.comment }}</template>
              </span>
              <span class="approval-status__action">
                <button
                  v-if="canDecideRow(row)"
                  class="btn approval-status__btn"
                  :class="approvalComment.trim() ? 'btn-danger' : 'approval-status__btn--agree'"
                  type="button"
                  @click="approveMine"
                >
                  {{ approvalButtonLabel }}
                </button>
                <button
                  v-else-if="canCancelRow(row)"
                  class="btn btn-blue-nb approval-status__btn"
                  type="button"
                  @click="cancelApproval(row)"
                >
                  Отменить
                </button>
              </span>
            </div>
          </div>
        </div>
      </div>
      <div
        v-if="!caseListMode && !approvalMode && (research || loaded)"
        class="doc-case-select doc-approvers"
      >
        <span>Согласовать</span>
        <div class="doc-case-select__field doc-approvers__body">
          <AddresseeField
            header="Согласовать"
            :value="approvers"
            :disabled="!canEditApprovers"
            @input="onApprovers"
          />
          <div
            v-for="(line, index) in approvalSentLines"
            :key="`${line}-${index}`"
            class="doc-approvers__sent"
          >
            Отправил: {{ line }}
          </div>
        </div>
      </div>
      <div
        v-if="!caseListMode && !approvalMode && (research || loaded)"
        class="doc-case-select"
      >
        <span>Дело</span>
        <Treeselect
          :value="selectedCaseId"
          class="doc-case-select__field"
          :multiple="false"
          :options="availableCases"
          placeholder="Выберите дело"
          no-options-text="Нет доступных дел"
          :append-to-body="true"
          @input="onMainCase"
        />
      </div>
      <div
        v-if="!caseListMode && !approvalMode && (research || loaded)"
        class="doc-case-select"
      >
        <span>Блок</span>
        <Treeselect
          :value="selectedBlockId"
          class="doc-case-select__field"
          :multiple="false"
          :options="availableBlocks"
          :disabled="!canChangeBlock"
          placeholder="Выберите блок"
          no-options-text="Нет доступных блоков"
          :append-to-body="true"
          @input="onMainBlock"
        />
      </div>
      <div
        v-if="!caseListMode && !approvalMode && approvalStatuses.length"
        class="group"
      >
        <div class="group-title">
          Согласование
        </div>
        <div class="fields">
          <div
            class="approval-status"
            :class="{ 'approval-status--view': !canCancelApproval }"
          >
            <div
              v-for="row in approvalStatuses"
              :key="row.id"
              class="approval-status__row"
            >
              <span class="approval-status__fio">{{ row.fio }}</span>
              <span
                class="approval-status__state"
                :class="`approval-status__state--${row.status}`"
              >{{ approvalStatusText(row.status) }}</span>
              <span class="approval-status__date">{{ row.decidedAt }}</span>
              <span class="approval-status__comment">{{ row.comment }}</span>
              <span
                v-if="canCancelApproval"
                class="approval-status__action"
              >
                <button
                  v-if="canCancelRow(row)"
                  class="btn btn-blue-nb approval-status__btn"
                  type="button"
                  @click="cancelApproval(row)"
                >
                  Отменить
                </button>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed, getCurrentInstance, onMounted, onUnmounted, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';
import { buildParaclinicResultFormData } from '@/api/buildParaclinicResultFormData';
import { vField, vGroup } from '@/components/visibility-triggers';
import DescriptiveForm from '@/forms/DescriptiveForm.vue';
import AddresseeField from '@/forms/Fields/AddresseeField.vue';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

const props = defineProps<{
  documentId?: number | null;
  caseId?: number | null;
  showCaseDocuments?: boolean;
  approvalMode?: boolean;
}>();

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'visibility-change'): void;
  (e: 'reviewed'): void;
  (e: 'approved'): void;
}>();

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const title = ref('');
const research = ref(null);
const issPk = ref<number | null>(null);
const loaded = ref(false);
const confirmed = ref(false);
const isHidden = ref(false);
const canHide = ref(false);
const canReset = ref(false);
const hasPrintTemplate = ref(false);
const inFavorite = ref(false);
const caseBlock = ref<{ id: number; createdAt: string; creator: string } | null>(null);
const caseTopic = ref('');
const savedCaseTopic = ref('');
const caseAccess = ref('[]');
const canEditCaseAccess = ref(false);
const caseComment = ref('');
const savedCaseComment = ref('');
const caseClosedAt = ref('');
const caseClosedBy = ref('');
const canEditCase = ref(false);
const canEditCaseTopic = ref(false);
const canCloseCase = ref(false);
const caseInFavorite = ref(false);
const selectedCaseId = ref<number | null>(null);
const availableCases = ref<{ id: number; label: string }[]>([]);
const selectedBlockId = ref<number | null>(null);
const availableBlocks = ref<{ id: number; label: string }[]>([]);
const canChangeBlock = ref(true);
const approvers = ref('[]');
const approvalSentSource = ref('[]');
const canEditApprovers = ref(false);
const canCancelApproval = ref(false);
type ApprovalStatusRow = {
  id: number;
  fio: string;
  status: string;
  decidedAt?: string;
  comment?: string;
};
const approvalStatuses = ref<ApprovalStatusRow[]>([]);
const anyApproverRejected = computed(() => (
  approvalStatuses.value.some(row => row.status === 'rejected')
));
const allApproversAgreed = computed(() => (
  approvalStatuses.value.length > 0
  && approvalStatuses.value.every(row => row.status === 'approved')
));
const approvalComment = ref('');
const currentDocPk = computed(() => Number(store.getters.currentDocPk) || 0);
const approvalButtonLabel = computed(() => (
  approvalComment.value.trim() ? 'Не согласен' : 'Согласен'
));
const canDecideRow = (row: ApprovalStatusRow) => (
  row.id === currentDocPk.value && row.status === 'waiting'
);
const canCancelRow = (row: ApprovalStatusRow) => (
  canCancelApproval.value && row.status !== 'waiting'
);
const approvalStatusText = (status: string) => {
  if (status === 'approved') {
    return 'Согласовано';
  }
  if (status === 'rejected') {
    return 'Не согласовано';
  }
  return 'Ожидает';
};
const approvalSentLines = computed(() => {
  let rows: { whoCreate?: string; createAtApprove?: string }[] = [];
  try {
    const parsed = JSON.parse(approvalSentSource.value);
    if (Array.isArray(parsed)) {
      rows = parsed;
    }
  } catch {
    rows = [];
  }
  const seen = new Set<string>();
  const lines: string[] = [];
  rows.forEach((row) => {
    const who = (row?.whoCreate || '').trim();
    const at = (row?.createAtApprove || '').trim();
    if (!who && !at) {
      return;
    }
    const line = [who, at].filter(Boolean).join(', ');
    if (seen.has(line)) {
      return;
    }
    seen.add(line);
    lines.push(line);
  });
  return lines;
});
const whoConfirmed = ref('');
const patient = {};

type CaseDocumentRow = {
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
  isHidden: boolean;
  canHide: boolean;
  canReset: boolean;
  hasPrintTemplate: boolean;
  whoConfirmed: string;
  caseId: number | null;
  availableCases: { id: number; label: string }[];
};

const caseDocuments = ref<CaseDocumentRow[]>([]);

const caseListMode = computed(() => Boolean((props.showCaseDocuments || props.caseId) && caseBlock.value));

const printHref = (id: number, format: 'docx' | 'pdf') => (
  `${window.location.origin}/api/document-manager/documents/print?id=${id}&format=${format}`
);

const caseDocumentHref = (id: number) => {
  const url = new URL(window.location.href);
  url.searchParams.set('document', String(id));
  return url.toString();
};

const caseDocumentLine = (row: { id: number; topic: string; typeTitle: string; createdAt: string; creator: string }) => (
  [String(row.id), row.topic, row.typeTitle, row.createdAt, row.creator].map(part => (part || '').trim() || '—').join(', ')
);

const blankDocumentBody = () => ({
  expanded: false,
  loading: false,
  loaded: false,
  research: null,
  issPk: null as number | null,
  confirmed: false,
  isHidden: false,
  canHide: false,
  canReset: false,
  hasPrintTemplate: false,
  whoConfirmed: '',
  caseId: null,
  availableCases: [],
});

const documentById = (id: number) => caseDocuments.value.find(item => item.id === id);

const patchDocument = (id: number, patch: Partial<CaseDocumentRow>) => {
  caseDocuments.value = caseDocuments.value.map(item => (
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
      isHidden: Boolean(result.isHidden),
      canHide: Boolean(result.canHide),
      canReset: Boolean(result.canReset),
      hasPrintTemplate: Boolean(result.hasPrintTemplate),
      whoConfirmed: result.whoConfirmed || '',
      caseId: result.case && !result.case.closedAt ? result.case.id : null,
      availableCases: result.availableCases || [],
      loaded: true,
      loading: false,
    });
    if (result.reviewedNow) {
      emit('reviewed');
    }
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
  const ids = caseDocuments.value.map(item => item.id);
  caseDocuments.value = caseDocuments.value.map(item => ({ ...item, expanded: true }));
  ids.forEach(id => {
    loadDocumentBody(id);
  });
};

const collapseAllDocuments = () => {
  caseDocuments.value = caseDocuments.value.map(item => ({ ...item, expanded: false }));
};

const visibilityStateFor = (formResearch) => {
  const groups = {};
  const fields = {};
  const igroups = formResearch?.groups || [];
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

const visibilityState = () => visibilityStateFor(research.value);

const applyFilesByField = (filesByField, formResearch = research.value) => {
  if (!filesByField || !formResearch?.groups) {
    return;
  }
  for (const group of formResearch.groups) {
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
  ...(caseBlock.value ? { caseTopic: caseTopic.value } : {}),
});

const saveRequest = async (payload) => {
  const { jsonPayload, formData } = buildParaclinicResultFormData(payload);
  if (formData) {
    return api('document-manager/documents/save', null, null, jsonPayload, formData);
  }
  return api('document-manager/documents/save', payload);
};

const fillCase = (caseData) => {
  if (!caseData) {
    return;
  }
  caseBlock.value = {
    id: caseData.id,
    createdAt: caseData.createdAt || '',
    creator: caseData.creator || '',
  };
  caseTopic.value = caseData.topic || '';
  savedCaseTopic.value = caseTopic.value;
  caseAccess.value = JSON.stringify(caseData.access || []);
  canEditCaseAccess.value = Boolean(caseData.canEditAccess);
  caseComment.value = caseData.comment || '';
  savedCaseComment.value = caseComment.value;
  caseClosedAt.value = caseData.closedAt || '';
  caseClosedBy.value = caseData.closedBy || '';
  canEditCase.value = Boolean(caseData.canEdit);
  canEditCaseTopic.value = Boolean(caseData.canEditTopic);
  canCloseCase.value = Boolean(caseData.canClose);
  caseInFavorite.value = Boolean(caseData.isFavorite);
  selectedCaseId.value = caseData.closedAt ? null : caseData.id;
  caseDocuments.value = (caseData.documents || []).map(row => ({
    id: row.id,
    topic: row.topic || '',
    typeTitle: row.typeTitle || '',
    createdAt: row.createdAt || '',
    creator: row.creator || '',
    ...blankDocumentBody(),
  }));
};

const casePayload = (extra: Record<string, unknown> = {}) => (
  props.caseId && !props.documentId
    ? { caseId: props.caseId, ...extra }
    : { id: props.documentId, ...extra }
);

const load = async () => {
  title.value = '';
  research.value = null;
  issPk.value = null;
  loaded.value = false;
  confirmed.value = false;
  isHidden.value = false;
  canHide.value = false;
  canReset.value = false;
  hasPrintTemplate.value = false;
  inFavorite.value = false;
  caseBlock.value = null;
  caseTopic.value = '';
  savedCaseTopic.value = '';
  caseAccess.value = '[]';
  canEditCaseAccess.value = false;
  caseComment.value = '';
  savedCaseComment.value = '';
  caseClosedAt.value = '';
  caseClosedBy.value = '';
  canEditCase.value = false;
  canEditCaseTopic.value = false;
  canCloseCase.value = false;
  caseInFavorite.value = false;
  selectedCaseId.value = null;
  availableCases.value = [];
  selectedBlockId.value = null;
  availableBlocks.value = [];
  canChangeBlock.value = true;
  approvers.value = '[]';
  approvalSentSource.value = '[]';
  canEditApprovers.value = false;
  canCancelApproval.value = false;
  approvalStatuses.value = [];
  approvalComment.value = '';
  caseDocuments.value = [];
  whoConfirmed.value = '';
  if (props.caseId && !props.documentId) {
    await store.dispatch(actions.INC_LOADING);
    try {
      const result = await api('document-manager/cases/details', { id: props.caseId });
      if (result?.ok) {
        fillCase(result);
      } else {
        root.$emit('msg', 'error', result?.message || 'Дело не найдено');
      }
    } finally {
      loaded.value = true;
      await store.dispatch(actions.DEC_LOADING);
    }
    return;
  }
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
      isHidden.value = Boolean(result.isHidden);
      canHide.value = Boolean(result.canHide);
      canReset.value = Boolean(result.canReset);
      hasPrintTemplate.value = Boolean(result.hasPrintTemplate);
      inFavorite.value = Boolean(result.isFavorite);
      fillCase(result.case);
      availableCases.value = result.availableCases || [];
      selectedBlockId.value = result.blockId || null;
      availableBlocks.value = result.availableBlocks || [];
      canChangeBlock.value = result.canChangeBlock !== false;
      approvers.value = JSON.stringify(result.approvers || []);
      approvalSentSource.value = approvers.value;
      canEditApprovers.value = Boolean(result.canEditApprovers);
      canCancelApproval.value = Boolean(result.canCancelApproval);
      approvalStatuses.value = result.approvalStatuses || [];
      whoConfirmed.value = result.whoConfirmed || '';
      if (result.reviewedNow) {
        emit('reviewed');
      }
    } else {
      root.$emit('msg', 'error', result?.message || 'Ошибка загрузки');
    }
  } finally {
    loaded.value = true;
    await store.dispatch(actions.DEC_LOADING);
  }
};

const saveCaseTopic = async () => {
  const anchored = Boolean(props.documentId || props.caseId);
  if (!canEditCaseTopic.value || !anchored || !caseBlock.value || caseTopic.value === savedCaseTopic.value) {
    return;
  }
  const topic = caseTopic.value.trim();
  if (!topic) {
    caseTopic.value = savedCaseTopic.value;
    root.$emit('msg', 'error', 'Укажите тему дела');
    return;
  }
  const result = await api('document-manager/cases/topic', casePayload({ topic }));
  if (result?.ok) {
    caseTopic.value = result.topic ?? topic;
    savedCaseTopic.value = caseTopic.value;
    root.$emit('msg', 'ok', 'Тема сохранена');
    emit('visibility-change');
  } else {
    caseTopic.value = savedCaseTopic.value;
    root.$emit('msg', 'error', result?.message || 'Не удалось сохранить тему');
  }
};

const saveCaseComment = async () => {
  const anchored = Boolean(props.documentId || props.caseId);
  if (!canEditCase.value || !anchored || !caseBlock.value || caseComment.value === savedCaseComment.value) {
    return;
  }
  const result = await api('document-manager/cases/comment', casePayload({ comment: caseComment.value }));
  if (result?.ok) {
    savedCaseComment.value = result.comment ?? caseComment.value;
    root.$emit('msg', 'ok', 'Комментарий сохранён');
  } else {
    root.$emit('msg', 'error', result?.message || 'Не удалось сохранить комментарий');
  }
};

const closeCase = async () => {
  const anchored = Boolean(props.documentId || props.caseId);
  if (!canCloseCase.value || !anchored || !caseBlock.value) {
    return;
  }
  const result = await api('document-manager/cases/close', casePayload());
  if (result?.ok) {
    caseClosedAt.value = result.closedAt || '';
    caseClosedBy.value = result.closedBy || '';
    canCloseCase.value = false;
    canEditCaseTopic.value = false;
    caseInFavorite.value = false;
    const closedId = caseBlock.value.id;
    availableCases.value = availableCases.value.filter(item => item.id !== closedId);
    if (selectedCaseId.value === closedId) {
      selectedCaseId.value = null;
    }
    root.$emit('msg', 'ok', 'Дело закрыто');
  } else {
    root.$emit('msg', 'error', result?.message || 'Не удалось закрыть дело');
  }
};

const assignDocumentCase = async (documentId: number, caseId: number | null) => {
  const result = await api('document-manager/documents/case', { id: documentId, caseId });
  if (!result?.ok) {
    root.$emit('msg', 'error', result?.message || 'Не удалось изменить дело');
    return null;
  }
  root.$emit('msg', 'ok', caseId ? 'Документ добавлен в дело' : 'Документ убран из дела');
  return result;
};

const assignDocumentBlock = async (documentId: number, blockId: number | null) => {
  const result = await api('document-manager/documents/block', { id: documentId, blockId });
  if (!result?.ok) {
    root.$emit('msg', 'error', result?.message || 'Не удалось изменить блок');
    return null;
  }
  root.$emit('msg', 'ok', blockId ? 'Документ добавлен в блок' : 'Документ убран из блока');
  return result;
};

const onMainBlock = async (blockId: number | null) => {
  const next = blockId || null;
  if (!props.documentId || !canChangeBlock.value || next === selectedBlockId.value) {
    return;
  }
  const previous = selectedBlockId.value;
  selectedBlockId.value = next;
  const result = await assignDocumentBlock(props.documentId, next);
  if (!result) {
    selectedBlockId.value = previous;
  }
};

const onMainCase = async (caseId: number | null) => {
  const next = caseId || null;
  if (!props.documentId || next === selectedCaseId.value) {
    return;
  }
  const previous = selectedCaseId.value;
  selectedCaseId.value = next;
  const result = await assignDocumentCase(props.documentId, next);
  if (!result) {
    selectedCaseId.value = previous;
    return;
  }
  if (!result.case) {
    caseBlock.value = null;
    caseTopic.value = '';
    savedCaseTopic.value = '';
    caseComment.value = '';
    savedCaseComment.value = '';
    caseClosedAt.value = '';
    caseClosedBy.value = '';
    canEditCase.value = false;
    canEditCaseTopic.value = false;
    canCloseCase.value = false;
    caseInFavorite.value = false;
    canEditCaseAccess.value = false;
    caseDocuments.value = [];
    return;
  }
  caseBlock.value = {
    id: result.case.id,
    createdAt: result.case.createdAt || '',
    creator: result.case.creator || '',
  };
  caseTopic.value = result.case.topic || '';
  savedCaseTopic.value = caseTopic.value;
  caseComment.value = result.case.comment || '';
  savedCaseComment.value = caseComment.value;
  caseClosedAt.value = result.case.closedAt || '';
  caseClosedBy.value = result.case.closedBy || '';
  canEditCase.value = Boolean(result.case.canEdit);
  canEditCaseTopic.value = Boolean(result.case.canEditTopic);
  canCloseCase.value = Boolean(result.case.canClose);
  caseInFavorite.value = Boolean(result.case.isFavorite);
  caseAccess.value = JSON.stringify(result.case.access || []);
  canEditCaseAccess.value = Boolean(result.case.canEditAccess);
};

const onRowCase = async (id: number, caseId: number | null) => {
  const current = documentById(id);
  if (!current) {
    return;
  }
  const next = caseId || null;
  if (next === current.caseId) {
    return;
  }
  const previous = current.caseId;
  patchDocument(id, { caseId: next });
  const result = await assignDocumentCase(id, next);
  if (!result) {
    patchDocument(id, { caseId: previous });
    return;
  }
  if (Number(id) !== Number(props.documentId)) {
    return;
  }
  selectedCaseId.value = result.case && !result.case.closedAt ? result.case.id : null;
  if (!result.case) {
    caseBlock.value = null;
    caseTopic.value = '';
    savedCaseTopic.value = '';
    caseComment.value = '';
    savedCaseComment.value = '';
    caseClosedAt.value = '';
    caseClosedBy.value = '';
    canEditCase.value = false;
    canEditCaseTopic.value = false;
    canCloseCase.value = false;
    caseInFavorite.value = false;
    canEditCaseAccess.value = false;
    caseDocuments.value = [];
    return;
  }
  caseBlock.value = {
    id: result.case.id,
    createdAt: result.case.createdAt || '',
    creator: result.case.creator || '',
  };
  caseTopic.value = result.case.topic || '';
  savedCaseTopic.value = caseTopic.value;
  caseComment.value = result.case.comment || '';
  savedCaseComment.value = caseComment.value;
  caseClosedAt.value = result.case.closedAt || '';
  caseClosedBy.value = result.case.closedBy || '';
  canEditCase.value = Boolean(result.case.canEdit);
  canEditCaseTopic.value = Boolean(result.case.canEditTopic);
  canCloseCase.value = Boolean(result.case.canClose);
  caseInFavorite.value = Boolean(result.case.isFavorite);
  caseAccess.value = JSON.stringify(result.case.access || []);
  canEditCaseAccess.value = Boolean(result.case.canEditAccess);
};

const onFavoritesChanged = (payload?: { id?: number; caseId?: number; favorite?: boolean; case?: boolean }) => {
  if (!payload) {
    return;
  }
  if (payload.case && Number(payload.caseId) === Number(caseBlock.value?.id)) {
    caseInFavorite.value = Boolean(payload.favorite);
    return;
  }
  if (Number(payload.id) !== Number(props.documentId)) {
    return;
  }
  if (payload.case) {
    caseInFavorite.value = Boolean(payload.favorite);
    return;
  }
  inFavorite.value = Boolean(payload.favorite);
};

const toggleCaseFavorite = async () => {
  if (!caseBlock.value) {
    return;
  }
  const payload = props.documentId
    ? { id: props.documentId, case: true }
    : { caseId: caseBlock.value.id };
  const result = await api('document-manager/record-favorites/toggle', payload);
  if (result?.ok) {
    caseInFavorite.value = Boolean(result.favorite);
    root.$emit('dou-favorites-changed', {
      id: props.documentId,
      caseId: caseBlock.value.id,
      favorite: result.favorite,
      case: true,
    });
  } else {
    root.$emit('msg', 'error', result?.message || 'Не удалось изменить избранное');
  }
};

const toggleRecordFavorite = async () => {
  if (!props.documentId) {
    return;
  }
  const result = await api('document-manager/record-favorites/toggle', { id: props.documentId });
  if (result?.ok) {
    inFavorite.value = Boolean(result.favorite);
    root.$emit('dou-favorites-changed', { id: props.documentId, favorite: result.favorite });
  } else {
    root.$emit('msg', 'error', result?.message || 'Не удалось изменить избранное');
  }
};

onMounted(() => {
  root.$on('dou-favorites-changed', onFavoritesChanged);
});

onUnmounted(() => {
  root.$off('dou-favorites-changed', onFavoritesChanged);
});

const approveMine = async () => {
  if (!props.documentId) {
    return;
  }
  const comment = approvalComment.value.trim();
  const result = await api('document-manager/documents/approve', {
    id: props.documentId,
    comment,
  });
  if (result?.ok) {
    approvalStatuses.value = result.approvalStatuses || [];
    approvalComment.value = '';
    root.$emit('msg', 'ok', comment ? 'Не согласовано' : 'Согласовано');
    emit('approved');
  } else {
    root.$emit('msg', 'error', result?.message || 'Не удалось согласовать');
  }
};

const cancelApproval = async (row: ApprovalStatusRow) => {
  if (!props.documentId || !canCancelRow(row)) {
    return;
  }
  const result = await api('document-manager/documents/approve-cancel', {
    id: props.documentId,
    employeeId: row.id,
  });
  if (result?.ok) {
    approvalStatuses.value = result.approvalStatuses || [];
    root.$emit('msg', 'ok', 'Согласование отменено');
    emit('approved');
  } else {
    root.$emit('msg', 'error', result?.message || 'Не удалось отменить согласование');
  }
};

const onApprovers = async (value: string) => {
  if (!props.documentId || !canEditApprovers.value || value === approvers.value) {
    return;
  }
  const previous = approvers.value;
  approvers.value = value;
  let members = [];
  try {
    members = JSON.parse(value);
  } catch {
    members = [];
  }
  const result = await api('document-manager/documents/approvers', { id: props.documentId, members });
  if (result?.ok) {
    approvers.value = JSON.stringify(result.approvers || members);
    approvalSentSource.value = approvers.value;
    if (result.approvalStatuses) {
      approvalStatuses.value = result.approvalStatuses;
    }
    root.$emit('msg', 'ok', 'Согласующие сохранены');
  } else {
    approvers.value = previous;
    root.$emit('msg', 'error', result?.message || 'Не удалось сохранить согласующих');
  }
};

const onCaseAccess = async (value: string) => {
  const anchored = Boolean(props.documentId || props.caseId);
  if (!canEditCaseAccess.value || !anchored || value === caseAccess.value) {
    return;
  }
  const previous = caseAccess.value;
  caseAccess.value = value;
  let members = [];
  try {
    members = JSON.parse(value);
  } catch {
    members = [];
  }
  const result = await api('document-manager/cases/access', casePayload({ members }));
  if (result?.ok) {
    caseAccess.value = JSON.stringify(result.access || members);
    root.$emit('msg', 'ok', 'Доступ сохранён');
  } else {
    caseAccess.value = previous;
    root.$emit('msg', 'error', result?.message || 'Не удалось сохранить доступ');
  }
};

const save = async () => {
  if (!props.documentId || !research.value || !issPk.value) {
    return false;
  }
  if (caseBlock.value && !caseTopic.value.trim()) {
    root.$emit('msg', 'error', 'Укажите тему дела');
    return false;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await saveRequest(savePayload(false));
    if (result?.ok) {
      applyFilesByField(result.files_by_field);
      root.$emit('msg', 'ok', 'Сохранено');
      emit('visibility-change');
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
  if (caseBlock.value && !caseTopic.value.trim()) {
    root.$emit('msg', 'error', 'Укажите тему дела');
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await saveRequest(savePayload(true));
    if (result?.ok) {
      applyFilesByField(result.files_by_field);
      confirmed.value = true;
      whoConfirmed.value = result.whoConfirmed || '';
      root.$emit('msg', 'ok', 'Подтверждено');
      emit('visibility-change');
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
      whoConfirmed.value = '';
      root.$emit('msg', 'ok', 'Подтверждение сброшено');
    } else {
      root.$emit('msg', 'error', result?.message || 'Ошибка сброса');
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const setHidden = async (hidden: boolean) => {
  if (!props.documentId) {
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/documents/hide', { id: props.documentId, hidden });
    if (result?.ok) {
      isHidden.value = Boolean(result.isHidden);
      root.$emit('msg', 'ok', hidden ? 'Документ скрыт' : 'Документ показан');
      emit('visibility-change');
    } else {
      root.$emit('msg', 'error', result?.message || 'Ошибка');
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const saveDocument = async (id: number) => {
  const current = documentById(id);
  if (!current?.research || !current.issPk) {
    return;
  }
  if (caseBlock.value && !caseTopic.value.trim()) {
    root.$emit('msg', 'error', 'Укажите тему дела');
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await saveRequest({
      data: { pk: current.issPk, research: current.research },
      with_confirm: false,
      visibility_state: visibilityStateFor(current.research),
      ...(caseBlock.value ? { caseTopic: caseTopic.value } : {}),
    });
    if (result?.ok) {
      applyFilesByField(result.files_by_field, current.research);
      root.$emit('msg', 'ok', 'Сохранено');
      emit('visibility-change');
    } else {
      root.$emit('msg', 'error', result?.message || 'Ошибка сохранения');
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const confirmDocument = async (id: number) => {
  const current = documentById(id);
  if (!current?.research || !current.issPk) {
    return;
  }
  if (caseBlock.value && !caseTopic.value.trim()) {
    root.$emit('msg', 'error', 'Укажите тему дела');
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await saveRequest({
      data: { pk: current.issPk, research: current.research },
      with_confirm: true,
      visibility_state: visibilityStateFor(current.research),
      ...(caseBlock.value ? { caseTopic: caseTopic.value } : {}),
    });
    if (result?.ok) {
      applyFilesByField(result.files_by_field, current.research);
      patchDocument(id, { confirmed: true, whoConfirmed: result.whoConfirmed || '' });
      root.$emit('msg', 'ok', 'Подтверждено');
      emit('visibility-change');
    } else {
      root.$emit('msg', 'error', result?.message || 'Ошибка подтверждения');
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const resetDocument = async (id: number) => {
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/documents/confirm-reset', { id });
    if (result?.ok) {
      patchDocument(id, { confirmed: false, whoConfirmed: '' });
      root.$emit('msg', 'ok', 'Подтверждение сброшено');
    } else {
      root.$emit('msg', 'error', result?.message || 'Ошибка сброса');
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const setDocumentHidden = async (id: number, hidden: boolean) => {
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/documents/hide', { id, hidden });
    if (result?.ok) {
      patchDocument(id, { isHidden: Boolean(result.isHidden) });
      root.$emit('msg', 'ok', hidden ? 'Документ скрыт' : 'Документ показан');
      emit('visibility-change');
    } else {
      root.$emit('msg', 'error', result?.message || 'Ошибка');
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

watch(() => [props.documentId, props.caseId], load, { immediate: true });
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
  display: flex;
  align-items: center;
  text-align: left;
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.research-title-text {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.doc-agreed {
  flex: 0 0 auto;
  margin-left: 10px;
  padding: 0 8px;
  height: 23px;
  line-height: 23px;
  background-color: #049372;
  color: #fff;
  font-size: 12px;
  font-weight: bold;
}

.doc-agreed--no {
  background-color: #da4453;
}

.favorite-star {
  flex: 0 0 auto;
  margin-right: 6px;
  padding: 0;
  border: none;
  background: transparent;
  color: #aab2bd;
  cursor: pointer;
  line-height: 1;
}

.favorite-star--on {
  color: #93046d;
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

.case-block {
  margin: 8px 10px;
  padding: 8px 10px;
  border: 1px solid #ccd1d9;
  background: #f5f7fa;
}

.case-block__label {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  font-weight: bold;
}

.case-block__topic {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 6px;

  span {
    flex: 0 0 auto;
    padding-top: 4px;
  }

  input,
  textarea {
    flex: 1;
    min-width: 0;
    padding: 2px 6px;
    border: 1px solid #ccd1d9;
    background: #fff;
  }

  input {
    height: 28px;
  }
}

.case-block__close-row {
  display: flex;
  justify-content: flex-end;
  margin: 6px 0;

  button {
    height: 34px;
    border-radius: 0;
  }
}

.case-block__meta {
  font-size: 13px;
  line-height: 1.4;
  color: #4a4a4a;
}

.case-block__gap {
  display: inline-block;
  width: 24px;
}

.case-block__access {
  display: flex;
  align-items: stretch;
  gap: 8px;
  margin-top: 6px;

  > span {
    flex: 0 0 auto;
    padding-top: 6px;
  }
}

.case-block__access-field {
  flex: 1;
  min-width: 0;
}

.case-docs {
  margin-top: 8px;
  border-top: 1px solid #ccd1d9;
}

.case-docs__head,
.case-docs__row {
  display: flex;
  flex-direction: row;
  align-items: baseline;
  gap: 6px;
  padding: 4px 0;
  font-size: 13px;
}

.case-docs__item {
  border-bottom: 1px solid #e6e9ed;
}

.case-docs__title {
  font-weight: bold;
}

.case-docs__toggle {
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

.case-docs__line {
  min-width: 0;
}

.case-docs__item--open {
  margin: 4px 0;
  background: #fff;
  border: 1px solid #ccd1d9;
}

.case-docs__link {
  flex: 0 0 auto;
  white-space: nowrap;
}

.doc-case-select {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 8px 10px;

  > span {
    flex: 0 0 auto;
  }
}

.doc-case-select__field {
  flex: 1;
  min-width: 0;
}

.doc-approvers {
  align-items: stretch;

  > span {
    padding-top: 6px;
  }
}

.doc-approvers__body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.doc-approvers__sent {
  line-height: 1.3;
}

.approval-status {
  display: grid;
  grid-template-columns: max-content max-content max-content 180px max-content;
  column-gap: 24px;
  row-gap: 6px;
  justify-content: start;
  align-items: center;
  margin: 4px 0;
  text-align: left;
}

.approval-status--view {
  grid-template-columns: max-content max-content max-content max-content;
}

.approval-status__row {
  display: contents;
}

.approval-status__fio,
.approval-status__state,
.approval-status__date,
.approval-status__comment,
.approval-status__action {
  justify-self: start;
  text-align: left;
}

.approval-status__comment-input {
  width: 180px;
  height: 23px;
  padding: 0 6px;
  font-size: 12px;
  line-height: 21px;
}

.approval-status__btn {
  height: 23px;
  min-height: 23px;
  padding: 0 8px;
  line-height: 21px;
  font-size: 12px;
}

.approval-status__btn--agree,
.approval-status__btn--agree:focus,
.approval-status__btn--agree:active {
  background-color: #049372;
  border-color: #049372;
  color: #fff;
}

.approval-status__btn--agree:hover {
  background-color: #0c8b6e;
  border-color: #0c8b6e;
  color: #fff;
}

.approval-status__state--approved {
  color: #1b7f3a;
}

.approval-status__state--rejected {
  color: #c0392b;
}

.approval-status__state--waiting {
  color: #000;
}

.case-docs__body {
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
  height: 34px;
  background-color: #f3f3f3;
  display: flex;
  flex-direction: row;
  margin-bottom: 10px;
  padding-right: 21px;

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

.print-link {
  align-self: center;
  margin-right: 12px;
  white-space: nowrap;
}
</style>
