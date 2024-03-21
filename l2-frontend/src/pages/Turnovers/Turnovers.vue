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
import RadioField from '@/fields/RadioField.vue';

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

const modes = ref(['Подразделение', 'Люди']);
const modesEnglish = ref({
  Подразделение: 'department',
  Люди: 'person',
});
const selectedMode = ref('Подразделение');

const tableData = ref([]);

const columns = ref([]);

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
.radio-button {
  width: 300px;
  margin: 5px auto;
}
</style>
