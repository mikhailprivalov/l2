<template>
  <div>
    <div
      v-if="noDocument && filtersFull"
      class="create-document"
    >
      <button
        class="btn btn-blue-nb"
        @click="createDocument"
      >
        Создать график
      </button>
    </div>
    <div v-if="!noDocument && filtersFull">
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
      class="white-background"
    >
      <VeTable
        max-height="calc(100vh - 200px)"
        :columns="columns"
        :table-data="filteredEmployees"
        :row-style-option="rowStyleOption"
        :cell-style-option="cellStyleOption"
        :column-hidden-option="columnHiddenOption"
        :border-y="true"
        :scroll-width="0"
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
  computed, getCurrentInstance, ref, watch,
} from 'vue';
import { VeTable } from 'vue-easytable';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import 'vue-easytable/libs/theme-default/index.css';
import moment from 'moment';

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
};

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

const changeWorkTime = async () => {
  await getEmployeesWorkTime();
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
const getColumns = () => {
  const columnTemplate = [
    {
      field: 'employeePositionId', key: 'employeePositionId', title: '№', align: 'center', width: 20, fixed: 'center',
    },
    {
      field: 'fio', key: 'fio', title: 'ФИО', align: 'center', width: 165, fixed: 'left',
    },
    {
      field: 'position',
      key: 'position',
      title: 'Должность',
      align: 'center',
      width: 115,
      fixed: 'left',
      isPosition: true,
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
  bodyCellClass: ({ column }) => {
    if (column.isPosition) {
      return '';
    }
    return 'table-body-cell';
  },
  headerCellClass: ({ column }) => {
    if (column.isWeekend) {
      return 'table-header-cell-weekend';
    }
    return 'table-header-cell';
  },
};
const rowStyleOption = {
  stripe: true,
};
const columnHiddenOption = {
  defaultHiddenColumnKeys: ['employeePositionId'],
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
.create-document {
  margin: 5px 10px
}
</style>

<style lang="scss">
.table-header-cell-weekend {
  background-color: #cbf2cb !important;
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
</style>
