<template>
  <div>
    <div>
      <VeTable
        :columns="columns"
        :table-data="assignments"
      />
      <div
        v-show="assignments.length === 0"
        class="empty-list"
      >
        Нет записей
      </div>
      <div class="flex-space-between">
        <VePagination
          :total="assignments.length"
          :page-index="page"
          :page-size="pageSize"
          :page-size-option="pageSizeOption"
          @on-page-number-change="pageNumberChange"
          @on-page-size-change="pageSizeChange"
        />
        <div class="print-div">
          <div class="button">
            <button
              v-tippy
              title="печать"
              class="btn last btn-blue-nb nbr"
            >
              печать
            </button>
          </div>
        </div>
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

const props = defineProps<{
  direction: number;
}>();

const columns = ref([
  {
    field: 'research', key: 'research', title: 'Медицинское вмешательство', align: 'center',
  },
  {
    field: 'assignedDate', key: 'dateAssigned', title: 'Дата назначения', align: 'center', width: 100,
  },
  {
    field: 'signatureCreator', key: 'signatureCreator', title: 'Подпись назначившего', align: 'center', width: 100,
  },
  {
    field: 'confirmationDate', key: 'confirmationDate', title: 'Дата подтверждения', align: 'center', width: 100,
  },
  {
    field: 'fioConfirmant', key: 'fioConfirmant', title: 'Фамилия подтвердившего', align: 'center', width: 200,
  },
]);
const store = useStore();
const pageSize = ref(100);
const page = ref(1);
const pageSizeOption = ref([30, 50, 100, 300]);
const pageNumberChange = (number: number) => {
  page.value = number;
};
const pageSizeChange = (size: number) => {
  pageSize.value = size;
};

const getAssignments = async () => {
  await store.dispatch(actions.INC_LOADING);
  const data = api('stationar/get-assignments', { history_id: props.direction });
  await store.dispatch(actions.DEC_LOADING);
};

const assignments = ref([]);
onMounted(getAssignments);

</script>

<style scoped>
.empty-list {
  width: 85px;
  margin: 20px auto;
}
.flex-space-between {
  display: flex;
  justify-content: space-between;
}
.print-div {
  width: 100px;
}
.button {
  width: 100%;
  display: flex;
  flex-wrap: nowrap;
  flex-direction: row;
  justify-content: stretch;
}
.btn {
  align-self: stretch;
  flex: 1;
  padding: 7px 0;
}
</style>
