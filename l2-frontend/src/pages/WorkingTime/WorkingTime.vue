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
        <label for="month">Месяц</label>
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
    <div v-if="filtersIsFilled && workTimeDocument">
      <label
        for="search"
        class="filters"
      >Поиск сотрудника</label>
      <input
        id="search"
        v-model.trim="search"
        class="form-control"
      >
    </div>
    <div
      v-if="filtersIsFilled && workTimeDocument"
      class="white-background"
    >
      <VeTable
        v-show="filteredEmployees.length"
        :columns="columns"
        :table-data="filteredEmployees"
        :row-style-option="rowStyleOption"
        :cell-style-option="cellStyleOption"
        :border-y="true"
        :scroll-width="0"
      />
      <div
        v-show="!filteredEmployees.length"
        class="empty-list"
      >
        Нет записей
      </div>
    </div>
    <div
      v-if="!workTimeDocument"
      class="create-document"
    >
      <button
        class="btn btn-blue-nb"
        @click="createWorkTimeDocument"
      >
        Создать график
      </button>
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
const years = ref([]);

const currentDate = ref(new Date());
const getYears = (yearStart = 2023) => {
  let start = yearStart;
  selectedYear.value = currentDate.value.getFullYear();
  while (start <= selectedYear.value) {
    years.value.push({ id: start, label: String(start) });
    start++;
  }
};
const setCurrentMonth = () => {
  selectedMonth.value = currentDate.value.getMonth() + 1;
};

const selectedDepartment = ref(null);
const departments = ref([]);
const getDepartments = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('/working-time/get-departments');
  await store.dispatch(actions.DEC_LOADING);
  departments.value = result;
  selectedDepartment.value = 1;
};

const filtersIsFilled = computed(() => !!(selectedDepartment.value && selectedMonth.value && selectedYear.value));

const search = ref('');

const workTimeDocument = ref(false);

const getWorkTimeDocument = async () => {
  if (filtersIsFilled.value) {
    await store.dispatch(actions.INC_LOADING);
    const { ok, message } = await api('/working-time/get-document', {
      month: selectedMonth.value,
      year: selectedYear.value,
      department: selectedDepartment.value,
    });
    await store.dispatch(actions.DEC_LOADING);
    if (ok) {
      workTimeDocument.value = true;
    } else {
      workTimeDocument.value = false;
    }
  }
};

const createWorkTimeDocument = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { ok, message } = await api('/working-time/create-document', {
    month: selectedMonth.value,
    year: selectedYear.value,
    department: selectedDepartment.value,
  });
  await store.dispatch(actions.DEC_LOADING);
  if (ok) {
    root.$emit('msg', 'ok', 'График создан');
  } else {
    root.$emit('msg', 'error', 'Ошибка');
  }
};

const employeesWorkTime = ref([]);

const getEmployeesWorkTime = async () => {
  if (filtersIsFilled.value) {
    await store.dispatch(actions.INC_LOADING);
    const { result } = await api('/working-time/get-work-time', {
      month: selectedMonth.value,
      year: selectedYear.value,
      department: selectedDepartment.value,
    });
    await store.dispatch(actions.DEC_LOADING);
    console.log(result);
    employeesWorkTime.value = result;
  }
};

const changeWorkTime = (workTime: object) => {
  const {
    start, end, rowIndex, columnKey, clear,
  } = workTime;
  if (clear) {
    employeesWorkTime.value[rowIndex][columnKey] = null;
    root.$emit('msg', 'ok', 'Очищено');
  } else {
    employeesWorkTime.value[rowIndex][columnKey] = { startWorkTime: start, endWorkTime: end };
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
        field: 'fio', key: 'fio', title: 'ФИО', align: 'center', width: 190, fixed: 'left',
      },
      {
        field: 'position', key: 'position', title: 'Должность', align: 'center', width: 120, fixed: 'left',
      },
      {
        field: 'bidType', key: 'bidType', title: 'Ставка', align: 'center', width: 70,
      },
      {
        field: 'normMonth', key: 'normMonth', title: 'Норма', align: 'center', width: 70,
      },
      {
        field: 'normDay', key: 'normDay', title: 'Смена', align: 'center', width: 70,
      },
    ];
    const daysMonth = getMonthDays(selectedYear.value, selectedMonth.value);
    const data = daysMonth.map((col) => {
      const date = col.toLocaleDateString();
      const dateTitle = col.toLocaleDateString('ru-RU', { weekday: 'short', day: '2-digit' });
      const weekend = [6, 0].includes(col.getDay());
      const isFirstDay = col.getDate() === 1;
      const prevDay = new Date(col.getFullYear(), col.getMonth(), col.getDate() - 1).toLocaleDateString();
      return {
        key: date,
        field: date,
        title: dateTitle,
        align: 'center',
        width: 211,
        isWeekend: weekend,
        renderBodyCell: ({ row, column, rowIndex }, h) => h(
          DateCell,
          {
            props: {
              workTime: row[column.field] ? row[column.field] : '',
              rowIndex,
              columnKey: column.key,
              isFirstDay,
              prevWorkTime: employeesWorkTime.value[rowIndex][prevDay],
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

const filteredEmployees = computed(() => employeesWorkTime.value.filter(employee => {
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
  getWorkTimeDocument();
  getEmployeesWorkTime();
});

onMounted(() => {
  getDepartments();
  getYears();
  setCurrentMonth();
});

</script>

<style scoped lang="scss">
.empty-list {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 30px;
  width: 100%;
  color: #666;
  font-size: 16px;
  border: 1px solid #eee;
  border-top: 0;
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
.create-document {
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>

<style lang="scss">
.table-body-cell-weekend {
  background: #ade0a875 !important;;
}
.table-header-cell-weekend {
  background: #ade0a875 !important;
}
</style>
