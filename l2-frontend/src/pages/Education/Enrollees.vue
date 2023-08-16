<template>
  <div class="main">
    <h4 class="text-center">
      Абитуриенты
    </h4>
    <div>
      <VeTable
        :columns="columns"
        :table-data="enrollees"
      />
      <div
        v-show="enrollees.length === 0"
        class="empty-list"
      >
        Нет записей
      </div>
      <div class="flex-space-between">
        <VePagination
          :total="enrollees.length"
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
import {
  onMounted, ref,
} from 'vue';
import {
  VeLocale,
  VePagination,
  VeTable,
} from 'vue-easytable';

import 'vue-easytable/libs/theme-default/index.css';
import * as actions from '@/store/action-types';
import api from '@/api';
import { useStore } from '@/store';
import ruRu from '@/locales/ve';

VeLocale.use(ruRu);

const columns = ref([
  {
    field: 'direction_id', key: 'direction_id', title: '№ напр.', width: 100,
  },
  {
    field: 'research_title', key: 'research_title', title: 'Медицинское вмешательство', align: 'left',
  },
  {
    field: 'create_date', key: 'create_date', title: 'Дата назначения', align: 'center', width: 150,
  },
  {
    field: 'who_assigned', key: 'who_assigned', title: 'ФИО назначившего', align: 'center', width: 200,
  },
  {
    field: 'time_confirmation', key: 'time_confirmation', title: 'Дата и время подтверждения', align: 'center', width: 150,
  },
  {
    field: 'who_confirm', key: 'who_confirm', title: 'ФИО подтвердившего', align: 'center', width: 200,
  },
]);

const getColumns = () => {
  await this.$store.dispatch(actions.INC_LOADING);
  const columns = await this.$api('education/get-columns');
  this.link_rows = resultData.rows;
  await this.$store.dispatch(actions.DEC_LOADING);
};

onMounted(getColumns);

const store = useStore();
const pageSize = ref(30);
const page = ref(1);
const pageSizeOption = ref([30, 50, 100, 300]);
const pageNumberChange = (number: number) => {
  page.value = number;
};
const pageSizeChange = (size: number) => {
  pageSize.value = size;
};
const enrollees = ref([]);

</script>

<style scoped>
.main {
  width: 90%;
  background-color: #ffffff;
  margin: 10px auto;
}
.empty-list {
  width: 85px;
  margin: 20px auto;
}
</style>
