<template>
  <Modal
    ref="modal"
    show-footer="true"
    white-bg="true"
    min-width="860px"
    max-width="1120px"
    width="84%"
    margin-left-right="auto"
    margin-top
    @close="hideModal"
  >
    <span slot="header">Направления из ЕЦП. Пациент: {{ card.family }} {{ card.name }} {{ card.twoname }},
      {{ card.birthday }} ({{ card.age }})</span>
    <div
      slot="body"
      class="ecp-body"
    >
      <div
        v-for="direction in directions"
        :key="direction.direction_id"
        class="ecp-direction"
      >
        <table class="ecp-table">
          <colgroup>
            <col class="ecp-col-meta">
            <col>
            <col>
          </colgroup>
          <thead>
            <tr>
              <th>Направление</th>
              <th>Услуги в ЕЦП</th>
              <th>Услуги в L2</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(research, idx) in rowsOf(direction)"
              :key="rowKey(direction, research, idx)"
            >
              <td
                v-if="idx === 0"
                :rowspan="rowsOf(direction).length"
                class="ecp-meta"
              >
                <div v-if="direction.direction_id">
                  Направление ЕЦП №{{ direction.direction_id }}
                  <template v-if="direction.setDate">
                    - {{ direction.setDate }}
                  </template>
                </div>
                <div v-if="direction.evnLabRequestId">
                  Заявка: {{ direction.evnLabRequestId }}
                </div>
                <div
                  v-if="isRegistered(direction)"
                  class="ecp-notice"
                >
                  Направление уже зарегистрировано в системе - {{ registeredId(direction) }}
                </div>
                <div
                  v-if="isRegistered(direction) && direction.localCancelled"
                  class="ecp-notice"
                >
                  Направление отменено
                </div>
                <div
                  v-if="isRegistered(direction) && missingTitles(direction)"
                  class="ecp-notice"
                >
                  В ЕЦП есть, в направлении нет: {{ missingTitles(direction) }}
                </div>
                <div
                  v-if="isRegistered(direction) && extraTitles(direction)"
                  class="ecp-notice"
                >
                  В направлении есть, в ЕЦП нет: {{ extraTitles(direction) }}
                </div>
                <button
                  v-if="canAddMissing(direction)"
                  type="button"
                  class="btn btn-blue-nb ecp-btn ecp-add"
                  :disabled="saving"
                  @click="addMissing(direction)"
                >
                  Добавить недостающие
                </button>
                <div
                  v-if="!isRegistered(direction) && validResearchIds(direction).length === 0"
                  class="ecp-notice"
                >
                  Нет услуг для создания направления
                </div>
              </td>
              <td>
                <template v-if="!isEmptyRow(direction)">
                  {{ research.ecpTitle || research.title }}
                </template>
              </td>
              <td :class="{ missing: research.missing && !isEmptyRow(direction) }">
                <template v-if="!isEmptyRow(direction)">
                  {{ research.missing ? 'не найдена' : research.title }}
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <div slot="footer">
      <div class="ecp-footer">
        <button
          type="button"
          class="btn btn-blue-nb ecp-btn"
          :disabled="saving || !canSave"
          @click="createDirections(true)"
        >
          Сохранить и печать
        </button>
        <button
          type="button"
          class="btn btn-blue-nb ecp-btn"
          :disabled="saving || !canSave"
          @click="createDirections(false)"
        >
          Сохранить
        </button>
        <button
          type="button"
          class="btn btn-blue-nb ecp-btn"
          :disabled="saving"
          @click="hideModal"
        >
          Закрыть
        </button>
      </div>
    </div>
  </Modal>
</template>

<script setup lang="ts">
import { computed, getCurrentInstance, ref } from 'vue';

import Modal from '@/ui-cards/Modal.vue';
import * as actions from '@/store/action-types';
import useNotify from '@/hooks/useNotify';

interface EcpResearch {
  id: number;
  title: string | null;
  ecpTitle?: string | null;
  missing: boolean;
}

interface EcpServiceRef {
  id: number;
  title: string | null;
  ecpTitle?: string | null;
  count?: number;
}

interface EcpDirectionData {
  direction_id: string;
  evnLabRequestId: string;
  personId?: string;
  setDate?: string | null;
  researches: EcpResearch[];
  alreadyExists: boolean;
  localDirectionId?: number | null;
  localCancelled?: boolean;
  missingResearches?: EcpServiceRef[];
  extraResearches?: EcpServiceRef[];
}

const props = defineProps<{
  card: Record<string, any>;
  directions: EcpDirectionData[];
}>();

const instance = getCurrentInstance();
const api = instance.proxy.$api;
const root = instance.proxy.$root;
const refs = instance.proxy.$refs;
const store = instance.proxy.$store;
const notify = useNotify();

const saving = ref(false);
const createdByEcpId = ref<Record<string, number>>({});
const addedResearchIds = ref<Record<string, number[]>>({});

const rowsOf = (direction: EcpDirectionData) => (
  direction.researches?.length
    ? direction.researches
    : [{
      id: 0, title: '', ecpTitle: '', missing: false,
    }]
);

const isEmptyRow = (direction: EcpDirectionData) => !direction.researches?.length;

const rowKey = (direction: EcpDirectionData, research: EcpResearch, idx: number) => {
  if (isEmptyRow(direction)) {
    return 'empty';
  }
  return research.missing
    ? `missing-${idx}-${research.ecpTitle || research.title}`
    : `${research.id}-${idx}`;
};

