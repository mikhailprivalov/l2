<template>
  <div class="block-margin">
    <div
      class="flex margins"
    >
      <button
        v-if="!documentCreated && filtersFull"
        class="btn btn-blue-nb"
        @click="createDocument"
      >
        Создать график
      </button>
    </div>
    <div
      v-if="documentCreated && filtersFull"
      class="flex"
    >
      <div class="search">
        <input
          v-model.trim="search"
          class="form-control"
          placeholder="Поиск работника"
        >
      </div>
      <button
        v-if="documentCreated && !documentBlocked"
        class="btn btn-blue-nb"
        @click="save"
      >
        Сохранить
      </button>
      <button
        class="btn btn-blue-nb"
        @click.prevent="printDocument()"
      >
        PDF
      </button>
    </div>
    <div
      class="white-background"
    >
      <VeTable
        max-height="calc(100vh - 240px)"
        :columns="columns"
        :table-data="filteredEmployees"
        :cell-style-option="cellStyleOption"
        :column-hidden-option="columnHiddenOption"
        :virtual-scroll-option="virtualScrollOption"
        row-key-field-name="employeePositionId"
        :cell-selection-option="cellSelectionOption"
        :row-style-option="rowStyleOption"
        :border-y="true"
        :scroll-width="0"
      />
      <div
        v-if="documentCreated && filtersFull"
        class="flex"
      >
        <div class="search" />
        <button
          v-if="!documentBlocked"
          class="btn btn-blue-nb"
          :disabled="documentBlocked"
          @click="save"
        >
          Сохранить
        </button>
        <button
          class="btn btn-blue-nb"
          @click.prevent="printDocument()"
        >
          PDF
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed, getCurrentInstance, onMounted, ref, watch,
} from 'vue';
import { VeTable } from 'vue-easytable';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import 'vue-easytable/libs/theme-default/index.css';
import moment from 'moment';
import axios from 'axios';

import api from '@/api';
import DateCell from '@/pages/WorkingTime/DateCell.vue';
import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import PositionCell from '@/pages/WorkingTime/PositionCell.vue';

const store = useStore();

const props = defineProps({
  year: {
    type: Number,
    required: true,
  },
  month: {
    type: Number,
    required: true,
  },
  department: {
    type: Number,
    required: false,
  },
});

const root = getCurrentInstance().proxy.$root;

const filtersFull = computed(() => !!(props.year && props.month && props.department));
const timeOptions = computed(() => (store.getters.modules.working_time_variants
  ? JSON.parse(store.getters.modules.working_time_variants) : []));

const search = ref('');

const documentCreated = ref(false);
const documentBlocked = ref(false);

const employeesWorkTime = ref([]);
const changedEmployeesWorkTime = ref({});

const updateChangedEmployeesWorkTime = (
  employeePositionId: number,
  date: string,
  startWorkTime: string = null,
  endWorkTime: string = null,
  typeId: number = null,
  fullData: object = null,
) => {
  if (!Object.hasOwn(changedEmployeesWorkTime.value, employeePositionId)) {
    changedEmployeesWorkTime.value[employeePositionId] = {};
  }
  if (fullData) {
    changedEmployeesWorkTime.value[employeePositionId][date] = fullData;
  } else {
    changedEmployeesWorkTime.value[employeePositionId][date] = {
      startWorkTime,
      endWorkTime,
      typeId,
    };
  }
};

const getEmployeesWorkTime = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('/working-time/get-work-time', {
    year: props.year,
    month: props.month + 1,
    departmentId: props.department,
  });
  await store.dispatch(actions.DEC_LOADING);
  const { data, documentIsBlocked, documentIsCreated } = result;
  employeesWorkTime.value = data;
  documentCreated.value = documentIsCreated;
  documentBlocked.value = documentIsBlocked;
  changedEmployeesWorkTime.value = {};
};

