<template>
  <VeTable
    :columns="columns"
    :table-data="templateData"
    :cell-style-option="cellStyleOption"
    :border-y="true"
    :scroll-width="0"
    :show-header="false"
  />
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { VeTable } from 'vue-easytable';
import 'vue-easytable/libs/theme-default/index.css';
import moment from 'moment/moment';

import DateCell from '@/pages/WorkingTime/DateCell.vue';

const props = defineProps({
  year: {
    type: Number,
    required: true,
  },
  month: {
    type: Number,
    required: true,
  },
  workDayStatuses: {
    type: Array,
    required: true,
  },
  shiftsVariants: {
    type: Array,
    required: true,
  },
  timeOptions: {
    type: Array,
    required: true,
  },
  departmentLunchDuration: {
    type: Number,
    required: true,
  },
});

const monthDays = ref([]);
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
onMounted(() => {
  monthDays.value = getMonthDays(props.year, props.month);
});
const columns = ref([]);

const templateData = ref([]);
const createTemplateData = () => {
  const result = {};
  for (const col of monthDays.value) {
    const dateString = moment(col).format('YYYY-MM-DD');
    result[dateString] = { startWorkTime: '', endWorkTime: '', typeId: null };
  }
  templateData.value = [{ ...result }];
};

onMounted(() => {
  createTemplateData();
});

const changeTemplateTime = async ({
  date, startWorkTime, endWorkTime, typeId, nextDayEndWork,
}) => {
  const row = templateData.value[0];
  row[date] = {
    startWorkTime,
    endWorkTime,
    typeId,
  };
  if (nextDayEndWork) {
    const nextDay = nextDayEndWork;
    const nextDayString = moment(nextDay).format('YYYY-MM-DD');
    const nextDayEnd = moment(nextDay).format('HH:mm');
    row[nextDayString] = {
      startWorkTime: '00:00',
      endWorkTime: nextDayEnd,
      typeId,
    };
  }
};

const getColumns = () => {
  const columnTemplate = [
    {
      field: 'button', key: 'button', title: '', align: 'center', width: 330, fixed: 'left',
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
            workDayStatuses: props.workDayStatuses,
            shiftsVariants: props.shiftsVariants,
            timeOptions: props.timeOptions,
            disabled: false,
            lunchDuration: props.departmentLunchDuration,
          },
          on: { changeWorkTime: changeTemplateTime },
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
onMounted(() => {
  getColumns();
});

const cellStyleOption = {
  bodyCellClass: ({ column }) => {
    const result = [];
    if (column.isWeekend) {
      result.push('table-body-weekend-cell');
    }
    result.push('table-body-cell');
    return result.join(' ');
  },
  headerCellClass: ({ column }) => {
    const result = [];
    if (column.isWeekend) {
      result.push('table-header-weekend-cell');
    }
    result.push('table-header-cell');
    return result.join(' ');
  },
};
</script>

<style scoped lang="scss">
.flex {
  display: flex;
}
</style>
