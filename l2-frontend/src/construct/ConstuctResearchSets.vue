<template>
  <div>
    <h4>
      Наборы
    </h4>
    <Treeselect
      v-model="currentSet"
      :options="sets.data"
      placeholder="Выберите набор"
      value-format="object"
    />
    <div class="title-set">
      <table class="table">
        <colgroup>
          <col>
          <col
            v-if="setIsSelected"
            width="40"
          >
          <col
            v-if="!setIsHidden"
            width="100"
          >
        </colgroup>
        <tr>
          <td class="border">
            <input
              v-model.trim="titleSet"
              class="form-control b"
            >
          </td>
          <td
            v-if="setIsSelected"
            class="border"
          >
            <div class="button">
              <button
                v-tippy
                class="btn last btn-blue-nb nbr"
                :title="setIsHidden ? 'Отменить скрытие' : 'Скрыть набор'"
                @click="updateSetHiding"
              >
                <i :class="setIsHidden ?'fa fa-eye' : 'fa fa-times'" />
              </button>
            </div>
          </td>
          <td
            v-if="!setIsHidden"
            class="border"
          >
            <div class="button">
              <button
                v-tippy
                class="btn last btn-blue-nb nbr"
                :title="setIsSelected ? 'Сохранить набор' : 'Добавить набор'"
                :disabled="!titleSet"
                @click="updateSet"
              >
                {{ setIsSelected ? 'Сохранить' : 'Добавить' }}
              </button>
            </div>
          </td>
        </tr>
      </table>
    </div>
    <h4 v-if="setIsSelected">
      Исследования
    </h4>
    <div
      v-if="setIsSelected"
      class="card-no-hover card card-1"
    >
      <div class="scroll">
        <table class="table">
          <colgroup>
            <col
              v-if="!setIsHidden"
              width="85"
            >
            <col>
          </colgroup>
          <tr
            v-if="researchesInSet.length === 0"
            class="text-center"
          >
            <td
              colspan="2"
            >
              Нет данных
            </td>
          </tr>
          <tr
            v-for="(i) in researchesInSet"
            :key="i.id"
          >
            <td
              v-if="!setIsHidden"
              class="border"
            >
              <div class="button">
                <button
                  class="btn last btn-blue-nb nbr"
                  :disabled="isFirstRow(i.order)"
                  @click="updateOrder(i, 'inc_order')"
                >
                  <i class="glyphicon glyphicon-arrow-up" />
                </button>
                <button
                  class="btn last btn-blue-nb nbr"
                  :disabled="isLastRow(i.order)"
                  @click="updateOrder(i, 'dec_order')"
                >
                  <i class="glyphicon glyphicon-arrow-down" />
                </button>
              </div>
            </td>
            <VueTippyTd
              class="research border padding-left"
              :text="i.research.label"
            />
          </tr>
        </table>
      </div>
    </div>
    <h4 v-if="setIsSelected && !setIsHidden">
      Добавить исследование в набор
    </h4>
    <div v-if="setIsSelected && !setIsHidden">
      <table>
        <colgroup>
          <col>
          <col width="100">
        </colgroup>
        <tr>
          <td>
            <Treeselect
              v-model="currentResearch"
              :options="researches.data"
              :disable-branch-nodes="true"
              :append-to-body="true"
              placeholder="Исследование"
              class="nba"
            />
          </td>
          <td>
            <div class="button">
              <button
                v-tippy
                class="btn last btn-blue-nb nbr"
                title="Добавить исследование"
                :disabled="!currentResearch"
                @click="addResearchInSet"
              >
                Добавить
              </button>
            </div>
          </td>
        </tr>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import Treeselect from '@riophae/vue-treeselect';
import {
  computed, getCurrentInstance, onMounted, ref, watch,
} from 'vue';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import VueTippyTd from '@/construct/VueTippyTd.vue';
import api from '@/api';
import * as actions from '@/store/action-types';
import { useStore } from '@/store';

const store = useStore();
const vm = getCurrentInstance().proxy;
const root = vm.$root;

const currentSet = ref<any>(null);
const currentResearch = ref<number | null>(null);
const sets = ref<any>({ data: [] });
const titleSet = ref('');
const hideStatus = ref<any>(false);
const researchesInSet = ref<any[]>([]);
const researches = ref<any>({ data: [] });

const setIsSelected = computed(() => !!currentSet.value);
const setIsHidden = computed(() => hideStatus.value.ok);

const minMaxOrder = computed(() => {
  let min = 0;
  let max = 0;
  for (const row of researchesInSet.value) {
    if (min === 0) {
      min = row.order;
    } else {
      min = Math.min(min, row.order);
    }
    max = Math.max(max, row.order);
  }
  return { min, max };
});

