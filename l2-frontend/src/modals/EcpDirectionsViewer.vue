<template>
  <Modal
    ref="modal"
    show-footer="true"
    white-bg="true"
    min-width="640px"
    max-width="860px"
    width="70%"
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
        <div class="ecp-meta">
          <div v-if="direction.direction_id">
            Направление ЕЦП №{{ direction.direction_id }}
          </div>
          <div v-if="direction.evnLabRequestId">
            Заявка: {{ direction.evnLabRequestId }}
          </div>
        </div>
        <div
          v-if="direction.alreadyExists"
          class="ecp-notice"
        >
          Направление уже зарегистрировано в системе - {{ direction.localDirectionId }}
        </div>
        <div
          v-else-if="validResearchIds(direction).length === 0"
          class="ecp-notice"
        >
          Нет услуг для создания направления
        </div>
        <ol class="ecp-services">
          <li
            v-for="research in direction.researches"
            :key="research.id"
            :class="{ missing: research.missing }"
          >
            <template v-if="research.missing">
              Услуга с id {{ research.id }} не найдена в L2
            </template>
            <template v-else>
              {{ research.title }}
            </template>
          </li>
        </ol>
        <div
          v-if="directions.length > 1 && canCreate(direction)"
          class="row ecp-actions"
        >
          <div class="col-xs-6">
            <button
              type="button"
              class="btn btn-primary-nb btn-blue-nb"
              :disabled="saving"
              @click="createDirection(direction, false)"
            >
              Сохранить
            </button>
          </div>
          <div class="col-xs-6">
            <button
              type="button"
              class="btn btn-primary-nb btn-blue-nb"
              :disabled="saving"
              @click="createDirection(direction, true)"
            >
              Сохранить и печать
            </button>
          </div>
        </div>
      </div>
    </div>
    <div slot="footer">
      <div class="row">
        <template v-if="singleDirection && canCreate(singleDirection)">
          <div class="col-xs-4">
            <button
              type="button"
              class="btn btn-primary-nb btn-blue-nb"
              :disabled="saving"
              @click="createDirection(singleDirection, false)"
            >
              Сохранить
            </button>
          </div>
          <div class="col-xs-4">
            <button
              type="button"
              class="btn btn-primary-nb btn-blue-nb"
              :disabled="saving"
              @click="createDirection(singleDirection, true)"
            >
              Сохранить и печать
            </button>
          </div>
          <div class="col-xs-4">
            <button
              type="button"
              class="btn btn-primary-nb btn-blue-nb"
              :disabled="saving"
              @click="hideModal"
            >
              Закрыть
            </button>
          </div>
        </template>
        <div
          v-else
          class="col-xs-12"
        >
          <button
            type="button"
            class="btn btn-primary-nb btn-blue-nb"
            :disabled="saving"
            @click="hideModal"
          >
            Закрыть
          </button>
        </div>
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
  missing: boolean;
}

interface EcpDirectionData {
  direction_id: string;
  evnLabRequestId: string;
  personId?: string;
  researches: EcpResearch[];
  alreadyExists: boolean;
  localDirectionId?: number | null;
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

const singleDirection = computed(() => (props.directions.length === 1 ? props.directions[0] : null));

const validResearchIds = (direction: EcpDirectionData) => (direction.researches || [])
  .filter(research => !research.missing)
  .map(research => research.id);

const canCreate = (direction: EcpDirectionData) => !direction.alreadyExists && validResearchIds(direction).length > 0;

const hideModal = () => {
  root.$emit('hide_ecp_directions');
  if (refs.modal) {
    (refs.modal as any).$el.style.display = 'none';
  }
};

const createDirection = async (direction: EcpDirectionData, printAfter: boolean) => {
  if (saving.value || !canCreate(direction)) {
    return;
  }
  saving.value = true;
  await store.dispatch(actions.INC_LOADING);
  try {
    const {
      ok, message, direction: createdId, directions,
    } = await api('directions/create-from-ecp', {
      card_pk: props.card.pk,
      researches: validResearchIds(direction),
      EvnDirectionId: direction.direction_id,
      EvnLabRequest_id: direction.evnLabRequestId,
    });
    if (!ok) {
      notify.error(message || 'Не удалось создать направление');
      return;
    }
    notify.ok(message || `Направление создано: ${createdId}`);
    root.$emit('researches-picker:refresh');
    if (printAfter && directions?.length) {
      root.$emit('print:directions', directions);
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

.ecp-meta {
  margin-bottom: 10px;
  font-weight: 600;
}

.ecp-actions {
  margin-top: 12px;
}

.ecp-notice {
  margin-bottom: 10px;
  color: #a94442;
}

.ecp-services {
  padding-left: 22px;
  margin: 0;

  li {
    margin-bottom: 6px;
  }

  .missing {
    color: #a94442;
  }
}

::v-deep .panel-flt {
  margin: 41px auto;
}

.btn + .btn {
  margin-left: 8px;
}
</style>
