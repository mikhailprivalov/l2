<template>
  <div>
    <div
      class="flex margins"
    >
      <button
        v-if="noDocument && filtersFull"
        class="btn btn-blue-nb"
        @click="createDocument"
      >
        Создать график
      </button>
    </div>
    <div
      v-if="!noDocument && filtersFull"
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
        v-if="!noDocument && filtersFull"
        class="btn btn-blue-nb"
        @click="save"
      >
        Сохранить
      </button>
      <button
        v-if="!noDocument && filtersFull"
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
      <div class="flex flex-end">
        <button
          v-if="!noDocument && filtersFull"
          class="btn btn-blue-nb"
          @click="save"
        >
          Сохранить
        </button>
        <button
          v-if="!noDocument && filtersFull"
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
import VueTippyDiv from '@/pages/ManageChambers/components/VueTippyDiv.vue';
import { useStore } from '@/store';
import * as actions from '@/store/action-types';

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

const search = ref('');

const noDocument = ref(false);

const employeesWorkTime = ref([]);
const changedEmployeesWorkTime = ref({});

const getEmployeesWorkTime = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('/working-time/get-work-time', {
    year: props.year,
    month: props.month + 1,
    departmentId: props.department,
  });
  await store.dispatch(actions.DEC_LOADING);
  if (result.length > 0) {
    employeesWorkTime.value = result;
    noDocument.value = false;
  } else {
    employeesWorkTime.value = [];
    noDocument.value = true;
  }
  changedEmployeesWorkTime.value = {};
};

watch(employeesWorkTime, () => {
  for (const employee of employeesWorkTime.value) {
    let tmpTotalHours = 0.0;
    const keys = Object.keys(employee);
    const lunchDuration = employee.lunchDuration / 60;
    for (const key of keys) {
      if (moment(key, 'YYYY-MM-DD', true).isValid()) {
        const currentDay = employee[key];
        const startTime = new Date(`${key} ${currentDay.startWorkTime}`);
        const endTime = new Date(`${key} ${currentDay.endWorkTime}`);
        const { typeId } = currentDay;
        if (!typeId) {
          const diffTime = (endTime - startTime) / (1000 * 60 * 60);
          tmpTotalHours += diffTime;
        }
      }
    }
    tmpTotalHours -= lunchDuration;
    employee.totalHours = tmpTotalHours.toFixed(1);
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
  employeePositionId, date, startWorkTime, endWorkTime, typeId,
}) => {
  const row = employeesWorkTime.value.find(employeePosition => employeePosition.employeePositionId === employeePositionId);
  row[date] = {
    startWorkTime,
    endWorkTime,
    typeId,
  };
  if (!Object.hasOwn(changedEmployeesWorkTime.value, employeePositionId)) {
    changedEmployeesWorkTime.value[employeePositionId] = {};
  }
  changedEmployeesWorkTime.value[employeePositionId][date] = {
    startWorkTime,
    endWorkTime,
    typeId,
  };
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

const workDayStatuses = ref([]);
const getRefBooks = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('/working-time/get-ref-books');
  await store.dispatch(actions.DEC_LOADING);
  workDayStatuses.value = result;
};

onMounted(async () => {
  await getRefBooks();
});

const getColumns = () => {
  const columnTemplate = [
    {
      field: 'employeePositionId', key: 'employeePositionId', title: '№', align: 'left', width: 20, fixed: 'center',
    },
    {
      field: 'fio', key: 'fio', title: 'ФИО', align: 'left', width: 165, fixed: 'left',
    },
    {
      field: 'position',
      key: 'position',
      title: 'Должность',
      align: 'center',
      width: 115,
      fixed: 'left',
      renderBodyCell: ({ row, column }, h) => h(
        VueTippyDiv,
        {
          props: {
            text: row[column.field] ? row[column.field] : '',
            tippyMaxWidth: '50%',
            ellipsis: true,
          },
          class: 'position-text',
        },
      ),
    },
    {
      field: 'bidType', key: 'bidType', title: 'Тип', align: 'center', width: 50,
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
      width: 49,
      isWeekend: weekend,
      renderBodyCell: ({ row, column }, h) => h(
        DateCell,
        {
          props: {
            workTime: row[column.field] ? row[column.field] : '',
            employeePositionId: row.employeePositionId,
            date: column.key,
            workDayStatuses: workDayStatuses.value,
          },
          on: { changeWorkTime },
        },
      ),
    };
  });
  columnTemplate.push(...data);
  const totalHoursCol = {
    field: 'totalHours', key: 'totalHours', title: 'Все', align: 'center', width: 40,
  };
  columnTemplate.push(totalHoursCol);
  columns.value = columnTemplate;
};

watch(() => [props.year, props.month], () => {
  if (props.year && props.month) {
    getColumns();
  }
}, { immediate: true });

const cellStyleOption = {
  bodyCellClass: ({ row }) => {
    const result = [];
    if (row.bidType === 'Внут') {
      result.push('table-body-cell-inner-bid');
    } else if (row.bidType === 'Внеш') {
      result.push('table-body-cell-outer-bid');
    }
    result.push('table-body-cell');
    return result.join(' ');
  },
  headerCellClass: ({ column }) => {
    if (column.isWeekend) {
      return 'table-header-cell-weekend';
    }
    return 'table-header-cell';
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
  flex: 1;
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
.table-body-position-cell {
  padding: 10px 2px !important;
}
.position-text {
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}
.table-body-cell-inner-bid {
  background-color: #ddf3fe !important;
}
.table-body-cell-outer-bid {
  background-color: #ddf3fe !important;
}
</style>