const checkSetHidden = async () => {
  if (setIsSelected.value) {
    hideStatus.value = await api('/check-set-hidden', currentSet.value.id);
  }
};

const getResearchesInSet = async () => {
  const result = await api('/get-researches-in-set', currentSet.value.id);
  researchesInSet.value = result.data;
};

watch(currentSet, () => {
  if (!currentSet.value) {
    titleSet.value = '';
  } else {
    checkSetHidden();
    getResearchesInSet();
    titleSet.value = currentSet.value.label;
  }
});

const updateOrder = async (research: any, action: string) => {
  await store.dispatch(actions.INC_LOADING);
  const { ok, message } = await api('/update-order-in-set', {
    id: research.id, set: currentSet.value.id, order: research.order, action,
  });
  await store.dispatch(actions.DEC_LOADING);
  if (ok) {
    root.$emit('msg', 'ok', 'Порядок изменён');
    await getResearchesInSet();
  } else {
    root.$emit('msg', 'error', message);
  }
};

const isFirstRow = (order: number) => order === minMaxOrder.value.max;

const isLastRow = (order: number) => order === minMaxOrder.value.min;

const getSets = async () => {
  sets.value = await api('/get-research-sets');
};

const getResearches = async () => {
  researches.value = await api('/get-research-list');
};

const addResearchInSet = async () => {
  if (researchesInSet.value.find((i) => i.research.id === currentResearch.value)) {
    root.$emit('msg', 'error', 'Такое исследование уже есть');
  } else {
    await store.dispatch(actions.INC_LOADING);
    const { ok, message } = await api('/add-research-in-set', {
      set: currentSet.value.id,
      research: currentResearch.value,
      minOrder: minMaxOrder.value.min,
    });
    await store.dispatch(actions.DEC_LOADING);
    if (ok) {
      root.$emit('msg', 'ok', 'Исследование добавлено');
      await getResearchesInSet();
      currentResearch.value = null;
    } else {
      root.$emit('msg', 'error', message);
    }
  }
};

const updateSet = async () => {
  if (setIsSelected.value) {
    await store.dispatch(actions.INC_LOADING);
    const { ok, message } = await api('/update-research-set', {
      id: currentSet.value.id,
      label: titleSet.value,
    });
    await store.dispatch(actions.DEC_LOADING);
    if (ok) {
      root.$emit('msg', 'ok', 'Набор изменён');
      await getSets();
    } else {
      root.$emit('msg', 'error', message);
    }
  } else {
    await store.dispatch(actions.INC_LOADING);
    const { ok, message } = await api('/update-research-set', {
      id: -1,
      label: titleSet.value,
    });
    await store.dispatch(actions.DEC_LOADING);
    if (ok) {
      root.$emit('msg', 'ok', 'Набор добавлен');
      await getSets();
      titleSet.value = '';
    } else {
      root.$emit('msg', 'error', message);
    }
  }
};

const updateSetHiding = async () => {
  if (!setIsHidden.value) {
    try {
      await vm.$dialog.confirm('Подтвердите скрытие набора');
    } catch (_) {
      return;
    }
  }
  await store.dispatch(actions.INC_LOADING);
  const { ok, message } = await api('/update-set-hiding', currentSet.value.id);
  await store.dispatch(actions.DEC_LOADING);
  if (ok) {
    if (!setIsHidden.value) {
      root.$emit('msg', 'ok', 'Набор скрыт');
    } else {
      root.$emit('msg', 'ok', 'Скрытие отменено');
    }
    await checkSetHidden();
  } else {
    root.$emit('msg', 'error', message);
  }
};

onMounted(() => {
  getSets();
  getResearches();
});
</script>

<style scoped>
::v-deep .form-control {
  border: 0;
}
::v-deep .card {
  margin: 0;
}
.title-set {
  margin: 10px 0;
}
.table {
  margin-bottom: 0;
  table-layout: fixed;
}
.scroll {
  min-height: 112px;
  max-height: calc(100vh - 400px);
  overflow-y: auto;
}
.border {
  border: 1px solid #ddd;
  border-radius: 0;
}
.table > thead > tr > th {
  border-bottom: 0;
}
.research {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  height: 37px;
}
.padding-left {
  padding-left: 6px;
}
.button {
  width: 100%;
  display: flex;
  flex-wrap: nowrap;
  flex-direction: row;
  justify-content: stretch;
}
  .btn {
    align-self: stretch;
    flex: 1;
    padding: 7px 0;
  }
</style>
