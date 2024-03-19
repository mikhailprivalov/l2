<template>
  <div>
    <div>
      <h4>Фильтры</h4>
      <Treeselect
        v-model="selectedMode"
        :options="modes"
      />
    </div>
    <div>
      <div class="flex-center">
        <div class="arrow-button-container">
          <button
            class="btn btn-blue-nb arrow-button"
            @click="getPrevDates"
          >
            <i class="fa fa-arrow-left" />
          </button>
          <button
            class="btn btn-blue-nb arrow-button"
            @click="getNextDates"
          >
            <i class="fa fa-arrow-right" />
          </button>
        </div>
      </div>
      <VeTable
        :columns="columns"
        :table-data="tableData"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  VeLocale,
  VeTable,
} from 'vue-easytable';
import 'vue-easytable/libs/theme-default/index.css';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import {
  onMounted, ref, watch,
} from 'vue';

import ruRu from '@/locales/ve';

VeLocale.use(ruRu);

const currentDate = ref(new Date());

const getMonthDays = () => {
  const days = [];
  const currentMonth = currentDate.value.getMonth();
  const date = new Date(currentDate.value.getFullYear(), currentMonth);
  while (date.getMonth() === currentMonth) {
    days.push(new Date(date));
    date.setDate(date.getDate() + 1);
  }
  return days;
};

const getMonthsYear = () => {
  const months = [];
  const currentYear = currentDate.value.getFullYear();
  const month = new Date(currentYear, 0);
  while (month.getFullYear() === currentYear) {
    months.push(new Date(month));
    month.setMonth(month.getMonth() + 1);
  }
  return months;
};

const modes = ref([
  { id: 0, label: 'По дням' },
  { id: 1, label: 'По месяцам' },
]);
const selectedMode = ref(0);

const tableData = ref([]);

const columns = ref([]);
const getColumns = () => {
  const columnsTemplate = [
    {
      key: 'office', field: 'office', title: 'Офисы', align: 'left', width: 200,
    },
  ];
  if (selectedMode.value === 1) {
    const monthsYear = getMonthsYear();
    const monthCols = monthsYear.map((col) => {
      const month = col.toLocaleDateString('ru-RU', { month: '2-digit', year: '2-digit' });
      return {
        key: month,
        field: month,
        title: month,
        align: 'center',
        width: 100,
      };
    });
    columnsTemplate.push(...monthCols);
  } else {
    const daysMonth = getMonthDays();
    const dateCols = daysMonth.map((col) => {
      const date = col.toLocaleDateString();
      return {
        key: date,
        field: date,
        title: date,
        align: 'center',
        width: 0,
      };
    });
    columnsTemplate.push(...dateCols);
  }
  columns.value = columnsTemplate;
};

const getNextDates = () => {
  if (selectedMode.value === 0) {
    currentDate.value = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() + 1, currentDate.value.getDate());
  } else {
    currentDate.value = new Date(currentDate.value.getFullYear() + 1, currentDate.value.getMonth(), currentDate.value.getDate());
  }
};
const getPrevDates = () => {
  if (selectedMode.value === 0) {
    currentDate.value = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() - 1, currentDate.value.getDate());
  } else {
    currentDate.value = new Date(currentDate.value.getFullYear() - 1, currentDate.value.getMonth(), currentDate.value.getDate());
  }
};

watch([selectedMode, currentDate], () => {
  getColumns();
});

onMounted(() => {
  getColumns();
});

</script>

<style scoped lang="scss">
.flex-center {
  display: flex;
  justify-content: center;
}
.arrow-button-container {
  display: flex;
  justify-content: space-between;
  margin: 5px 0;
  width: 150px;
}
.arrow-button {
  width: 60px;
}
</style>
