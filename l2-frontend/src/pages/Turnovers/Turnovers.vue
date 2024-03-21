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
          <button
            class="btn btn-blue-nb arrow-button"
            @click="setNextMonth"
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
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import {
  onMounted,
  ref, watch,
} from 'vue';

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

const getTurnoversData = async () => {
  console.log('Текущая дата', currentDate.value);
  console.log('Текущий мод', modesEnglish.value[selectedMode.value]);
  // await store.dispatch(actions.INC_LOADING);
  // const result = await api('stationar/get-assignments', {
  //   currentDate: currentDate.value,
  //   mode: modesEnglish.value[selectedMode.value],
  // });
  // await store.dispatch(actions.DEC_LOADING);
  // columns.value = result.columns;
  // tableData.value = result.data;
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
