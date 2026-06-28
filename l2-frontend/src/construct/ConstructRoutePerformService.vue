<template>
  <div>
    <table
      class="table table-bordered table-condensed table-sm-pd"
      style="table-layout: fixed; font-size: 12px; margin-bottom: 0"
    >
      <colgroup>
        <col width="500">
        <col>
        <col width="37">
      </colgroup>
      <thead>
        <tr>
          <th>Услуга</th>
          <th>Исполнитель</th>
          <th />
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(val, index) in tbData"
          :key="index"
        >
          <td class="cl-td">
            <Treeselect
              v-model="val.researchId"
              class="treeselect-noborder treeselect-32px"
              :multiple="false"
              :options="researches"
              :disable-branch-nodes="true"
              :append-to-body="true"
              placeholder="Не выбрана"
              @input="checkUniqueResearch"
            />
          </td>
          <td class="cl-td">
            <Treeselect
              v-model="val.planExternalPerformerId"
              class="treeselect-noborder treeselect-32px"
              :multiple="false"
              :options="performerHospitals"
              :disable-branch-nodes="true"
              :append-to-body="true"
              placeholder="Не выбран"
            />
          </td>
          <td class="text-center cl-td">
            <button
              v-tippy="{ placement: 'bottom' }"
              class="btn btn-blue-nb"
              title="Удалить строку"
              @click="deleteRow(index)"
            >
              <i class="fa fa-times" />
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    <div
      class="flex add-row-div"
    >
      <button
        v-tippy="{ placement: 'bottom' }"
        class="btn btn-blue-nb add-row margin-button"
        title="Добавить строку"
        type="button"
        @click="addNewRow"
      >
        Добавить
      </button>
      <button
        class="btn btn-blue-nb add-row margin-button"
        :disabled="disabledButtons"
        @click="saveResearchPerformer(tbData)"
      >
        Сохранить
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import Treeselect from '@riophae/vue-treeselect';
import { getCurrentInstance, onMounted, ref } from 'vue';

import api from '@/api';
import * as actions from '@/store/action-types';
import { useStore } from '@/store';

const makeDefaultRow = (researchId = null) => ({ researchId });

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const tbData = ref<any[]>([makeDefaultRow()]);
const researches = ref<any[]>([]);
const performerHospitals = ref<any[]>([]);
const disabledButtons = ref(false);

const addNewRow = () => {
  tbData.value.push(makeDefaultRow(null));
};

const deleteRow = (index: number) => {
  tbData.value.splice(index, 1);
};

const getResearchList = async () => {
  const result = await api('/get-research-list');
  researches.value = result.data;
};

const getPerformerHospitals = async () => {
  const result = await api('hospitals/external-performer');
  performerHospitals.value = result.data;
};

const checkUniqueResearch = () => {
  const currentResearch = tbData.value.map((v) => v.researchId);
  const setCurrentResearch = new Set(currentResearch);
  disabledButtons.value = currentResearch.length !== setCurrentResearch.size;
};

const loadData = async () => {
  await store.dispatch(actions.INC_LOADING);
  tbData.value = await api('researches/get-research-performer');
  await store.dispatch(actions.DEC_LOADING);
};

const saveResearchPerformer = async (rows: any[]) => {
  await store.dispatch(actions.INC_LOADING);
  const { ok, message } = await api('researches/research-performer-save', {
    tb_data: rows,
  });
  if (ok) {
    root.$emit('msg', 'ok', message);
  } else {
    root.$emit('msg', 'error', message);
  }
  await loadData();
  await store.dispatch(actions.DEC_LOADING);
};

onMounted(() => {
  getResearchList();
  getPerformerHospitals();
  loadData();
});
</script>

<style scoped>

.add-row-div {
  justify-content: flex-end;
  padding-top: 10px;
}

.flex {
  display: flex;
}
.margin-button {
  margin-left: 10px;
}
</style>
