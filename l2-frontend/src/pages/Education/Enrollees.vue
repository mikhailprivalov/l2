<template>
  <div class="main">
    <h4 class="text-center">
      Абитуриенты
    </h4>
    <div class="filter-div">
      <div class="margin-div">
        <Treeselect
          v-model="selectedDestinations"
          :multiple="true"
          :options="destinations"
          :disable-branch-nodes="true"
          placeholder="Направление"
        />
      </div>
      <div class="margin-div">
        <Treeselect
          v-model="selectedCompetitions"
          :multiple="true"
          :options="competitions"
          :disable-branch-nodes="true"
          placeholder="Конкурс"
        />
      </div>
      <div class="margin-div">
        <Treeselect
          v-model="selectedCustomers"
          :multiple="true"
          :options="customers"
          :disable-branch-nodes="true"
          placeholder="Заказчик"
        />
      </div>
      <div class="margin-div">
        <Treeselect
          v-model="selectedEnrollmentStatuses"
          :multiple="true"
          :options="enrollmentStatuses"
          :disable-branch-nodes="true"
          placeholder="Статус зачисления"
        />
      </div>
      <div class="margin-div">
        <Treeselect
          v-model="selectedDeductionStatuses"
          :multiple="true"
          :options="deductionStatuses"
          :disable-branch-nodes="true"
        />
      </div>
      <div class="margin-div">
        <Treeselect
          v-model="selectedCommands"
          :multiple="true"
          :options="commands"
          :disable-branch-nodes="true"
        />
      </div>
      <div class="margin-div flex-div">
        <input
          v-model="consent"
          type="checkbox"
        >
        <label>Согласие на зачисление</label>
        <input
          v-model="activeApplicationOnly"
          type="checkbox"
        >
        <label>Только активные заявления</label>
      </div>
      <div class="margin-div flex-div">
        <input
          v-model="contract"
          type="checkbox"
        >
        <label>Есть договор</label>
        <input
          v-model="payment"
          type="checkbox"
        >
        <label>Есть оплата</label>
      </div>
    </div>
    <div>
      <input
        v-model="search"
        placeholder="Поиск"
        class="form-control"
      >
    </div>
    <div>
      <VeTable
        :columns="columns"
        :table-data="enrollees"
      />
      <div
        v-show="enrollees.length === 0"
        class="empty-list"
      >
        Нет записей
      </div>
      <div class="flex-space-between">
        <VePagination
          :total="enrollees.length"
          :page-index="page"
          :page-size="pageSize"
          :page-size-option="pageSizeOption"
          @on-page-number-change="pageNumberChange"
          @on-page-size-change="pageSizeChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  onMounted, ref,
} from 'vue';
import {
  VeLocale,
  VePagination,
  VeTable,
} from 'vue-easytable';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import 'vue-easytable/libs/theme-default/index.css';
// import * as actions from '@/store/action-types';
// import api from '@/api';
import { useStore } from '@/store';
import ruRu from '@/locales/ve';

VeLocale.use(ruRu);

const store = useStore();
const pageSize = ref(30);
const page = ref(1);
const pageSizeOption = ref([30, 50, 100, 300]);
const pageNumberChange = (number: number) => {
  page.value = number;
};
const pageSizeChange = (size: number) => {
  pageSize.value = size;
};

const selectedDestinations = ref([]);
const destinations = ref([
  { id: 1, label: 'Направление 1' },
  { id: 2, label: 'Направление 2' },
  { id: 3, label: 'Направление 3' },
]);
const selectedCompetitions = ref([]);
const competitions = ref([
  { id: 1, label: 'Конкурс 1' },
  { id: 2, label: 'Конкурс 2' },
  { id: 3, label: 'Конкурс 3' },
]);
const selectedCustomers = ref([]);
const customers = ref([
  { id: 1, label: 'Заказчик 1' },
  { id: 2, label: 'Заказчик 2' },
  { id: 3, label: 'Заказчик 3' },
]);
const selectedEnrollmentStatuses = ref([]);
const enrollmentStatuses = ref([
  { id: 1, label: 'Статус зачисления 1' },
  { id: 2, label: 'Статус зачисления 2' },
  { id: 3, label: 'Статус зачисления 3' },
]);
const selectedDeductionStatuses = ref([]);
const deductionStatuses = ref([
  { id: 1, label: 'Статус отчисления 1' },
  { id: 2, label: 'Статус отчисления 2' },
  { id: 3, label: 'Статус отчисления 3' },
]);
const selectedCommands = ref([]);
const commands = ref([
  { id: 1, label: 'Приказ 1' },
  { id: 2, label: 'Приказ 2' },
  { id: 3, label: 'Приказ 3' },
]);

const consent = ref(Boolean);

const search = ref('');

const enrollees = ref([]);

const columns = ref([
  { field: 'card', key: 'card', title: 'Дело' },
  { field: 'fio', key: 'fio', title: 'ФИО' },
  { field: 'application', key: 'application', title: 'Заявление' },
  { field: 'сhemistry', key: 'сhemistry', title: 'Хим' },
  { field: 'biology', key: 'biology', title: 'Био' },
  { field: 'mathematics', key: 'mathematics', title: 'Мат' },
  { field: 'russian_language', key: 'russian_language', title: 'Рус.' },
  { field: 'ia', key: 'ia', title: 'ИД' },
  { field: 'ia+', key: 'ia+', title: 'ИД+' },
  { field: 'amount', key: 'amount', title: 'Сумм' },
  { field: 'is_original', key: 'is_original', title: 'Оригинал' },
  { field: 'status', key: 'status', title: 'Статус' },
  { field: 'create_date', key: 'create_date', title: 'Создано' },
]);
// const getColumns = async () => {
//   await store.dispatch(actions.INC_LOADING);
//   const data = await api('education/get-columns');
//   await store.dispatch(actions.DEC_LOADING);
//   columns.value = data.result;
//   console.log(columns);
// };

// onMounted(getColumns);

</script>

<style scoped>
.main {
  width: 90%;
  background-color: #ffffff;
  margin: 10px auto;
}
.empty-list {
  width: 85px;
  margin: 20px auto;
}
.filter-div {
  display: grid;
  grid-template-columns: auto auto auto;
  margin-bottom: 10px;
}
.margin-div {
  margin: 5px 10px;
}
.flex-div {
  display: flex;
}
</style>
