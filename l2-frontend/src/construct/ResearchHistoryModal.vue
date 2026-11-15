<template>
  <div>
    <Modal
      show-footer="true"
      white-bg="true"
      margin-top
      margin-left-right="auto"
      max-width="760px"
      width="100%"
      @close="hide"
    >
      <span slot="header">История</span>
      <div
        slot="body"
        class="body"
      >
        <div v-if="rows.length === 0">
          Нет записей
        </div>
        <template v-else>
          <div class="history-head">
            <span>Дата и время</span>
            <span>Действие</span>
            <span>Пользователь</span>
          </div>
          <a
            v-for="row in rows"
            :key="row.id"
            href="#"
            class="history-row-link"
            @click.prevent="openBody(row)"
          >
            <span>{{ row.time }}</span>
            <span>{{ row.action }}</span>
            <span>{{ row.user }}</span>
          </a>
        </template>
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-8" />
          <div class="col-xs-4">
            <button
              type="button"
              class="btn btn-primary-nb btn-blue-nb"
              @click="hide"
            >
              Закрыть
            </button>
          </div>
        </div>
      </div>
    </Modal>
    <Modal
      v-if="selected"
      show-footer="true"
      white-bg="true"
      margin-top
      margin-left-right="auto"
      max-width="960px"
      width="100%"
      :z-index="5100"
      @close="closeBody"
    >
      <span slot="header">{{ selected.action }}</span>
      <div
        slot="body"
        class="body body-detail"
      >
        <div class="detail-meta">
          {{ selected.time }} — {{ selected.user }}
        </div>
        <pre
          v-if="selected.body"
          class="detail-json"
        >{{ selected.body }}</pre>
        <div v-else>
          Нет данных
        </div>
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-8" />
          <div class="col-xs-4">
            <button
              type="button"
              class="btn btn-primary-nb btn-blue-nb"
              @click="closeBody"
            >
              Назад
            </button>
          </div>
        </div>
      </div>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { getCurrentInstance, onMounted, ref } from 'vue';

import api from '@/api';
import Modal from '@/ui-cards/Modal.vue';
import { useStore } from '@/store';
import * as actions from '@/store/action-types';

interface HistoryRow {
  id: number;
  time: string;
  action: string;
  user: string;
}

interface HistoryDetail {
  time: string;
  action: string;
  user: string;
  body: string;
}

const props = defineProps({
  researchId: {
    type: Number,
    required: true,
  },
});

const emit = defineEmits(['hide']);
const store = useStore();
const root = getCurrentInstance().proxy.$root;
const rows = ref<HistoryRow[]>([]);
const selected = ref<HistoryDetail | null>(null);

const hide = () => {
  emit('hide');
};

const closeBody = () => {
  selected.value = null;
};

const formatBody = (body: string) => {
  try {
    return JSON.stringify(JSON.parse(body), null, 2);
  } catch (error) {
    return body;
  }
};

const openBody = async (row: HistoryRow) => {
  await store.dispatch(actions.INC_LOADING);
  const response = await api('researches/history-body', { pk: props.researchId, id: row.id });
  await store.dispatch(actions.DEC_LOADING);
  if (!response?.ok) {
    root.$emit('msg', 'error', response?.message || 'Не удалось загрузить изменения');
    return;
  }
  selected.value = {
    time: response.time,
    action: response.action,
    user: response.user,
    body: formatBody(response.body || ''),
  };
};

onMounted(async () => {
  await store.dispatch(actions.INC_LOADING);
  const response = await api('researches/history', { pk: props.researchId });
  await store.dispatch(actions.DEC_LOADING);
  if (response?.ok) {
    rows.value = response.rows || [];
    return;
  }
  root.$emit('msg', 'error', response?.message || 'Не удалось загрузить историю');
});
</script>

<style scoped lang="scss">
.body {
  width: 720px;
  max-width: 100%;
  min-height: 80px;
  max-height: 60vh;
  overflow: auto;
}

.body-detail {
  width: 920px;
}

.history-head,
.history-row-link {
  display: grid;
  grid-template-columns: 180px 130px 1fr;
  column-gap: 8px;
  padding: 6px 8px;
}

.history-head {
  font-weight: bold;
  border-bottom: 1px solid #ddd;
}

.history-row-link {
  color: #1b6ca8;
  text-decoration: underline;
  border-bottom: 1px solid #eee;
}

.history-row-link:hover {
  background: #f4f8fb;
}

.detail-meta {
  margin-bottom: 8px;
}

.detail-json {
  margin: 0;
  white-space: pre;
  font-size: 12px;
}
</style>
