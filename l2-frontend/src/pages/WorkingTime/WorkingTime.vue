<template>
  <div class="main">
    <div class="flex margin-bottom">
      <div class="filters department-width">
        <label>Подразделение</label>
        <Treeselect
          v-model="selectedDepartment"
          :options="departments"
          placeholder="Выберите подразделение"
          :clearable="false"
        />
      </div>
      <div class="filters month-width">
        <label for="month">Месяц</label>
        <Treeselect
          v-model="selectedMonth"
          :options="months"
          placeholder="Выберите месяц"
          :clearable="false"
        />
      </div>
      <div class="filters year-width">
        <label>Год</label>
        <Treeselect
          v-model="selectedYear"
          :options="years"
          placeholder="Выберите год"
          :clearable="false"
        />
      </div>
    </div>
    <WorkingTimeTable
      :year="selectedYear"
      :month="selectedMonth"
      :department="selectedDepartment"
    />
  </div>
</template>

<script setup lang="ts">
import {
  onMounted, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import 'vue-easytable/libs/theme-default/index.css';

import api from '@/api';
import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import WorkingTimeTable from '@/pages/WorkingTime/WorkingTimeTable.vue';

const store = useStore();

const currentDate = ref(new Date());

const selectedMonth = ref(currentDate.value.getMonth());
const months = ref([
  { id: 0, label: 'Январь' },
  { id: 1, label: 'Февраль' },
  { id: 2, label: 'Март' },
  { id: 3, label: 'Апрель' },
  { id: 4, label: 'Май' },
  { id: 5, label: 'Июнь' },
  { id: 6, label: 'Июль' },
  { id: 7, label: 'Август' },
  { id: 8, label: 'Сентябрь' },
  { id: 9, label: 'Октябрь' },
  { id: 10, label: 'Ноябрь' },
  { id: 11, label: 'Декабрь' },
]);

const selectedYear = ref(currentDate.value.getFullYear());
const years = ref([]);

const getYears = (yearStart = 2023) => {
  let start = yearStart;
  currentDate.value.getFullYear();
  while (start <= currentDate.value.getFullYear()) {
    years.value.push({ id: start, label: String(start) });
    start++;
  }
};

const selectedDepartment = ref(null);
const departments = ref([]);
const getDepartments = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('/working-time/get-departments');
  await store.dispatch(actions.DEC_LOADING);
  departments.value = result;
};

onMounted(() => {
  getDepartments();
  getYears();
});

</script>

<style scoped lang="scss">
.main {
  width: 100%;
  margin: 0 auto;
}
.flex {
  display: flex;
}
.four-col {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-bottom: 5px;
}
.filters {
  margin: 0 10px;
}
.month-width {
  width: 130px;
}
.year-width {
  width: 100px;
}
.department-width {
  width: 490px;
}
.margin-bottom {
  margin-bottom: 5px;
}
.create-document {
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