watch(employeesWorkTime, () => {
  for (const employee of employeesWorkTime.value) {
    let totalDiffTime = 0;
    const keys = Object.keys(employee);
    const lunchDuration = employee.lunchDuration * 60 * 1000;
    for (const key of keys) {
      if (moment(key, 'YYYY-MM-DD', true).isValid()) {
        const currentDay = employee[key];
        if (currentDay.startWorkTime && currentDay.endWorkTime && !currentDay.typeId) {
          const startTime = new Date(`${key} ${currentDay.startWorkTime}`);
          let endTime;
          if (currentDay.endWorkTime === '00:00') {
            endTime = new Date(startTime.getFullYear(), startTime.getMonth(), startTime.getDate() + 1, 0, 0);
          } else {
            endTime = new Date(`${key} ${currentDay.endWorkTime}`);
          }
          const dayDiffTime = endTime - startTime - lunchDuration;
          totalDiffTime += dayDiffTime;
        }
      }
    }
    const totalDiffSec = totalDiffTime / (1000 * 60);
    const totalHoursDecimal = totalDiffSec / 60;
    const totalHours = Math.trunc(totalHoursDecimal);
    const totalMin = totalDiffSec % 60;
    employee.totalHoursDecimal = totalHoursDecimal.toFixed(1);
    employee.totalHours = `${totalHours}ч ${totalMin}м`;
  }
}, { deep: true });

const createDocument = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { ok, message } = await api('/working-time/create-document', {
    year: props.year,
    month: props.month + 1,
    departmentId: props.department,
  });
  await store.dispatch(actions.DEC_LOADING);
  if (ok) {
    await getEmployeesWorkTime();
  } else {
    root.$emit('msg', 'error', message);
  }
};

watch(() => [props.year, props.month, props.department], () => {
  if (props.year && props.month && props.department) {
    getEmployeesWorkTime();
  }
}, { immediate: true });

const filteredEmployees = computed(() => employeesWorkTime.value.filter(employee => {
  const employeesFio = employee.fio?.toLowerCase();
  const searchTerm = search.value.toLowerCase();
  return employeesFio.includes(searchTerm);
}));

const changeWorkTime = async ({
  employeePositionId, date, startWorkTime, endWorkTime, typeId, nextDayEndWork,
}) => {
  const row = employeesWorkTime.value.find(employeePosition => employeePosition.employeePositionId === employeePositionId);
  row[date] = {
    startWorkTime,
    endWorkTime,
    typeId,
  };
  updateChangedEmployeesWorkTime(employeePositionId, date, startWorkTime, endWorkTime, typeId);
  if (nextDayEndWork) {
    const nextDay = nextDayEndWork;
    const nextDayString = moment(nextDay).format('YYYY-MM-DD');
    const nextDayEnd = moment(nextDay).format('HH:mm');
    row[nextDayString] = {
      startWorkTime: '00:00',
      endWorkTime: nextDayEnd,
      typeId,
    };
    updateChangedEmployeesWorkTime(employeePositionId, nextDayString, '00:00', nextDayEnd, typeId);
  }
};

