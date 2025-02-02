<template>
  <div>
    <div
      class="card-no-hover card card-1"
    >
      <div class="scroll">
        <table class="table">
          <colgroup>
            <col>
            <col style="width: 230px">
            <col style="width: 300px">
            <col style="width: 120px">
          </colgroup>
          <thead>
            <tr>
              <td class="text-center">
                <strong>Название</strong>
              </td>
              <td class="text-center">
                <strong>Код</strong>
              </td>
              <td class="text-center">
                <strong>Цвет</strong>
              </td>
              <td />
            </tr>
          </thead>
          <tr
            v-if="tubes.length === 0"
            class="text-center"
          >
            <td
              colspan="4"
            >
              Нет данных
            </td>
          </tr>
          <tr
            v-for="tube in tubes"
            :key="tube.id"
          >
            <td>
              <input
                v-model.trim="tube.label"
                class="form-control nbr"
                maxlength="255"
              >
            </td>
            <td>
              <input
                v-model.trim="tube.shortLabel"
                class="form-control nbr"
                maxlength="16"
              >
            </td>
            <td>
              <InputColorString v-model.trim="tube.color" />
            </td>
            <td>
              <div class="button">
                <button
                  v-tippy
                  class="btn last btn-blue-nb nbr"
                  title="Сохранить"
                  :disabled="!checkBerofe(tube)"
                  @click="update(tube)"
                >
                  Сохранить
                </button>
              </div>
            </td>
          </tr>
        </table>
      </div>
    </div>
    <h4>
      Добавить пробирку
    </h4>
    <div>
      <table class="table">
        <colgroup>
          <col>
          <col style="width: 230px">
          <col style="width: 300px">
          <col style="width: 120px">
        </colgroup>
        <tr>
          <td>
            <input
              v-model.trim="newTube.label"
              class="form-control nbr"
              maxlength="255"
            >
          </td>
          <td>
            <input
              v-model.trim="newTube.shortLabel"
              class="form-control nbr"
              maxlength="16"
            >
          </td>
          <td>
            <InputColorString v-model.trim="newTube.color" />
          </td>
          <td>
            <div class="button">
              <button
                v-tippy
                class="btn last btn-blue-nb nbr"
                title="Добавить"
                :disabled="!checkBerofe()"
                @click="create"
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
import {
  getCurrentInstance, onMounted, ref,
} from 'vue';

import * as actions from '@/store/action-types';
import { useStore } from '@/store';
import api from '@/api';
import InputColorString from '@/construct/ConstructTubes/InputColorString.vue';

interface tubeData {
  id: number,
  label: string,
  shortLabel: string,
  color: string,
}

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const tubes = ref<tubeData[]>([]);

const getTubes = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('construct/tubes/get-tubes');
  tubes.value = result;
  await store.dispatch(actions.DEC_LOADING);
};

onMounted(async () => {
  await getTubes();
});

const newTube = ref<tubeData>({
  id: null,
  label: '',
  shortLabel: '',
  color: '',
});
const checkBerofe = (tube: tubeData = null) :boolean => {
  if (!tube) {
    return newTube.value.label && newTube.value.label.length > 0 && newTube.value.color && newTube.value.color.length > 0
       && newTube.value.color.length < 8;
  }
  return tube.label && tube.label.length > 0 && tube.color && tube.color.length > 0
       && tube.color.length < 8;
};
const update = async (tube: tubeData) => {
  const tubeValid = checkBerofe(tube);
  if (!tubeValid) {
    root.$emit('msg', 'error', 'Название или цвет не заполнены');
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  const { ok, message } = await api('construct/tubes/update-tube', {
    ...tube,
  });
  if (ok) {
    await getTubes();
    root.$emit('msg', 'ok', 'Обновлено');
  } else {
    root.$emit('msg', 'error', message);
  }
  await store.dispatch(actions.DEC_LOADING);
};

const create = async () => {
  const newTubeValid = checkBerofe();
  if (!newTubeValid) {
    root.$emit('msg', 'error', 'Название или цвет не заполнены');
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  const { ok, message } = await api('construct/tubes/create-tube', {
    ...newTube.value,
  });
  if (ok) {
    newTube.value = {
      id: null,
      label: '',
      shortLabel: '',
      color: '',
    };
    await getTubes();
    root.$emit('msg', 'ok', 'Обновлено');
  } else {
    root.$emit('msg', 'error', message);
  }
  await store.dispatch(actions.DEC_LOADING);
};

</script>

<style scoped>
::v-deep .card {
  margin: 0;
}
.table {
  margin-bottom: 0;
  table-layout: fixed;
}
.scroll {
  min-height: 104px;
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}
.table > thead > tr > th {
  border-bottom: 0;
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
  padding: 6px 0;
}
</style>
