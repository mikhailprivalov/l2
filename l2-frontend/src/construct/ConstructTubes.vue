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
          <tr>
            <td>
              <input class="form-control nbr">
            </td>
            <td>
              <input class="form-control nbr">
            </td>
            <td>
              <input class="form-control nbr">
            </td>
            <td>
              <div class="button">
                <button
                  v-tippy
                  class="btn last btn-blue-nb nbr"
                  title="Сохранить"
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
              v-model="newTube.title"
              class="form-control nbr"
            >
          </td>
          <td>
            <input
              v-model="newTube.code"
              class="form-control nbr"
            >
          </td>
          <td>
            <input
              v-model="newTube.color"
              class="form-control nbr"
            >
          </td>
          <td>
            <div class="button">
              <button
                v-tippy
                class="btn last btn-blue-nb nbr"
                title="Добавить"
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
import {onMounted, ref} from 'vue';

import * as actions from '@/store/action-types';
import { useStore } from '@/store';
import api from "@/api";
import {afterWrite} from "@popperjs/core";

interface tube {
  id: number,
  label: string,
  shortLabel: string,
  color: string,
}

const store = useStore();

const tubes = ref<tube[]>([]);

const getTubes = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('construct/tubes/get-tubes');
  tubes.value = result;
};

onMounted(async () => {
  await getTubes();
});

const newTube = ref<tube>({
  id: null,
  label: '',
  shortLabel: '',
  color: '',
});
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