const copyTop = ({ rowIndex }) => {
  const currentFilteredEmployeePosition = filteredEmployees.value[rowIndex];
  const prevFilteredEmployeePosition = filteredEmployees.value[rowIndex - 1];
  const currentEmployeePosition = employeesWorkTime.value.find(employeeWorkTime => employeeWorkTime.employeePositionId
    === currentFilteredEmployeePosition.employeePositionId);
  const keys = Object.keys(currentEmployeePosition);
  for (const key of keys) {
    if (moment(key, 'YYYY-MM-DD', true).isValid()) {
      currentEmployeePosition[key] = { ...prevFilteredEmployeePosition[key] };
      updateChangedEmployeesWorkTime(
        currentEmployeePosition.employeePositionId,
        key,
        null,
        null,
        null,
        { ...prevFilteredEmployeePosition[key] },
      );
    }
  }
};
const copyFrom = ({ employeePositionId, selectedEmployeePositionId }) => {
  const currentEmployeePosition = employeesWorkTime.value.find(employeeWorkTime => employeeWorkTime.employeePositionId
    === employeePositionId);
  const selectedEmployeePosition = employeesWorkTime.value.find(employeeWorkTime => employeeWorkTime.employeePositionId
    === selectedEmployeePositionId);
  const keys = Object.keys(currentEmployeePosition);
  for (const key of keys) {
    if (moment(key, 'YYYY-MM-DD', true).isValid()) {
      currentEmployeePosition[key] = { ...selectedEmployeePosition[key] };
      updateChangedEmployeesWorkTime(
        currentEmployeePosition.employeePositionId,
        key,
        null,
        null,
        null,
        { ...selectedEmployeePosition[key] },
      );
    }
  }
};
const clear = ({ rowIndex }) => {
  const currentFilteredEmployeePosition = filteredEmployees.value[rowIndex];
  const currentEmployeePosition = employeesWorkTime.value.find(employeeWorkTime => employeeWorkTime.employeePositionId
    === currentFilteredEmployeePosition.employeePositionId);
  const keys = Object.keys(currentEmployeePosition);
  const emptyData = { startWorkTime: '', endWorkTime: '', typeId: null };
  for (const key of keys) {
    if (moment(key, 'YYYY-MM-DD', true).isValid()) {
      currentEmployeePosition[key] = { ...emptyData };
      updateChangedEmployeesWorkTime(
        currentEmployeePosition.employeePositionId,
        key,
        null,
        null,
        null,
        { ...emptyData },
      );
    }
  }
};

const columns = ref([]);
const getMonthDays = (year: number, month: number) => {
  const days = [];
  const currentMonth = month;
  const date = new Date(year, currentMonth);
  while (date.getMonth() === currentMonth) {
    days.push(new Date(date));
    date.setDate(date.getDate() + 1);
  }
  return days;
};

const shiftsVariants = ref([]);
const workDayStatuses = ref([]);
const getRefBooks = async () => {
  await store.dispatch(actions.INC_LOADING);
  const result = await api('/working-time/get-ref-books');
  await store.dispatch(actions.DEC_LOADING);
  workDayStatuses.value = result.workDayStatuses;
  shiftsVariants.value = result.shiftsVariants;
};

onMounted(async () => {
  await getRefBooks();
});

const getColumns = () => {
  const columnTemplate = [
    {
      field: 'employeePositionId', key: 'employeePositionId', title: '№', align: 'left', width: 20,
    },
    {
      field: 'fio', key: 'fio', title: 'ФИО', align: 'left', width: 160, fixed: 'left',
    },
    {
      field: 'position',
      key: 'position',
      title: 'Должность',
      align: 'left',
      width: 115,
      fixed: 'left',
      renderBodyCell: ({ row, column, rowIndex }, h) => h(
        PositionCell,
        {
          props: {
            text: row[column.field] ? row[column.field] : '',
            tippyMaxWidth: '50%',
            rowIndex,
            employeePositionId: row.employeePositionId,
            employeePositions: employeesWorkTime.value,
          },
          on: {
            copyTop,
            copyFrom,
            clear,
          },
        },
      ),
    },
    {
      field: 'bidType', key: 'bidType', title: 'Тип', align: 'center', width: 30, fixed: 'left',
    },
  ];
  const daysMonth = getMonthDays(props.year, props.month);
  const data = daysMonth.map((col) => {
    const dateString = moment(col).format('YYYY-MM-DD');
    const dateTitle = col.toLocaleDateString('ru-RU', { weekday: 'short', day: '2-digit' });
    const weekend = [6, 0].includes(col.getDay());
    return {
      key: dateString,
      field: dateString,
      title: dateTitle,
      align: 'center',
      width: 47,
      isWeekend: weekend,
      renderBodyCell: ({ row, column }, h) => h(
        DateCell,
        {
          props: {
            workTime: row[column.field] ? row[column.field] : '',
            employeePositionId: row.employeePositionId,
            date: column.key,
            workDayStatuses: workDayStatuses.value,
            shiftsVariants: shiftsVariants.value,
            timeOptions: timeOptions.value,
            disabled: documentBlocked.value,
            lunchDuration: row.lunchDuration,
          },
          on: { changeWorkTime },
        },
      ),
    };
  });
  columnTemplate.push(...data);
  const totalHoursCol = {
    field: 'totalHoursDecimal', key: 'totalHoursDecimal', title: 'Все', align: 'center', width: 30, fixed: 'right',
  };
  const totalHoursWithMinCol = {
    field: 'totalHours', key: 'totalHours', title: 'чч:мм', align: 'center', width: 42, fixed: 'right',
  };
  columnTemplate.push(totalHoursCol);
  columnTemplate.push(totalHoursWithMinCol);
  columns.value = columnTemplate;
};

