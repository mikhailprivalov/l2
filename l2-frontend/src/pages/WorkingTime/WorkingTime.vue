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
      <div class="filters department-lunch">
        <label>Обед подразделения: {{ lunchDurationSelectedDepartment }} м.</label>
      </div>
    </div>
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
        v-show="documentCreated && filtersFull"
      >
        <TemplateTable
          :shifts-variants="shiftsVariants"
          :time-options="timeOptions"
          :work-day-statuses="workDayStatuses"
          :department-lunch-duration="lunchDurationSelectedDepartment"
          :holidays="holidays"
          :refresh-key="templateTableRefreshKey"
          :month-days="monthDays"
          @fillInTemplate="fillInTemplateData"
          @fillByEmployeeTemplate="fillByEmployeeTemplate"
          @fillColumnByTemplate="fillColumnByTemplate"
        />
      </div>
      <div
        class="white-background"
      >
        <VeTable
          max-height="calc(100vh - 290px)"
          :columns="columns"
          :table-data="filteredAndSortedEmployees"
          :cell-style-option="cellStyleOption"
          :column-hidden-option="columnHiddenOption"
          :virtual-scroll-option="virtualScrollOption"
          row-key-field-name="employeePositionId"
          :checkbox-option="checkboxOption"
          :cell-selection-option="cellSelectionOption"
          :row-style-option="rowStyleOption"
          :border-y="true"
          :scroll-width="0"
        />
        <div
          v-if="documentCreated && filtersFull"
          class="buttons-bottom"
        >
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
            :disabled="hasChange"
            @click.prevent="downloadXlsx()"
          >
            XLSX
          </button>
          <button
            class="btn btn-blue-nb"
            :disabled="hasChange"
            @click.prevent="printDocument()"
          >
            PDF
          </button>
          <button
            class="btn btn-blue-nb"
            :disabled="hasChange"
            @click.prevent="downloadTabelXlsx()"
          >
            Табель
          </button>
        </div>
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
import moment from 'moment/moment';
import axios from 'axios';

import api from '@/api';
import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import TemplateTable from '@/pages/WorkingTime/TemplateTable.vue';
import PositionCell from '@/pages/WorkingTime/PositionCell.vue';
import DateCell from '@/pages/WorkingTime/DateCell.vue';
import FioHeader from '@/pages/WorkingTime/FioHeader.vue';
import PositionHeader from '@/pages/WorkingTime/PositionHeader.vue';
import FioCell from '@/pages/WorkingTime/FioCell.vue';
import {
  DepartmentItem, EMPTY_WORK_TIME_DAY_CELL,
  GetEmployeesWorkTimeResult,
  HolidaysMap, RefBooksResponse,
  SelectOptionItem, ShiftVariantItem, TableColumn, TimeOptionItem, WorkDayStatusItem, WorkTimeDayCell,
} from '@/pages/WorkingTime/types/types';
import {
  formatDateKey, formatDateTitle,
  getMonthDays, getYears, isISODateString, MONTHS,
} from '@/pages/WorkingTime/utils/date';

const store = useStore();
const root = getCurrentInstance().proxy.$root;
const currentDate = ref(new Date());

const selectedMonth = ref(currentDate.value.getMonth());
const months = ref<SelectOptionItem[]>(MONTHS);

const selectedYear = ref(currentDate.value.getFullYear());
const years = ref<SelectOptionItem[]>(getYears(currentDate.value.getFullYear()));

const selectedDepartment = ref(null);
const lunchDurationSelectedDepartment = ref(0);
const departments = ref<DepartmentItem[]>([]);
const getDepartments = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result }: { result: DepartmentItem[] } = await api('/working-time/get-departments');
  await store.dispatch(actions.DEC_LOADING);
  departments.value = result;
};

const shiftsVariants = ref<ShiftVariantItem[]>([]);
const workDayStatuses = ref<WorkDayStatusItem[]>([]);
const getRefBooks = async () => {
  await store.dispatch(actions.INC_LOADING);
  const result: RefBooksResponse = await api('/working-time/get-ref-books');
  await store.dispatch(actions.DEC_LOADING);
  workDayStatuses.value = result.workDayStatuses;
  shiftsVariants.value = result.shiftsVariants;
};

