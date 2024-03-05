<template>
  <div>
    <div class="print-div">
      <div class="button">
        <button
          v-tippy
          title="Печать"
          class="btn last btn-blue-nb"
          @click="printForm"
        >
          Печать
        </button>
      </div>
    </div>
    <div>
      <VeTable
        :columns="columns"
        :table-data="assignmentPagination"
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
      </div>
    </div>
    <ScheduleModal
      v-if="showSchedule"
      :card-pk="props.cardPk"
      :service-number="currentResearchPk"
      @hide="showSchedule = false"
    />
  </div>
</template>

<script setup lang="ts">
import {
  computed, onMounted, ref,
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
import ScheduleModal from '@/modals/ScheduleModal.vue';

VeLocale.use(ruRu);

const props = defineProps({
  direction: {
    type: Number,
    required: true,
  },
  cardPk: {
    type: Number,
    required: true,
  },
});

const showSchedule = ref(false);
const currentResearchPk = ref(-1);
const openSchedule = (researchIds) => {
  const data = researchIds[0];
  console.log(data);
  currentResearchPk.value = data;
  showSchedule.value = true;
};

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
    field: 'schedule_date',
    key: 'schedule_date',
    title: 'Расписание',
    align: 'center',
    width: 100,
    renderBodyCell: ({ row }, h) => {
      if (row.schedule_date) {
        const date = new Date(row.schedule_date);
        const stringDate = date.toLocaleString('ru-RU', {
          day: '2-digit',
          month: '2-digit',
          weekday: 'short',
          hour: '2-digit',
          minute: '2-digit',
        });
        const list = stringDate.split(', ');
        return `${list[1]} ${list[0]} ${list[2]}`;
      }
      return h('div', { class: 'button' }, [
        h('button', {
          class: 'transparent-button',
          on: {
            click: () => {
              openSchedule(row.research_id);
            },
          },
        }, 'Записать'),
      ]);
    },
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
const assignments = ref([]);

const getAssignments = async () => {
  await store.dispatch(actions.INC_LOADING);
  const results = await api('stationar/get-assignments', { direction_id: props.direction });
  await store.dispatch(actions.DEC_LOADING);
  assignments.value = results.data;
};

const assignmentPagination = computed(() => assignments.value.slice(
  (page.value - 1) * pageSize.value,
  page.value * pageSize.value,
));

const printForm = () => {
  window.open(`/forms/pdf?type=107.03&&hosp_pk=${props.direction}`);
};

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
  width: 75px;
  margin-bottom: 5px;
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
  padding: 6px 0;
}
</style>

<style>
.transparent-button {
  background-color: transparent;
  color: #434A54;
  border: none;
  border-radius: 4px;
  padding: 6px 12px;
}
.transparent-button:hover {
  background-color: #434a54;
  color: #FFFFFF;
  border: none;
}
.transparent-button:active {
  background-color: #37BC9B;
  color: #FFFFFF;
}
</style>
