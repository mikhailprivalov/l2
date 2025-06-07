<template>
  <VeTable
    :columns="columns"
    :table-data="templateData"
    :cell-style-option="cellStyleOption"
    :border-y="true"
    :scroll-width="0"
    :show-header="false"
    :row-style-option="rowStyleOption"
  />
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { VeTable } from 'vue-easytable';
import 'vue-easytable/libs/theme-default/index.css';
import moment from 'moment/moment';

import DateCell from '@/pages/WorkingTime/DateCell.vue';
import FillingCell from '@/pages/WorkingTime/FillingCell.vue';

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

const emit = defineEmits(['fillInTemplate']);
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

const copyPrevFilledCell = ({ date }) => {
  const currentDay = new Date(date);
  const currentTemplateData = templateData.value[0];
  const sortedKeys = Object.keys(currentTemplateData)
    .filter(key => new Date(key) < currentDay)
    .sort((a, b) => new Date(b) - new Date(a));
  for (const key of sortedKeys) {
    const keyData = currentTemplateData[key];
    const keyValues = Object.values(keyData).filter(value => value);
    if (keyValues.length > 0) {
      currentTemplateData[date] = { ...keyData };
      break;
    }
  }
};

const fillInTemplate = () => {
  emit('fillInTemplate', { templateData: templateData.value[0] });
};

const clearTemplate = () => {
  createTemplateData();
};

const getColumns = () => {
  const columnTemplate = [
    {
      field: 'button',
      key: 'button',
      title: '',
      align: 'center',
      width: 345,
      fixed: 'left',
      renderBodyCell: ({ row, column }, h) => h(
        FillingCell,
        {
          props: {
            workTime: row[column.field] ? row[column.field] : '',
          },
          on: { fill: fillInTemplate, clear: clearTemplate },
        },
      ),
    },
  ];
  const daysMonth = [...monthDays.value];
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
            dateTitle,
            workDayStatuses: props.workDayStatuses,
            shiftsVariants: props.shiftsVariants,
            timeOptions: props.timeOptions,
            disabled: false,
            lunchDuration: props.departmentLunchDuration,
            showAdditionalButtons: true,
          },
          on: { changeWorkTime: changeTemplateTime, copyPrevFilled: copyPrevFilledCell },
        },
      ),
    };
  });
  columnTemplate.push(...data);
  const endTable = {
    field: 'total', key: 'total', title: '', align: 'center', width: 72, fixed: 'right',
  };
  columnTemplate.push(endTable);
  columns.value = columnTemplate;
};

watch(() => [props.year, props.month], () => {
  if (props.year && props.month) {
    monthDays.value = getMonthDays(props.year, props.month);
    getColumns();
    createTemplateData();
  }
}, { immediate: true });

const cellStyleOption = ref({
  bodyCellClass: ({ column }) => {
    const result = [];
    if (column.isWeekend) {
      result.push('template-table-body-weekend-cell');
    }
    result.push('template-table-body-cell');
    return result.join(' ');
  },
});
const rowStyleOption = ref({
  hoverHighlight: false,
  clickHighlight: false,
  stripe: false,
});
</script>

<style scoped lang="scss">
.flex {
  display: flex;
}
</style>
