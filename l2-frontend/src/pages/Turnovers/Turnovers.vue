<template>
  <div>
    <div>
      <RadioField
        v-model="selectedMode"
        :variants="modes"
        class="radio-button"
      />
    </div>
    <div>
      <div class="flex-center">
        <div class="arrow-button-container">
          <button
            class="btn btn-blue-nb arrow-button"
            @click="setPrevMonth"
          >
            <i class="fa fa-arrow-left" />
          </button>
          <div class="date">{{ currentDate.toLocaleDateString('ru-RU', { month: "long", year: "numeric" }) }}</div>
          <button
            class="btn btn-blue-nb arrow-button"
            @click="setNextMonth"
          >
            <i class="fa fa-arrow-right" />
          </button>
        </div>
      </div>
      <VeTable
        id="table"
        :columns="columns"
        :table-data="tableData"
        :scroll-width="0"
        :border-y="true"
        :cell-style-option="cellStyleOption"
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
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import {
  onMounted,
  ref, watch,
} from 'vue';
import moment from 'moment';

import ruRu from '@/locales/ve';
import RadioField from '@/fields/RadioField.vue';
import * as actions from '@/store/action-types';
import api from '@/api';
import { useStore } from '@/store';

VeLocale.use(ruRu);

const store = useStore();

const currentDate = ref(new Date());

const modes = ref(['Подразделение', 'Люди']);
const modesEnglish = ref({
  Подразделение: 'department',
  Люди: 'person',
});
const selectedMode = ref('Подразделение');

const tableData = ref([]);

const columns = ref([]);

const cellStyleOption = {
  bodyCellClass: ({ row, column }) => {
    if (row.only1stCol && column.field === 'office') {
      return 'table-body-cell-class-type-cash';
    }
    if (row.totalRow) {
      return 'table-body-cell-class-total';
    }
    if (row.officeRow) {
      return 'table-body-cell-class-office';
    }
    return 'table-body-cell-class';
  },
};

const getTurnoversData = async () => {
  const dateString = moment(currentDate.value).format('YYYYMMDD');
  await store.dispatch(actions.INC_LOADING);
  const result = await api('dashboards/cash-register', {
    dateStart: dateString,
    mode: modesEnglish.value[selectedMode.value],
  });
  await store.dispatch(actions.DEC_LOADING);
  columns.value = result.columns;
  tableData.value = result.tableData;
};

const setPrevMonth = () => {
  currentDate.value = new Date(currentDate.value.setMonth(currentDate.value.getMonth() - 1));
};

const setNextMonth = () => {
  currentDate.value = new Date(currentDate.value.setMonth(currentDate.value.getMonth() + 1));
};

watch([selectedMode, currentDate], () => {
  getTurnoversData();
});

onMounted(() => {
  getTurnoversData();
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
  width: 235px;
}
.arrow-button {
  width: 60px;
}
.radio-button {
  width: 300px;
  margin: 5px auto;
}
.date {
  padding: 6px 0;
}
</style>

<style lang="scss">
.table-body-cell-class {
  padding: 0 0 0 10px !important;
}
.table-body-cell-class-office {
  background-color: #6d9eea !important;
  padding: 0 0 0 10px !important;
}
.table-body-cell-class-type-cash {
  background-color: #e9d1de !important;
  padding: 0 0 0 10px !important;
}
.table-body-cell-class-total {
  background-color: #41c0c6 !important;
  padding: 0 0 0 10px !important;
}

#table tbody :first-child {
  height: 0 !important;
}
#table tr {
  height: 10px !important;
}
</style>