watch(() => [props.year, props.month], () => {
  if (props.year && props.month) {
    getColumns();
  }
}, { immediate: true });

const cellStyleOption = {
  bodyCellClass: ({ row, column }) => {
    const result = [];
    if (row.bidType === 'Вну') {
      result.push('table-body-cell-inner-bid');
    } else if (row.bidType === 'Вне') {
      result.push('table-body-cell-outer-bid');
    }
    if (column.key === 'fio') {
      result.push('table-body-name-cell');
    } else if (column.key === 'position') {
      result.push('table-body-position-cell');
    } else {
      result.push('table-body-cell');
    }
    return result.join(' ');
  },
  headerCellClass: ({ column }) => {
    const result = [];
    const nonDateKey = ['fio', 'position'];
    if (column.isWeekend) {
      result.push('table-header-cell-weekend');
    } else if (nonDateKey.includes(column.key)) {
      result.push('table-header-non-date-cell');
    } else {
      result.push('table-header-cell');
    }
    return result.join(' ');
  },
};
const columnHiddenOption = {
  defaultHiddenColumnKeys: ['employeePositionId'],
};
const virtualScrollOption = {
  enable: true,
};
const cellSelectionOption = {
  enable: false,
};
const rowStyleOption = {
  hoverHighlight: false,
  clickHighlight: false,
  stripe: false,
};
const save = async () => {
  if (!documentBlocked.value) {
    await store.dispatch(actions.INC_LOADING);
    const { ok, message } = await api('/working-time/update-time', {
      changedEmployeesWorkTime: changedEmployeesWorkTime.value,
      departmentId: props.department,
      year: props.year,
      month: props.month + 1,
    });
    await store.dispatch(actions.DEC_LOADING);
    if (ok) {
      root.$emit('msg', 'ok', 'Сохранено');
      await getEmployeesWorkTime();
    } else {
      root.$emit('msg', 'error', message);
    }
  } else {
    root.$emit('msg', 'error', 'Документ заблокирован');
  }
};

const printDocument = async () => {
  const apiForBlob = axios.create({
    baseURL: `${window.location.origin}/api`,
    responseType: 'blob',
  });
  await store.dispatch(actions.INC_LOADING);
  const result = await apiForBlob.post('/working-time/print-document', {
    employeesWorkTime: employeesWorkTime.value,
  });
  await store.dispatch(actions.DEC_LOADING);
  const urlFile = URL.createObjectURL(result.data);
  window.open(urlFile);
};

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
.white-background {
  background-color: #FFF;
}
.filters {
  margin: 0 10px;
}
.margins {
  margin: 5px 10px
}
.flex {
  display: flex;
  gap: 10px;
}
.flex-end {
  justify-content: flex-end;
}
.search {
  width: 760px;
}
.block-margin {
  margin: 0 10px;
}
.button-bottom {
  width: 770px;
}
</style>

<style lang="scss">
.table-header-cell-weekend {
  background-color: #b6e3ff !important;
  padding: 10px 0 !important;
}
.table-body-cell {
  padding: 10px 0 !important;
}
.table-header-cell {
  padding: 10px 0 !important;
}
.table-header-non-date-cell {
  padding: 10px 12px !important;
}
.table-body-name-cell {
  padding: 10px 0 10px 12px !important;
}
.table-body-position-cell {
  padding: 0 !important;
  white-space: normal !important;
}
.table-body-cell-inner-bid {
  background-color: #ddf3fe !important;
}
.table-body-cell-outer-bid {
  background-color: #ddf3fe !important;
}
</style>
