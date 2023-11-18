<template>
  <div class="main">
    <div class="flex margin-bottom">
      <div class="filters department-width">
        <label>Подразделение</label>
        <Treeselect
          v-model="selectedDepartment"
          :options="departments"
          placeholder="Выберите подразделение"
        />
      </div>
      <div class="filters month-width">
        <label>Месяц</label>
        <Treeselect
          v-model="selectedMonth"
          :options="months"
          placeholder="Выберите месяц"
        />
      </div>
      <div class="filters year-width">
        <label>Год</label>
        <Treeselect
          v-model="selectedYear"
          :options="years"
          placeholder="Выберите год"
        />
      </div>
    </div>
    <div v-if="filtersIsFilled">
      <label class="filters">Поиск сотрудника</label>
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
        :columns="columns"
        :table-data="filteredEmployees"
        :row-style-option="rowStyleOption"
        :cell-style-option="cellStyleOption"
        :border-y="true"
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
import { VeTable } from 'vue-easytable';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import 'vue-easytable/libs/theme-default/index.css';

import api from '@/api';
import { useStore } from '@/store';
import DateCell from '@/pages/WorkingTime/DateCell.vue';
import * as actions from '@/store/action-types';

const root = getCurrentInstance().proxy.$root;

const store = useStore();

const selectedMonth = ref(null);
const months = ref([
  { id: 1, label: 'Январь' },
  { id: 2, label: 'Февраль' },
  { id: 3, label: 'Март' },
  { id: 4, label: 'Апрель' },
  { id: 5, label: 'Май' },
  { id: 6, label: 'Июнь' },
  { id: 7, label: 'Июль' },
  { id: 8, label: 'Август' },
  { id: 9, label: 'Сентябрь' },
  { id: 10, label: 'Октябрь' },
  { id: 11, label: 'Ноябрь' },
  { id: 12, label: 'Декабрь' },
]);

const selectedYear = ref(2023);
const years = ref([
  { id: 2023, label: '2023' },
  { id: 2024, label: '2024' },
  { id: 2025, label: '2025' },
]);

const selectedDepartment = ref(null);
const departments = ref([
  { id: 1, label: 'Отдел ИТ' },
  { id: 2, label: 'Планово-экономический отдел' },
  { id: 3, label: 'Гастроэнтерология' },
]);

const filtersIsFilled = computed(() => !!(selectedDepartment.value && selectedMonth.value && selectedYear.value));

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
    normDay: '8',
    '01.10.2023': { startWorkTime: '08:00', endWorkTime: '16:30' },
    '02.10.2023': '8',
  },
  {
    fio: 'Касьяненко С.Н.',
    position: 'Начальник',
    bidType: 'осн.',
    normMonth: '178',
    normDay: '8',
    '01.10.2023': { startWorkTime: '08:00', endWorkTime: '16:30' },
    '02.10.2023': '8',
  },
  {
    fio: 'Димитров С.Н.',
    position: 'Техник',
    bidType: 'осн.',
    normMonth: '178',
    normDay: '8',
    '01.10.2023': { startWorkTime: '08:00', endWorkTime: '16:30' },
    '02.10.2023': '8',
  },
]);

const changeWorkTime = (workTime: object) => {
  const {
    start, end, rowIndex, columnKey, clear,
  } = workTime;
  if (clear) {
    employees.value[rowIndex][columnKey] = null;
    root.$emit('msg', 'ok', 'Очищено');
  } else {
    employees.value[rowIndex][columnKey] = { startWorkTime: start, endWorkTime: end };
    root.$emit('msg', 'ok', 'Обновлено');
  }
};

const columns = ref([]);

const getMonthDays = (year: number, month: number) => {
  const days = [];
  const currentMonth = month - 1;
  const date = new Date(year, currentMonth);
  while (date.getMonth() === currentMonth) {
    days.push(new Date(date));
    date.setDate(date.getDate() + 1);
  }
  return days;
};

const getColumns = () => {
  if (filtersIsFilled.value) {
    const columnTemplate = [
      {
        field: 'fio', key: 'fio', title: 'ФИО', align: 'center', width: 250, fixed: 'left',
      },
      {
        field: 'position', key: 'position', title: 'Должность', align: 'center', width: 100, fixed: 'left',
      },
      {
        field: 'bidType', key: 'bidType', title: 'Ставка', align: 'center', width: 30,
      },
      {
        field: 'normMonth', key: 'normMonth', title: 'Норма', align: 'center', width: 30,
      },
      {
        field: 'normDay', key: 'normDay', title: 'Смена', align: 'center', width: 30,
      },
    ];
    const daysMonth = getMonthDays(selectedYear.value, selectedMonth.value);
    const data = daysMonth.map((col) => {
      const date = col.toLocaleDateString();
      const dateTitle = col.toLocaleDateString('ru-RU', { weekday: 'short', day: '2-digit' });
      const weekend = [6, 0].includes(col.getDay());
      const isFirstDay = col.getDate() === 1;
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
            props: {
              workTime: row[column.field] ? row[column.field] : '', rowIndex, columnKey: column.key, isFirstDay,
            },
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
    return '';
  },
};

const rowStyleOption = {
  stripe: true,
};

watch([selectedMonth, selectedYear, selectedDepartment], () => {
  getColumns();
});

onMounted(() => {
  getDepartments();
  getColumns();
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
.flex {
  display: flex;
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
</style>

<style lang="scss">
.table-body-cell-weekend {
  background: #ade0a875 !important;
}
.table-header-cell-weekend {
  background: #ade0a875 !important;
}

</style>