const holidays = ref<HolidaysMap>({});
const getHolidays = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result }: { result: HolidaysMap } = await api('/working-time/get-holidays', {
    year: selectedYear.value,
    month: selectedMonth.value + 1,
  });
  await store.dispatch(actions.DEC_LOADING);
  holidays.value = result;
};

const findDepartmentLunchDuration = () => {
  const currentDepartment = departments.value.find(department => department.id === selectedDepartment.value);
  lunchDurationSelectedDepartment.value = currentDepartment.lunchDuration ? currentDepartment.lunchDuration : 0;
};

watch(selectedDepartment, () => {
  findDepartmentLunchDuration();
});

onMounted(() => {
  getDepartments();
  getRefBooks();
});

const filtersFull = computed(() => !!(selectedYear.value && selectedMonth.value != null && selectedDepartment.value));
const timeOptions = computed<TimeOptionItem[]>(() => (store.getters.modules.working_time_variants
  ? JSON.parse(store.getters.modules.working_time_variants) : []));

const documentId = ref<number | null>(null);
const documentCreated = ref(false);
const documentBlocked = ref(false);

const employeesWorkTime = ref([]);
const changedEmployeesWorkTime = ref({});
const hasChange = ref(false);

const getEmployeesWorkTime = async () => {
  employeesWorkTime.value = [];
  changedEmployeesWorkTime.value = {};
  hasChange.value = false;
  await store.dispatch(actions.INC_LOADING);
  const { result }: { result: GetEmployeesWorkTimeResult } = await api('/working-time/get-work-time', {
    year: selectedYear.value,
    month: selectedMonth.value + 1,
    departmentId: selectedDepartment.value,
  });
  await store.dispatch(actions.DEC_LOADING);
  const {
    data, documentPk, documentIsBlocked, documentIsCreated,
  } = result;
  employeesWorkTime.value = data;
  documentId.value = documentPk;
  documentCreated.value = documentIsCreated;
  documentBlocked.value = documentIsBlocked;
};

