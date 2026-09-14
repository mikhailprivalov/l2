<template>
  <div
    :class="{ [$style.direction]: true, [$style.directionCito]: props.request.cito }"
    @click="handleCardClick"
  >
    <div :class="[$style.topPart, props.request.cito && $style.citoColor]">
      <div :class="$style.topLeft">
        <span
          v-if="props.request.cito"
          :class="$style.citoBadge"
        >
          CITO
        </span>
        <span :class="$style.datetime">
          {{ props.request.datetime }}<template v-if="props.request.orderDate"> {{ props.request.orderDate }}</template>
        </span>
      </div>
      <span
        :class="$style.patient"
        :title="props.request.patient"
      >{{ props.request.patient }}</span>
      <span
        v-if="showClinic"
        :class="$style.clinic"
        :title="props.request.clinic"
      >{{ props.request.clinic }}</span>
      <span :class="$style.requestId">{{ props.request.id }}</span>
      <div class="topBtn">
        <button
          v-if="showAcceptButton()"
          class="btn btn-sm btn-not-accepted"
          :disabled="processing"
          @click="handleRequestAction(true)"
        >
          принять <i class="fa-regular fa-square" />
        </button>
        <button
          v-else-if="showCancelButton()"
          v-tippy
          class="btn btn-sm btn-blue-nb"
          title="отменить принятие"
          :disabled="processing"
          @click="handleRequestAction(false)"
        >
          принято <i class="fa fa-square-check" />
        </button>
      </div>
    </div>
    <div
      v-if="props.request.research"
      :class="$style.infoRow"
      :title="props.request.research"
    >
      {{ props.request.research }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';

import api from '@/api';
import useNotify from '@/hooks/useNotify';

export type Request = {
  id: number;
  patient: string;
  clinic: string;
  datetime: string;
  orderDate?: string;
  research: string;
  podrzdeleniye?: string;
  cardId: number;
  waitFill: boolean;
  cito?: boolean;
  accepted: boolean;
  acceptedByCurrentUser: boolean;
};

interface Props {
  request: Request;
  hospitalId?: number;
}

const props = withDefaults(defineProps<Props>(), {
  hospitalId: -1,
});

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'request-accepted', data: { requestId: number; accepted: boolean; acceptedByCurrentUser: boolean }): void;
  (e: 'card-clicked', request: Request): void;
}>();

const notify = useNotify();
const processing = ref(false);

const showClinic = computed(() => props.hospitalId === -1 && Boolean(props.request.clinic));

const showAcceptButton = () => props.request.waitFill && !props.request.accepted;

const showCancelButton = () => props.request.waitFill && props.request.accepted && props.request.acceptedByCurrentUser;

const handleRequestAction = async (accept: boolean) => {
  if (processing.value) return;

  const endpoint = accept ? 'requests/accept' : 'requests/cancel-accept';
  const successMessage = accept ? 'Заявка успешно принята' : 'Принятие заявки отменено';
  const errorMessage = accept ? 'Ошибка при принятии заявки' : 'Ошибка при отмене принятия заявки';
  const newAcceptedState = accept;
  const newAcceptedByCurrentUser = accept;

  try {
    processing.value = true;
    emit('request-accepted', {
      requestId: props.request.id,
      accepted: newAcceptedState,
      acceptedByCurrentUser: newAcceptedByCurrentUser,
    });

    const response = await api(endpoint, { requestId: props.request.id, hospitalId: props.hospitalId });

    if (response.ok) {
      notify.ok(successMessage);
    } else {
      emit('request-accepted', {
        requestId: props.request.id,
        accepted: !newAcceptedState,
        acceptedByCurrentUser: !newAcceptedByCurrentUser,
      });
      notify.error(response.message || errorMessage);
    }
  } catch (error) {
    emit('request-accepted', {
      requestId: props.request.id,
      accepted: !newAcceptedState,
      acceptedByCurrentUser: !newAcceptedByCurrentUser,
    });
    notify.error(errorMessage);
  } finally {
    processing.value = false;
  }
};

const handleCardClick = (event: Event) => {
  const target = event.target as HTMLElement;
  if (!target.closest('.btn')) {
    emit('card-clicked', props.request);
  }
};
</script>

<style module lang="scss">
.direction {
  padding: 5px;
  margin: 5px;
  border-radius: 5px;
  border: 1px solid rgba(0, 0, 0, 0.14);
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: #049372;
    background: linear-gradient(to bottom, rgba(4, 147, 114, 0.05) 0%, rgba(4, 147, 114, 0.15) 100%);
  }
}

.directionCito {
  border-color: #ff6b6b;
}

.citoColor {
  color: #ff6b6b;
}

.topLeft {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  white-space: nowrap;
}

.patient,
.clinic {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.requestId {
  flex: 0 0 auto;
  color: #434A54;
  font-size: 13px;
  font-weight: 600;
  vertical-align: middle;
}

.citoBadge {
  display: inline-block;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  margin-right: 2px;
  border-radius: 3px;
  background-color: #ff6b6b;
  color: white;
  letter-spacing: 0.5px;
  vertical-align: middle;
}

.datetime {
  font-family: 'Lucida Console', Monaco, monospace;
  vertical-align: middle;
}

.infoRow {
  padding: 3px;
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.topPart {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}
</style>

<style scoped lang="scss">
.topBtn {
  flex: 0 0 auto;
  width: 79px;
  text-align: right;

  .btn {
    padding: 2px 6px;

    i {
      vertical-align: middle;
      margin-left: 1px;
    }

    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    &.btn-not-accepted {
      background-color: transparent;
      color: #434A54;

      &:hover {
        background-color: #434A5411;
      }
    }
  }
}
</style>