const validResearchIds = (direction: EcpDirectionData) => (direction.researches || [])
  .filter(research => !research.missing)
  .map(research => research.id);

const registeredId = (direction: EcpDirectionData) => (
  createdByEcpId.value[direction.direction_id] || direction.localDirectionId || null
);

const isRegistered = (direction: EcpDirectionData) => (
  direction.alreadyExists || Boolean(createdByEcpId.value[direction.direction_id])
);

const canCreate = (direction: EcpDirectionData) => (
  !isRegistered(direction) && validResearchIds(direction).length > 0
);

const missingOf = (direction: EcpDirectionData) => {
  const added = new Set(addedResearchIds.value[direction.direction_id] || []);
  return (direction.missingResearches || []).filter(item => !added.has(item.id));
};

const titlesOf = (items: EcpServiceRef[]) => items
  .map(item => item.title || item.ecpTitle || '')
  .filter(Boolean)
  .join(', ');

const missingTitles = (direction: EcpDirectionData) => titlesOf(missingOf(direction));

const extraTitles = (direction: EcpDirectionData) => titlesOf(direction.extraResearches || []);

const canAddMissing = (direction: EcpDirectionData) => (
  isRegistered(direction) && !direction.localCancelled && missingOf(direction).length > 0
);

const creatableDirections = computed(() => props.directions.filter(canCreate));
const canSave = computed(() => creatableDirections.value.length > 0);

const addMissing = async (direction: EcpDirectionData) => {
  const localId = registeredId(direction);
  const missing = missingOf(direction);
  if (saving.value || !localId || !missing.length || direction.localCancelled) {
    return;
  }
  saving.value = true;
  await store.dispatch(actions.INC_LOADING);
  try {
    const { ok, message, added } = await api('directions/update-from-ecp', {
      direction_pk: localId,
      researches: missing.map(item => item.id),
    });
    if (!ok) {
      notify.error(message || 'Не удалось добавить услуги');
      return;
    }
    const ids = (added || []).map(item => item.id).filter(Boolean);
    addedResearchIds.value = {
      ...addedResearchIds.value,
      [direction.direction_id]: [
        ...(addedResearchIds.value[direction.direction_id] || []),
        ...ids,
      ],
    };
    notify.ok(message || 'Услуги добавлены');
    root.$emit('researches-picker:refresh');
  } finally {
    saving.value = false;
    await store.dispatch(actions.DEC_LOADING);
  }
};

const hideModal = () => {
  root.$emit('hide_ecp_directions');
  if (refs.modal) {
    (refs.modal as any).$el.style.display = 'none';
  }
};

const createDirections = async (printAfter: boolean) => {
  if (saving.value || !canSave.value) {
    return;
  }
  saving.value = true;
  await store.dispatch(actions.INC_LOADING);
  const createdIds: number[] = [];
  try {
    for (const direction of creatableDirections.value) {
      const {
        ok, message, direction: createdId, directions: created,
      } = await api('directions/create-from-ecp', {
        card_pk: props.card.pk,
        researches: validResearchIds(direction),
        EvnDirectionId: direction.direction_id,
        EvnLabRequest_id: direction.evnLabRequestId,
      });
      if (!ok) {
        notify.error(message || 'Не удалось создать направление');
        if (createdIds.length) {
          root.$emit('researches-picker:refresh');
        }
        return;
      }
      const ids = (created?.length ? created : [createdId]).filter(Boolean);
      createdIds.push(...ids);
      createdByEcpId.value = {
        ...createdByEcpId.value,
        [direction.direction_id]: createdId,
      };
    }
    const createdText = createdIds.join(', ');
    notify.ok(createdIds.length > 1
      ? `Направления созданы: ${createdText}`
      : `Направление создано: ${createdText}`);
    root.$emit('researches-picker:refresh');
    if (printAfter && createdIds.length) {
      root.$emit('print:directions', createdIds);
    }
    hideModal();
  } finally {
    saving.value = false;
    await store.dispatch(actions.DEC_LOADING);
  }
};
</script>

<style scoped lang="scss">
.ecp-body {
  min-height: 180px;
  padding: 8px 4px;
}

.ecp-direction + .ecp-direction {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ddd;
}

.ecp-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;

  th,
  td {
    border: 1px solid #e6e9ed;
    padding: 8px 10px;
    vertical-align: top;
    font-weight: normal;
  }

  th {
    font-weight: 600;
    background: #f5f7fa;
  }
}

.ecp-col-meta {
  width: 42%;
}

.ecp-meta {
  font-weight: 600;
}

.ecp-footer {
  display: flex;
  justify-content: flex-end;
}

.ecp-notice {
  margin-top: 10px;
  font-weight: normal;
  color: #a94442;
}

.ecp-add {
  margin-top: 8px;
}

.missing {
  color: #a94442;
}

.ecp-btn.btn,
.ecp-btn.btn:hover,
.ecp-btn.btn:focus,
.ecp-btn.btn:active {
  width: auto;
  height: 34px;
  padding: 0 12px;
  border-radius: 0;
  font-size: 12px;
  line-height: 32px;
  color: #fff !important;
  box-sizing: border-box;
}

::v-deep .panel-flt {
  margin: 41px auto;
}
</style>