watch(employeesWorkTime, () => {
  for (const employee of employeesWorkTime.value) {
    let totalDiffTime = 0;
    const keys = Object.keys(employee);
    const lunchDuration = employee.lunchDuration * 60 * 1000;
    for (const key of keys) {
      if (isISODateString(key)) {
        const currentDay: WorkTimeDayCell = employee[key];
        if (currentDay.startWorkTime && currentDay.endWorkTime && !currentDay.typeId) {
          const startTime = new Date(`${key} ${currentDay.startWorkTime}`);
          let endTime;
          if (currentDay.endWorkTime === '00:00') {
            endTime = new Date(startTime.getFullYear(), startTime.getMonth(), startTime.getDate() + 1, 0, 0);
          } else {
            endTime = new Date(`${key} ${currentDay.endWorkTime}`);
          }
          const dayDiffTime = endTime.getTime() - startTime.getTime() - lunchDuration;
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

watch([selectedYear, selectedMonth, selectedDepartment], () => {
  if (filtersFull.value) {
    getEmployeesWorkTime();
  }
}, { immediate: true });

const cellStyleOption = ref({
  bodyCellClass: ({ row, column }) => {
    const result = [];
    if (row.bidType !== 'Осн') {
      result.push('table-body-bid-cell');
    }
    if (column.isHoliday) {
      result.push('table-body-holiday-cell');
    } else if (column.isWeekend) {
      result.push('table-body-weekend-cell');
    }
    if (row[column.key]?.blocked) {
      result.push('table-body-blocked-cell');
    }
    if (column.key === 'fio') {
      result.push('table-body-name-cell');
    } else if (column.key === 'position') {
      result.push('table-body-position-cell');
    } else if (column.key === 'checkbox') {
      result.push('table-checkbox-cell');
    } else {
      result.push('table-body-cell');
    }
    return result.join(' ');
  },
  headerCellClass: ({ column }) => {
    const result = [];
    const nonDateKey = ['position'];
    if (column.isHoliday) {
      result.push('table-header-holiday-cell');
    } else if (column.isWeekend) {
      result.push('table-header-weekend-cell');
    } else if (nonDateKey.includes(column.key)) {
      result.push('table-header-non-date-cell');
    } else if (column.key === 'checkbox') {
      result.push('table-header-checkbox-cell');
    } else {
      result.push('table-header-cell');
    }
    return result.join(' ');
  },
});
const columnHiddenOption = ref({
  defaultHiddenColumnKeys: ['employeePositionId'],
});
const virtualScrollOption = ref({
  enable: true,
});
const cellSelectionOption = ref({
  enable: false,
});
const rowStyleOption = ref({
  hoverHighlight: false,
  clickHighlight: false,
  stripe: false,
});
const checkboxOption = ref({
  selectedRowKeys: [],
  selectedRowChange: ({ selectedRowKeys }) => {
    checkboxOption.value.selectedRowKeys = selectedRowKeys;
  },
  selectedAllChange: ({ selectedRowKeys }) => {
    checkboxOption.value.selectedRowKeys = selectedRowKeys;
  },
});

const filters = ref({
  fio: '',
  positions: [],
});

const changeFilterFio = (searchValue: string) => {
  filters.value.fio = searchValue;
};

const changeFilterPositions = (selectedPosition: object[]) => {
  filters.value.positions = selectedPosition;
};

const sorts = ref('none');

const sortChange = (sortType: string) => {
  sorts.value = sortType;
};

watch([filters, sorts], () => {
  checkboxOption.value.selectedRowKeys = [];
}, { deep: true });

const filteredAndSortedEmployees = computed(() => {
  const searchedFio = filters.value.fio.toLowerCase();
  const searchedPositions = filters.value.positions;
  const filteredEmployees = employeesWorkTime.value.filter(employee => {
    const employeeFio = employee.fio?.toLowerCase();
    const employeePosition = employee.position;
    return employeeFio.includes(searchedFio) && (searchedPositions.length === 0 || searchedPositions.includes(employeePosition));
  });
  return filteredEmployees.sort((first, second) => {
    const firstPosition = first.position.toLowerCase();
    const secondPosition = second.position.toLowerCase();
    const firstFio = first.fio.toLowerCase();
    const secondFio = second.fio.toLowerCase();
    if (sorts.value === 'asc') {
      return firstPosition.localeCompare(secondPosition);
    }
    if (sorts.value === 'desc') {
      return secondPosition.localeCompare(firstPosition);
    }
    return firstFio.localeCompare(secondFio);
  });
});

const updateChangedEmployeesWorkTime = (
  employeePositionId: number,
  date: string,
  startWorkTime: string = null,
  endWorkTime: string = null,
  typeId: number = null,
  fullData: object = null,
  lunchDuration: number = null,
) => {
  if (!Object.hasOwn(changedEmployeesWorkTime.value, employeePositionId)) {
    changedEmployeesWorkTime.value[employeePositionId] = { lunchDuration };
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
  hasChange.value = true;
};

const changeWorkTime = async ({
  employeePositionId, date, startWorkTime, endWorkTime, typeId, nextDayEndWork,
}) => {
  const row = employeesWorkTime.value.find(employeePosition => employeePosition.employeePositionId === employeePositionId);
  const { lunchDuration } = row;
  row[date] = {
    startWorkTime,
    endWorkTime,
    typeId,
  };
  updateChangedEmployeesWorkTime(employeePositionId, date, startWorkTime, endWorkTime, typeId, null, lunchDuration);
  if (nextDayEndWork) {
    const nextDay = nextDayEndWork;
    const nextDayString = formatDateKey(nextDay);
    const nextDayEnd = moment(nextDay).format('HH:mm');
    row[nextDayString] = {
      startWorkTime: '00:00',
      endWorkTime: nextDayEnd,
      typeId,
    };
    updateChangedEmployeesWorkTime(
      employeePositionId,
      nextDayString,
      '00:00',
      nextDayEnd,
      typeId,
      null,
      lunchDuration,
    );
  }
};

const fillInTemplateData = ({ templateData }) => {
  for (const employeePosition of employeesWorkTime.value) {
    if (checkboxOption.value.selectedRowKeys.includes(employeePosition.employeePositionId)) {
      const keys = Object.keys(employeePosition);
      const { lunchDuration } = employeePosition;
      for (const key of keys) {
        if (isISODateString(key)) {
          employeePosition[key] = { ...templateData[key] };
          updateChangedEmployeesWorkTime(
            employeePosition.employeePositionId,
            key,
            null,
            null,
            null,
            { ...templateData[key] },
            lunchDuration,
          );
        }
      }
    }
  }
  checkboxOption.value.selectedRowKeys = [];
};

const fillByEmployeeTemplate = async ({ action }) => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('/working-time/get-work-time-filling-by-employee-template', {
    year: selectedYear.value,
    month: selectedMonth.value + 1,
    departmentId: selectedDepartment.value,
    action,
  });
  await store.dispatch(actions.DEC_LOADING);
  employeesWorkTime.value = result;
  for (const employeePosition of result) {
    const { employeePositionId } = employeePosition;
    const { lunchDuration } = employeePosition;
    for (const [key, value] of Object.entries(employeePosition)) {
      if (isISODateString(key)) {
        updateChangedEmployeesWorkTime(employeePositionId, key, null, null, null, value, lunchDuration);
      }
    }
  }
};

const fillColumnByTemplate = ({
  date, startWork, endWork, typeId,
}) => {
  for (const employeePosition of employeesWorkTime.value) {
    const { lunchDuration } = employeePosition;
    const { employeePositionId } = employeePosition;
    if (checkboxOption.value.selectedRowKeys.length === 0) {
      employeePosition[date] = { startWorkTime: startWork, endWorkTime: endWork, typeId };
      updateChangedEmployeesWorkTime(employeePositionId, date, startWork, endWork, typeId, null, lunchDuration);
    } else if (checkboxOption.value.selectedRowKeys.includes(employeePositionId)) {
      employeePosition[date] = { startWorkTime: startWork, endWorkTime: endWork, typeId };
      updateChangedEmployeesWorkTime(employeePositionId, date, startWork, endWork, typeId, null, lunchDuration);
    }
  }
};

const copyTop = ({ rowIndex }) => {
  const currentFilteredEmployeePosition = filteredAndSortedEmployees.value[rowIndex];
  const prevFilteredEmployeePosition = filteredAndSortedEmployees.value[rowIndex - 1];
  const currentEmployeePosition = employeesWorkTime.value.find(employee => employee.employeePositionId
    === currentFilteredEmployeePosition.employeePositionId);
  const { lunchDuration } = currentEmployeePosition;
  const keys = Object.keys(currentEmployeePosition);
  for (const key of keys) {
    if (isISODateString(key)) {
      currentEmployeePosition[key] = { ...prevFilteredEmployeePosition[key] };
      updateChangedEmployeesWorkTime(
        currentEmployeePosition.employeePositionId,
        key,
        null,
        null,
        null,
        { ...prevFilteredEmployeePosition[key] },
        lunchDuration,
      );
    }
  }
};
const copyFrom = ({ employeePositionId, selectedEmployeePositionId }) => {
  const currentEmployeePosition = employeesWorkTime.value.find(employeeWorkTime => employeeWorkTime.employeePositionId
    === employeePositionId);
  const { lunchDuration } = currentEmployeePosition;
  const selectedEmployeePosition = employeesWorkTime.value.find(employeeWorkTime => employeeWorkTime.employeePositionId
    === selectedEmployeePositionId);
  const keys = Object.keys(currentEmployeePosition);
  for (const key of keys) {
    if (isISODateString(key)) {
      currentEmployeePosition[key] = { ...selectedEmployeePosition[key] };
      updateChangedEmployeesWorkTime(
        currentEmployeePosition.employeePositionId,
        key,
        null,
        null,
        null,
        { ...selectedEmployeePosition[key] },
        lunchDuration,
      );
    }
  }
};
const clear = ({ rowIndex }) => {
  const currentFilteredEmployeePosition = filteredAndSortedEmployees.value[rowIndex];
  const currentEmployeePosition = employeesWorkTime.value.find(employeeWorkTime => employeeWorkTime.employeePositionId
    === currentFilteredEmployeePosition.employeePositionId);
  const { lunchDuration } = currentEmployeePosition;
  const keys = Object.keys(currentEmployeePosition);
  const emptyData = { startWorkTime: '', endWorkTime: '', typeId: null };
  for (const key of keys) {
    if (isISODateString(key)) {
      currentEmployeePosition[key] = { ...emptyData };
      updateChangedEmployeesWorkTime(
        currentEmployeePosition.employeePositionId,
        key,
        null,
        null,
        null,
        { ...emptyData },
        lunchDuration,
      );
    }
  }
};

const employeeTransfer = async ({ employeePositionId, date }) => {
  await store.dispatch(actions.INC_LOADING);
  const { ok, message } = await api('/working-time/employee-transfer', {
    employeePositionId,
    date,
  });
  await store.dispatch(actions.DEC_LOADING);
  if (ok) {
    root.$emit('msg', 'ok', 'Сохранено');
    await getEmployeesWorkTime();
  } else {
    root.$emit('msg', 'error', message);
  }
};

const editLunch = async ({ employeePositionId, lunchDurationInMinutes }) => {
  await store.dispatch(actions.INC_LOADING);
  const { ok, message } = await api('/working-time/edit-lunch', {
    employeePositionId,
    lunchDurationInMinutes,
  });
  await store.dispatch(actions.DEC_LOADING);
  if (ok) {
    root.$emit('msg', 'ok', 'Сохранено');
    await getEmployeesWorkTime();
  } else {
    root.$emit('msg', 'error', message);
  }
};

const fillDayOff = ({
  employeePositionId, workDayStatusId, dayOffStart, dayOffEnd,
}) => {
  const dayOffStartDate = moment(dayOffStart);
  const dayOffEndDate = moment(dayOffEnd);
  const currentEmployeePosition = employeesWorkTime.value.find(employeeWorkTime => employeeWorkTime.employeePositionId
      === employeePositionId);
  const { lunchDuration } = currentEmployeePosition;
  const fullData = { startWorkTime: '', endWorkTime: '', typeId: workDayStatusId };
  for (let day = moment(dayOffStartDate); day <= dayOffEndDate; day.add(1, 'day')) {
    const date = day.format('YYYY-MM-DD');
    currentEmployeePosition[date] = { ...fullData };
    updateChangedEmployeesWorkTime(
      employeePositionId,
      date,
      null,
      null,
      null,
      { ...fullData },
      lunchDuration,
    );
  }
};

const columns = ref<TableColumn[]>([]);

const monthDays = ref<Date[]>([]);
const firstDayMonth = computed(() => formatDateKey(new Date(selectedYear.value, selectedMonth.value, 1)));
const lastDayMonth = computed(() => formatDateKey(new Date(selectedYear.value, selectedMonth.value + 1, 0)));

const getColumns = () => {
  const columnTemplate: TableColumn[] = [
    {
      field: 'checkbox', key: 'checkbox', type: 'checkbox', title: '', align: 'center', width: 25, fixed: 'left',
    },
    {
      field: 'employeePositionId',
      key: 'employeePositionId',
      title: '№',
      align: 'center',
      width: 20,
    },
    {
      field: 'fio',
      key: 'fio',
      title: 'ФИО',
      align: 'left',
      width: 160,
      fixed: 'left',
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      renderHeaderCell: ({ column }, h) => h(
        FioHeader,
        {
          on: {
            input: changeFilterFio,
          },
        },
      ),
      renderBodyCell: ({ row, column }, h) => h(
        FioCell,
        {
          props: {
            text: row[column.field] ? row[column.field] : '',
            tippyMaxWidth: '50%',
            employeePositionId: row.employeePositionId,
          },
          on: {
            employeeTransfer,
          },
        },
      ),
    },
    {
      field: 'position',
      key: 'position',
      title: 'Должность',
      align: 'left',
      width: 130,
      fixed: 'left',
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      renderHeaderCell: ({ column }, h) => h(
        PositionHeader,
        {
          props: { employeePositions: employeesWorkTime.value },
          on: {
            input: changeFilterPositions,
            sort: sortChange,
          },
        },
      ),
      renderBodyCell: ({ row, column, rowIndex }, h) => h(
        PositionCell,
        {
          props: {
            text: row[column.field] ? row[column.field] : '',
            tippyMaxWidth: '50%',
            rowIndex,
            employeePositionId: row.employeePositionId,
            employeeLunchDuration: row.lunchDuration,
            employeePositions: employeesWorkTime.value,
            firstDayMonth: firstDayMonth.value,
            lastDayMonth: lastDayMonth.value,
            workDayStatuses: workDayStatuses.value,
          },
          on: {
            copyTop,
            copyFrom,
            clear,
            editLunch,
            fillDayOff,
          },
        },
      ),
    },
    {
      field: 'bidType', key: 'bidType', title: 'Тип', align: 'center', width: 30, fixed: 'left',
    },
  ];
  const daysMonth = [...monthDays.value];
  const data: TableColumn[] = daysMonth.map((col) => {
    const dateString = formatDateKey(col);
    const dateTitle = formatDateTitle(col);
    const weekend = [6, 0].includes(col.getDay());
    const holiday = holidays.value[dateString]?.kind === 'HOLIDAY';
    return {
      key: dateString,
      field: dateString,
      title: dateTitle,
      align: 'center',
      width: 47,
      isWeekend: weekend,
      isHoliday: holiday,
      renderBodyCell: ({ row, column }, h) => h(
        DateCell,
        {
          props: {
            workTime: row[column.field] ? row[column.field] : EMPTY_WORK_TIME_DAY_CELL,
            employeePositionId: row.employeePositionId,
            date: column.key,
            workDayStatuses: workDayStatuses.value,
            shiftsVariants: shiftsVariants.value,
            timeOptions: timeOptions.value,
            documentBlocked: documentBlocked.value,
            lunchDuration: row.lunchDuration,
          },
          on: { changeWorkTime },
        },
      ),
    };
  });
  columnTemplate.push(...data);
  const totalHoursCol: TableColumn = {
    field: 'totalHoursDecimal', key: 'totalHoursDecimal', title: 'Все', align: 'center', width: 30, fixed: 'right',
  };
  const totalHoursWithMinCol: TableColumn = {
    field: 'totalHours', key: 'totalHours', title: 'чч:мм', align: 'center', width: 42, fixed: 'right',
  };
  columnTemplate.push(totalHoursCol);
  columnTemplate.push(totalHoursWithMinCol);
  columns.value = columnTemplate;
};

const templateTableRefreshKey = ref(0);
watch([selectedYear, selectedMonth], async () => {
  if (selectedYear.value && selectedMonth.value != null) {
    monthDays.value = getMonthDays(selectedYear.value, selectedMonth.value);
    await getHolidays();
    templateTableRefreshKey.value += 1;
    getColumns();
  }
}, { immediate: true });

const save = async () => {
  if (!documentBlocked.value) {
    await store.dispatch(actions.INC_LOADING);
    const { ok, message } = await api('/working-time/update-time', {
      changedEmployeesWorkTime: changedEmployeesWorkTime.value,
      departmentId: selectedDepartment.value,
      year: selectedYear.value,
      month: selectedMonth.value + 1,
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

const createDocument = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { ok, message } = await api('/working-time/create-document', {
    year: selectedYear.value,
    month: selectedMonth.value + 1,
    departmentId: selectedDepartment.value,
  });
  await store.dispatch(actions.DEC_LOADING);
  if (ok) {
    await getEmployeesWorkTime();
  } else {
    root.$emit('msg', 'error', message);
  }
};

const printDocument = async () => {
  if (hasChange.value) {
    root.$emit('msg', 'error', 'Есть не сохраненные изменения');
  } else {
    const apiForBlob = axios.create({
      baseURL: `${window.location.origin}/forms`,
      responseType: 'blob',
    });
    await store.dispatch(actions.INC_LOADING);
    const result = await apiForBlob.post('/pdf?type=300.01', {
      employeesWorkTime: employeesWorkTime.value,
      documentId: documentId.value,
    });
    await store.dispatch(actions.DEC_LOADING);
    const urlFile = URL.createObjectURL(result.data);
    window.open(urlFile);
  }
};

const downloadXlsx = async () => {
  if (hasChange.value) {
    root.$emit('msg', 'error', 'Есть не сохраненные изменения');
  } else {
    const apiForBlob = axios.create({
      baseURL: `${window.location.origin}/forms`,
      responseType: 'blob',
    });
    await store.dispatch(actions.INC_LOADING);
    const result = await apiForBlob.post('/xlsx?type=104.01', {
      employeesWorkTime: employeesWorkTime.value,
      documentId: documentId.value,
    });
    await store.dispatch(actions.DEC_LOADING);
    const blob = new Blob([result.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    const urlFile = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = urlFile;
    const contentDisposition = result.headers['content-disposition'];
    let fileName = 'form.xlsx';
    if (contentDisposition) {
      const match = contentDisposition.match(/filename="?([^"]+?)(?:_)?"?$/);
      if (match?.[1]) {
        [, fileName] = match;
      }
    }
    link.setAttribute('download', fileName);
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(urlFile);
  }
};

const downloadTabelXlsx = async () => {
  window.open(`/forms/xlsx?type=104.02&year=${selectedYear.value}&month=${selectedMonth.value + 1}&departmentId=
  ${selectedDepartment.value}`, '_blank');
};

</script>

<style scoped lang="scss">
.main {
  width: 100%;
  margin: 0 auto;
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
.department-lunch {
  width: 200px;
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
.buttons-bottom {
  display: flex;
  justify-content: flex-end;
  gap: 5px;
}
::v-deep .ve-table-header-tr {
  height: 35px !important;
}
</style>

<style lang="scss">
.table-body-weekend-cell {
  background-color: #b6e3ff !important;
  padding: 10px 0 !important;
}
.table-body-holiday-cell {
  background-color: #9fd8ff !important;
  padding: 10px 0 !important;
}
.template-table-body-weekend-cell {
  background-color: #b6e3ff !important;
  padding: 0 !important;
}
.template-table-body-holiday-cell {
  background-color: #9fd8ff !important;
  padding: 0 !important;
}
.table-header-weekend-cell {
  background-color: #b6e3ff !important;
  padding: 0 !important;
}
.table-header-holiday-cell {
  background-color: #9fd8ff !important;
  padding: 0 !important;
}
.table-body-cell {
  padding: 10px 0 !important;
}
.table-body-blocked-cell {
  background: linear-gradient(rgba(101,109,120,0.4), rgba(101,109,120,0.4));
}
.template-table-body-cell {
  padding: 0 !important;
}
.table-header-cell {
  padding: 0 !important;
}
.table-header-non-date-cell {
  padding: 0 12px !important;
}
.table-body-name-cell {
  padding: 0 0 0 12px !important;
  white-space: normal !important;
}
.table-body-position-cell {
  padding: 0 !important;
  white-space: normal !important;
}
.table-body-bid-cell {
  font-style: italic !important;
}
.table-header-checkbox-cell {
  padding: 0 5px 0 5px !important;
}
.table-checkbox-cell {
  padding: 10px 5px 5px 5px !important;
}
</style>
