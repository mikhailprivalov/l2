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
import { PropType, ref, watch } from 'vue';
import { VeTable } from 'vue-easytable';
import 'vue-easytable/libs/theme-default/index.css';
import moment from 'moment/moment';

import DateCell from '@/pages/WorkingTime/DateCell.vue';
import FillingCell from '@/pages/WorkingTime/FillingCell.vue';
import {
  EMPTY_WORK_TIME_DAY_CELL,
  HolidaysMap, ShiftVariantItem, TableColumn, TimeOptionItem, WorkDayStatusItem,
} from '@/pages/WorkingTime/types/types';
import { formatDateKey, formatDateTitle } from '@/pages/WorkingTime/utils/date';

const props = defineProps({
  workDayStatuses: {
    type: Array as PropType<WorkDayStatusItem[]>,
    required: true,
  },
  shiftsVariants: {
    type: Array as PropType<ShiftVariantItem[]>,
    required: true,
  },
  timeOptions: {
    type: Array as PropType<TimeOptionItem[]>,
    required: true,
  },
  departmentLunchDuration: {
    type: Number,
    required: true,
  },
  holidays: {
    type: Object as PropType<HolidaysMap>,
    required: true,
  },
  refreshKey: {
    type: Number,
    required: true,
  },
  monthDays: {
    type: Array as PropType<Date[]>,
    required: true,
  },
});

const emit = defineEmits(['fillInTemplate', 'fillByEmployeeTemplate', 'fillColumnByTemplate']);
const columns = ref<TableColumn[]>([]);

const templateData = ref([]);
const createTemplateData = () => {
  const result = {};
  for (const col of props.monthDays) {
    const dateString = formatDateKey(col);
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
    const nextDayString = formatDateKey(nextDay);
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
    .sort((a, b) => new Date(b).getTime() - new Date(a).getTime());
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

const fillByEmployeeTemplate = ({ action }) => {
  emit('fillByEmployeeTemplate', { action });
};

const fillColumnByTemplate = ({
  date, startWork, endWork, typeId,
}) => {
  emit('fillColumnByTemplate', {
    date, startWork, endWork, typeId,
  });
};

const getColumns = () => {
  const columnTemplate: TableColumn[] = [
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
          on: { fill: fillInTemplate, clear: clearTemplate, fillByEmployeesTemplate: fillByEmployeeTemplate },
        },
      ),
    },
  ];
  const daysMonth = [...props.monthDays];
  const data: TableColumn[] = daysMonth.map((col) => {
    const dateString = formatDateKey(col);
    const dateTitle = formatDateTitle(col);
    const weekend = [6, 0].includes(col.getDay());
    const holiday = props.holidays[dateString]?.kind === 'HOLIDAY';
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
            dateTitle,
            workDayStatuses: props.workDayStatuses,
            shiftsVariants: props.shiftsVariants,
            timeOptions: props.timeOptions,
            disabled: false,
            lunchDuration: props.departmentLunchDuration,
            showAdditionalButtons: true,
          },
          on: { changeWorkTime: changeTemplateTime, copyPrevFilled: copyPrevFilledCell, copyToColumn: fillColumnByTemplate },
        },
      ),
    };
  });
  columnTemplate.push(...data);
  const endTable: TableColumn = {
    field: 'total', key: 'total', title: '', align: 'center', width: 72, fixed: 'right',
  };
  columnTemplate.push(endTable);
  columns.value = columnTemplate;
};

watch(() => [props.refreshKey], () => {
  getColumns();
  createTemplateData();
}, { immediate: true });

const cellStyleOption = ref({
  bodyCellClass: ({ column }) => {
    const result = [];
    if (column.isHoliday) {
      result.push('template-table-body-holiday-cell');
    } else if (column.isWeekend) {
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
