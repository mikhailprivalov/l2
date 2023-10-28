<template>
  <div class="main">
    <div class="four-col">
      <div class="filters">
        <label>Месяц</label>
        <Treeselect
          v-model="selectedMonth"
          :options="months"
          placeholder="Выберите направление"
          class="treeselect-wide"
        />
      </div>
      <div class="filters">
        <label>Подразделение</label>
        <Treeselect
          v-model="selectedDepartment"
          :options="departments"
          placeholder="Выберите направление"
          class="treeselect-wide"
        />
      </div>
      <div class="filters">
        <label>Название</label>
      </div>
    </div>
    <div>
      <label>Поиск сотрудника</label>
      <input
        v-model="search"
        class="form-control"
      >
    </div>
    <div class="white-background">
      <VeTable
        :columns="columns"
        :table-data="filteredEmployees"
      />
      <div
        v-show="filteredEmployees.length === 0"
        class="empty-list"
      >
        Нет записей
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed, defineProps, onMounted, ref, useCssModule,
} from 'vue';
import { VeTable } from 'vue-easytable';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import 'vue-easytable/libs/theme-default/index.css';
import api from '@/api';
import { useStore } from '@/store';

const selectedMonth = ref(1);
const months = ref([
  { id: 1, label: 'Октябрь 2023' },
  { id: 2, label: 'Сентябрь 2023' },
  { id: 3, label: 'Август 2023' },
]);

const selectedDepartment = ref(3);
const departments = ref([
  { id: 1, label: 'Отдел ИТ' },
  { id: 2, label: 'Планово-экономический отдел' },
  { id: 3, label: 'Гастроэнтерология' },
]);

const search = ref('');

const columns = ref([
  {
    field: 'fio', key: 'fio', title: 'ФИО', align: 'center', width: 80,
  },
  {
    field: 'position', key: 'position', title: 'Должность', align: 'center', width: 80,
  },
  {
    field: 'bidType', key: 'bidType', title: 'Ставка', align: 'center', width: 30,
  },
  {
    field: 'normMonth', key: 'normMonth', title: 'Норма', align: 'center', width: 30,
  },
  {
    field: 'shiftDuration', key: 'shiftDuration', title: 'Смена', align: 'center', width: 30,
  },
  {
    field: '01.10.2023',
    key: '01.10.2023',
    title: '1',
    align: 'center',
    width: 5,
    renderBodyCell: ({ row }, h) => h('p', { title: 'Привет мир!' }, '3'),
  },
  {
    field: '02.10.2023', key: '02.10.2023', title: '2', align: 'center', width: 5,
  },
  {
    field: '03.10.2023', key: '03.10.2023', title: '3', align: 'center', width: 5,
  },
  {
    field: '04.10.2023', key: '04.10.2023', title: '4', align: 'center', width: 5,
  },
  {
    field: '05.10.2023', key: '05.10.2023', title: '5', align: 'center', width: 5,
  },
  {
    field: '06.10.2023', key: '06.10.2023', title: '6', align: 'center', width: 5,
  },
  {
    field: '07.10.2023', key: '07.10.2023', title: '7', align: 'center', width: 5,
  },
  {
    field: '08.10.2023', key: '08.10.2023', title: '8', align: 'center', width: 5,
  },
  {
    field: '09.10.2023', key: '09.10.2023', title: '9', align: 'center', width: 5,
  },
  {
    field: '10.10.2023', key: '10.10.2023', title: '10', align: 'center', width: 5,
  },
  {
    field: '11.10.2023', key: '11.10.2023', title: '11', align: 'center', width: 5,
  },
  {
    field: '12.10.2023', key: '12.10.2023', title: '12', align: 'center', width: 5,
  },
  {
    field: '13.10.2023', key: '13.10.2023', title: '13', align: 'center', width: 5,
  },
  {
    field: '14.10.2023', key: '14.10.2023', title: '14', align: 'center', width: 5,
  },
  {
    field: '15.10.2023', key: '15.10.2023', title: '15', align: 'center', width: 5,
  },
  {
    field: '16.10.2023', key: '16.10.2023', title: '16', align: 'center', width: 5,
  },
  {
    field: '17.10.2023', key: '17.10.2023', title: '17', align: 'center', width: 5,
  },
  {
    field: '18.10.2023', key: '18.10.2023', title: '18', align: 'center', width: 5,
  },
  {
    field: '19.10.2023', key: '19.10.2023', title: '19', align: 'center', width: 5,
  },
  {
    field: '20.10.2023', key: '20.10.2023', title: '20', align: 'center', width: 5,
  },
  {
    field: '21.10.2023', key: '21.10.2023', title: '21', align: 'center', width: 5,
  },
  {
    field: '22.10.2023', key: '22.10.2023', title: '22', align: 'center', width: 5,
  },
  {
    field: '23.10.2023', key: '23.10.2023', title: '23', align: 'center', width: 5,
  },
  {
    field: '24.10.2023', key: '24.10.2023', title: '24', align: 'center', width: 5,
  },
  {
    field: '25.10.2023', key: '25.10.2023', title: '25', align: 'center', width: 5,
  },
  {
    field: '26.10.2023', key: '26.10.2023', title: '26', align: 'center', width: 5,
  },
  {
    field: '27.10.2023', key: '27.10.2023', title: '27', align: 'center', width: 5,
  },
  {
    field: '28.10.2023', key: '28.10.2023', title: '28', align: 'center', width: 5,
  },
  {
    field: '29.10.2023', key: '29.10.2023', title: '29', align: 'center', width: 5,
  },
  {
    field: '30.10.2023', key: '30.10.2023', title: '30', align: 'center', width: 5,
  },
  {
    field: '31.10.2023', key: '31.10.2023', title: '31', align: 'center', width: 5,
  },
]);
const employees = ref([
  {
    fio: 'Антонюк Г.Р',
    position: 'Техник',
    bidType: 'осн.',
    normMonth: '178',
    shiftDuration: '8',
    '01.10.2023': '8',
    '02.10.2023': '8',
  },
]);
const filteredEmployees = computed(() => employees.value.filter(employee => {
  const employeesFio = employee.fio?.toLowerCase();
  const searchTerm = search.value.toLowerCase();
  return employeesFio.includes(searchTerm);
}));
</script>

<style scoped lang="scss">
.empty-list {
  width: 85px;
  margin: 20px auto;
}
.main {
  width: 95%;
  margin: 0 auto;
}
.four-col {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-bottom: 5px;
}
.white-background {
  background-color: #FFF;
}
.filters {
  margin: 0 10px;
}
</style>
