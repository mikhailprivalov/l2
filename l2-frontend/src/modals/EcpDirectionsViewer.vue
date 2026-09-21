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
      <div class="ecp-meta">
        <div v-if="data.evnDirectionId">
          Направление ЕЦП №{{ data.evnDirectionId }}
        </div>
        <div v-if="data.evnLabRequestId">
          Заявка: {{ data.evnLabRequestId }}
        </div>
      </div>
      <div
        v-if="data.alreadyExists"
        class="ecp-notice"
      >
        Направление уже зарегистрировано в системе
      </div>
      <div
        v-else-if="validResearchIds.length === 0"
        class="ecp-notice"
      >
        Нет услуг для создания направления
      </div>
      <ol class="ecp-services">
        <li
          v-for="research in data.researches"
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
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-8 text-left">
          <button
            v-if="canCreate"
            type="button"
            class="btn btn-primary-nb btn-blue-nb"
            :disabled="saving"
            @click="createDirection(false)"
          >
            Сохранить
          </button>
          <button
            v-if="canCreate"
            type="button"
            class="btn btn-primary-nb btn-blue-nb"
            :disabled="saving"
            @click="createDirection(true)"
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
  evnDirectionId: string;
  evnLabRequestId: string;
  personId?: string;
  researches: EcpResearch[];
  alreadyExists: boolean;
}

const props = defineProps<{
  card: Record<string, any>;
  data: EcpDirectionData;
}>();

const instance = getCurrentInstance();
const api = instance.proxy.$api;
const root = instance.proxy.$root;
const refs = instance.proxy.$refs;
const store = instance.proxy.$store;
const notify = useNotify();

const saving = ref(false);

const validResearchIds = computed(() => (props.data.researches || [])
  .filter(research => !research.missing)
  .map(research => research.id));

const canCreate = computed(() => !props.data.alreadyExists && validResearchIds.value.length > 0);

const hideModal = () => {
  root.$emit('hide_ecp_directions');
  if (refs.modal) {
    (refs.modal as any).$el.style.display = 'none';
  }
};

const createDirection = async (printAfter: boolean) => {
  if (saving.value || !canCreate.value) {
    return;
  }
  saving.value = true;
  await store.dispatch(actions.INC_LOADING);
  try {
    const {
      ok, message, direction, directions,
    } = await api('directions/create-from-ecp', {
      card_pk: props.card.pk,
      researches: validResearchIds.value,
      EvnDirectionId: props.data.evnDirectionId,
      EvnLabRequest_id: props.data.evnLabRequestId,
    });
    if (!ok) {
      notify.error(message || 'Не удалось создать направление');
      return;
    }
    notify.ok(message || `Направление создано: ${direction}`);
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

.ecp-meta {
  margin-bottom: 10px;
  font-weight: 600;
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
