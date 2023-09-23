<template>
  <div class="main">
    <div class="filters">
      <div class="four-col">
        <Treeselect
          :disable-branch-nodes="true"
          placeholder="Выберите исследование"
        />
      </div>
    </div>
    <div>
      <VeTable
        :columns="columns"
        :table-data="researches"
        row-key-field-name="researchId"
        :checkbox-option="checkboxOption"
      />
      <div
        v-show="researches.length === 0"
        class="empty-list"
      >
        Нет записей
      </div>
      <div>
        <VePagination
          :total="researches.length"
          :page-index="page"
          :page-size="pageSize"
          :page-size-option="pageSizeOption"
          @on-page-number-change="pageNumberChange"
          @on-page-size-change="pageSizeChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { VeLocale, VePagination, VeTable } from 'vue-easytable';
import 'vue-easytable/libs/theme-default/index.css';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import ruRu from '@/locales/ve';
// import * as actions from '@/store/action-types';
// import { useStore } from '@/store';

VeLocale.use(ruRu);

// const store = useStore();

VeLocale.use(ruRu);
const columns = ref([
  {
    field: 'checkbox', key: 'checkbox', title: '', type: 'checkbox', align: 'center', width: 50,
  },
  { field: 'eds', key: 'eds', title: 'ЭЦП' },
  { field: 'remd', key: 'remd', title: 'РЭМД' },
  { field: 'ECP', key: 'ECP', title: 'ЕЦП' },
  { field: 'link', key: 'link', title: 'L2' },
  { field: 'card', key: 'сard', title: 'Карта' },
  { field: 'patientFio', key: 'patientFio', title: 'ФИО' },
  { field: 'direction', key: 'direction', title: 'Напр.' },
  { field: 'researchTitle', key: 'researchTitle', title: 'Услуга' },
  { field: 'whoAssigned', key: 'whoAssigned', title: 'Врач' },
]);
const researches = ref([
  { eds: '' },
]);
const pageSize = ref(50);
const page = ref(1);
const pageSizeOption = ref([50, 100, 300, 500]);

// const enrolleesPagination = computed(() => props.enrollees.slice((page.value - 1) * pageSize.value, page.value
//   * pageSize.value));
const pageNumberChange = (number) => {
  page.value = number;
};
const pageSizeChange = (size) => {
  pageSize.value = size;
};

const checkboxOption = ref({
  selectedRowChange: ({ row, isSelected, selectedRowKeys }) => {
    console.log(row, isSelected, selectedRowKeys);
  },
  selectedAllChange: ({ isSelected, selectedRowKeys }) => {
    console.log(isSelected, selectedRowKeys);
  },
});
// const getInternalBase = async () => {
//   await store.dispatch(actions.DEC_LOADING);
//   const baseData = await api('/bases');
//   await store.dispatch(actions.DEC_LOADING);
//   basePk.value = baseData.bases[0].pk;
// };
</script>

<style scoped>
.main {
  width: 90%;
  margin: 10px auto;
  background-color: #ffffff;
}
.filters {
  margin: 10px;
}
.four-col {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-bottom: 5px;
}
.empty-list {
  width: 85px;
  margin: 10px auto;
}
</style>
