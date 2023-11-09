<template>
  <div class="main">
    <div class="four-col">
      <div class="filters">
        <label>Подразделение</label>
        <Treeselect
          v-model="selectedDepartment"
          :options="departments"
          placeholder="Выберите подразделение"
          class="treeselect-wide"
        />
      </div>
      <div class="two-col filters">
        <div>
          <label>Месяц</label>
          <Treeselect
            v-model="selectedMonth"
            :options="months"
            placeholder="Выберите месяц"
            class="treeselect-wide"
          />
        </div>
        <div>
          <label>Год</label>
          <Treeselect
            v-model="selectedYear"
            :options="years"
            value-format="object"
            placeholder="Выберите год"
            class="treeselect-wide"
          />
        </div>
      </div>
    </div>
    <div v-if="filtersIsFilled">
      <label>Поиск сотрудника</label>
      <input
        v-model.trim="search"
        class="form-control"
      >
    </div>
    <div
      v-if="filtersIsFilled"
      class="white-background"
    >
      <VeTable
        id="loading-container"
        :columns="columns"
        :table-data="filteredEmployees"
        :row-style-option="rowStyleOption"
        :cell-style-option="cellStyleOption"
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
  computed, getCurrentInstance, onMounted, ref, watch,
} from 'vue';
import { VeTable, VeLoading } from 'vue-easytable';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import 'vue-easytable/libs/theme-default/index.css';

import api from '@/api';
import { useStore } from '@/store';
import DateCell from '@/pages/WorkingTime/DateCell.vue';
import * as actions from '@/store/action-types';

const root = getCurrentInstance().proxy.$root;

let loadingInstance: VeLoading | null = null;

const store = useStore();

const selectedMonth = ref(null);
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

const selectedYear = ref({ id: 1, label: '2023' });
const years = ref([
  { id: 1, label: '2023' },
  { id: 2, label: '2024' },
  { id: 3, label: '2025' },
]);

const selectedDepartment = ref(null);
const departments = ref([
  { id: 1, label: 'Отдел ИТ' },
  { id: 2, label: 'Планово-экономический отдел' },
  { id: 3, label: 'Гастроэнтерология' },
]);

const filtersIsFilled = computed(() => !!(selectedDepartment.value && (selectedMonth.value || selectedMonth.value === 0)
  && selectedYear.value));

const getDepartments = async () => {
  await store.dispatch(actions.INC_LOADING);
  // const { ok, message } = await api('/working-time/get-columns');
  await store.dispatch(actions.DEC_LOADING);
  selectedDepartment.value = 1;
};

const search = ref('');

const employees = ref([
  {
    fio: 'Антонюк Г.Р',
    position: 'Техник',
    bidType: 'осн.',
    normMonth: '178',
    shiftDuration: '8',
    '01.10.2023': { startWorkTime: '8:00', endWorkTime: '16:30' },
    '02.10.2023': '8',
  },
  {
    fio: 'Касьяненко С.Н.',
    position: 'Начальник',
    bidType: 'осн.',
    normMonth: '178',
    shiftDuration: '8',
    '01.10.2023': { startWorkTime: '8:00', endWorkTime: '16:30' },
    '02.10.2023': '8',
  },
  {
    fio: 'Димитров С.Н.',
    position: 'Техник',
    bidType: 'осн.',
    normMonth: '178',
    shiftDuration: '8',
    '01.10.2023': { startWorkTime: '8:00', endWorkTime: '16:30' },
    '02.10.2023': '8',
  },
]);

const changeWorkTime = (workTime: object) => {
  const {
    start, end, rowIndex, columnKey,
  } = workTime;
  employees.value[rowIndex][columnKey] = { startWorkTime: start, endWorkTime: end };
};

const columns = ref([]);

const getMonthDays = (year: number, month: number) => {
  const days = [];
  const date = new Date(year, month);
  while (date.getMonth() === month) {
    days.push(new Date(date));
    date.setDate(date.getDate() + 1);
  }
  return days;
};

const getColumns = () => {
  const columnTemplate = [{
    field: 'fio', key: 'fio', title: 'ФИО', align: 'center', width: 100,
  },
  {
    field: 'position', key: 'position', title: 'Должность', align: 'center', width: 100,
  },
  {
    field: 'bidType', key: 'bidType', title: 'Ставка', align: 'center', width: 30,
  },
  {
    field: 'normMonth', key: 'normMonth', title: 'Норма', align: 'center', width: 30,
  },
  {
    field: 'shiftDuration', key: 'shiftDuration', title: 'Смена', align: 'center', width: 30,
  }];
  if (filtersIsFilled.value) {
    const daysMonth = getMonthDays(Number(selectedYear.value.label), selectedMonth.value);
    const data = daysMonth.map((col) => {
      const date = col.toLocaleDateString();
      const dateTitle = col.toLocaleDateString('ru-RU', { weekday: 'short', day: '2-digit' });
      const weekend = [6, 0].includes(col.getDay());
      return {
        key: date,
        field: date,
        title: dateTitle,
        align: 'center',
        width: 385,
        isWeekend: weekend,
        renderBodyCell: ({ row, column, rowIndex }, h) => h(
          DateCell,
          {
            props: { workTime: row[column.field] ? row[column.field] : '', rowIndex, columnKey: column.key },
            on: { changeWorkTime },
          },
        ),
      };
    });
    columnTemplate.push(...data);
    columns.value = columnTemplate;
  }
};

const filteredEmployees = computed(() => employees.value.filter(employee => {
  const employeesFio = employee.fio?.toLowerCase();
  const searchTerm = search.value.toLowerCase();
  return employeesFio.includes(searchTerm);
}));

const cellStyleOption = {
  bodyCellClass: ({ column }) => {
    if (column.isWeekend) {
      return 'table-body-cell-weekend';
    }
    return '';
  },
  headerCellClass: ({ column }) => {
    if (column.isWeekend) {
      return 'table-header-cell-weekend';
    }
    return 'table-header-cell-weekday';
  },
};

const rowStyleOption = {
  stripe: true,
};

watch([selectedMonth, selectedYear], (newSelectedMonth, newSelectedYear) => {
  getColumns();
});

onMounted(() => {
  getDepartments();
  getColumns();
  loadingInstance = $ve
});

</script>

<style scoped lang="scss">
.empty-list {
  width: 85px;
  margin: 20px auto;
}
.main {
  width: 100%;
  margin: 0 auto;
}
.four-col {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-bottom: 5px;
}
.two-col {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-bottom: 5px;
}
.white-background {
  background-color: #FFF;
}
.filters {
  margin: 0 10px;
}
</style>

<style lang="scss">
.table-body-cell-weekend {
  background: #ade0a875 !important;
}
.table-header-cell-weekend {
  background: #ade0a875 !important;
  padding-right: 35px !important;
}
.table-header-cell-weekday {
  padding-right: 35px !important;
}

</style>
