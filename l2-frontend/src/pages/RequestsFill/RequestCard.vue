<template>
  <div
    class="direction"
    @click="handleCardClick"
  >
    <div>{{ props.request.clinic }}</div>
    <div class="research-row">
      <div class="row">
        <div class="col-xs-5">
          {{ props.request.datetime }}
          <span
            v-if="props.request.cito"
            class="cito-badge"
          >
            CITO
          </span>
        </div>
        <div class="col-xs-7 text-right">
          <span
            class="fill-status"
            :class="getStatusClass()"
          >
            <button
              v-if="showAcceptButton()"
              class="btn btn-sm btn-blue-nb"
              :disabled="processing"
              @click="handleRequestAction(true)"
            >
              {{ processing ? 'Принимаю...' : 'принять' }}
            </button>
            <button
              v-else-if="showCancelButton()"
              class="btn btn-sm btn-blue-nb"
              :disabled="processing"
              @click="handleRequestAction(false)"
            >
              {{ processing ? 'Отменяю...' : 'отменить принятие' }}
            </button>
            <div v-else />
          </span>
        </div>
      </div>
      <div class="research-row">
        <span class="request-id">{{ props.request.id }}</span> {{ props.request.patient }}
      </div>
      <div class="research-row">
        {{ props.request.research }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

import api from '@/api';
import useNotify from '@/hooks/useNotify';

export type Request = {
  id: number;
  patient: string;
  clinic: string;
  datetime: string;
  research: string;
  cardId: number;
  waitFill: boolean;
  cito?: boolean;
  accepted: boolean;
  acceptedByCurrentUser: boolean;
};

const props = defineProps<{ request: Request }>();

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'request-accepted', data: { requestId: number; accepted: boolean; acceptedByCurrentUser: boolean }): void;
  (e: 'card-clicked', request: Request): void;
}>();

const notify = useNotify();
const processing = ref(false);

const getStatusClass = () => {
  if (!props.request.waitFill) return 'fill-status--done';
  if (props.request.accepted) return 'fill-status--accepted';
  return 'fill-status--wait';
};

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

    const response = await api(endpoint, { requestId: props.request.id });

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

<style scoped lang="scss">
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
.research-row {
  margin-top: 3px;
  margin-bottom: 3px;
  padding: 3px;
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);
}
.fill-status {
  font-size: 12px;
  font-weight: 500;

  .btn {
    padding: 3px;
    margin-left: 5px;

    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    &.btn-orange-nb {
      background-color: #f39c12;
      color: white;
      border: 1px solid #e67e22;

      &:hover:not(:disabled) {
        background-color: #e67e22;
      }
    }
  }
}
.fill-status--wait {
  color: #1448f4;
}
.fill-status--accepted {
  color: #049372;
}
.fill-status--done {
  color: #2ecc40;
}
.cito-badge {
  display: inline-block;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  margin-left: 8px;
  border-radius: 3px;
  background-color: #ff6b6b;
  color: white;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.request-id {
  font-size: 13px;
  color: #049372;
  font-weight: 600;
  background: #f0f9f7;
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
}
</style>
