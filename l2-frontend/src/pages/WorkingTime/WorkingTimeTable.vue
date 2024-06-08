<template>
  <div>
    <div>
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
        v-show="filteredEmployees.length > 0"
        :max-height="600"
        :columns="columns"
        :table-data="filteredEmployees"
        :row-style-option="rowStyleOption"
        :cell-style-option="cellStyleOption"
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
  computed, getCurrentInstance, onMounted, ref, watch,
} from 'vue';
import { VeTable } from 'vue-easytable';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import 'vue-easytable/libs/theme-default/index.css';
import moment from 'moment';

import api from '@/api';
import DateCell from '@/pages/WorkingTime/DateCell.vue';
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
    required: true,
  },
});
const root = getCurrentInstance().proxy.$root;

const search = ref('');

const employeesWorkTime = ref([]);

const getEmployeesWorkTime = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('/working-time/get-work-time', {
    year: props.year,
    month: props.month + 1,
    departmentId: props.department,
  });
  await store.dispatch(actions.DEC_LOADING);
  employeesWorkTime.value = result;
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

const changeWorkTime = async (workTime: object) => {
  const {
    start, end, rowIndex, columnKey,
  } = workTime;
  filteredEmployees.value[rowIndex][columnKey] = { startWorkTime: start, endWorkTime: end };
  root.$emit('msg', 'ok', 'Обновлено');
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
      width: 95,
      isWeekend: weekend,
      renderBodyCell: ({ row, column, rowIndex }, h) => h(
        DateCell,
        {
          props: {
            workTime: row[column.field] ? row[column.field] : '',
            rowIndex,
            columnKey: column.key,
          },
          on: { changeWorkTime },
        },
      ),
    };
  });
  columnTemplate.push(...data);
  columns.value = columnTemplate;
};

watch(() => [props.year, props.month], () => {
  if (props.year && props.month) {
    getColumns();
  }
}, { immediate: true });

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
</style>

<style lang="scss">
.table-body-cell-weekend {
  background: #ade0a875 !important;;
}
.table-header-cell-weekend {
  background: #ade0a875 !important;
}
</style>
