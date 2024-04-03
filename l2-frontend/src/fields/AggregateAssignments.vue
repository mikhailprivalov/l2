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
        :cell-style-option="cellStyleOption"
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
      :direction-id="currentDirectionPk"
      @hide="showSchedule = false"
      @slotFilled="slotFilled"
    />
  </div>
</template>

<script setup lang="ts">
import {
  computed, getCurrentInstance, onMounted, ref,
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

const root = getCurrentInstance().proxy.$root;
const store = useStore();

const showSchedule = ref(false);
const currentResearchPk = ref(null);
const currentDirectionPk = ref(null);

const openSchedule = (researchId, directionId) => {
  currentResearchPk.value = researchId;
  currentDirectionPk.value = directionId;
  showSchedule.value = true;
};

const pageSize = ref(30);
const page = ref(1);
const pageSizeOption = ref([30, 50, 100, 300]);
const pageNumberChange = (number: number) => {
  page.value = number;
};
const pageSizeChange = (size: number) => {
  pageSize.value = size;
};

const cellStyleOption = {
  bodyCellClass: ({ row }) => {
    if (row.scheduleDate) {
      return 'table-body-cell-green';
    }
    return '';
  },
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

const slotFilled = () => {
  getAssignments();
};

const cancelSlot = async (researchId, slotPlanId) => {
  await store.dispatch(actions.INC_LOADING);
  const { ok, message } = await api('/schedule/cancel', {
    cardId: props.cardPk,
    id: slotPlanId,
    serviceId: researchId,
  });
  await store.dispatch(actions.DEC_LOADING);
  if (ok) {
    root.$emit('msg', 'ok', 'Отменено');
    await getAssignments();
  } else {
    root.$emit('msg', 'error', message);
  }

  await store.dispatch(actions.DEC_LOADING);
};

const columns = ref([
  {
    field: 'directionId', key: 'directionId', title: '№ напр.', width: 100,
  },
  {
    field: 'researchTitle', key: 'researchTitle', title: 'Медицинское вмешательство', align: 'left',
  },
  {
    field: 'createDate', key: 'createDate', title: 'Дата назначения', align: 'center', width: 150,
  },
  {
    field: 'scheduleDate',
    key: 'scheduleDate',
    title: 'Расписание',
    align: 'center',
    width: 150,
    renderBodyCell: ({ row }, h) => {
      if (row.scheduleDate) {
        return h('div', {}, [
          h('p', {}, row.scheduleDate),
          h('button', {
            class: 'transparent-button transparent-button-small',
            on: {
              click: () => {
                cancelSlot(row.researchId[0], row.slotPlanId);
              },
            },
          }, 'Отменить запись'),
        ]);
      }
      return h('div', { class: 'button' }, [
        h('button', {
          class: 'transparent-button',
          on: {
            click: () => {
              openSchedule(row.researchId[0], row.directionId);
            },
          },
        }, 'Записать'),
      ]);
    },
  },
  {
    field: 'whoAssigned', key: 'whoAssigned', title: 'ФИО назначившего', align: 'center', width: 200,
  },
  {
    field: 'timeConfirmation',
    key: 'timeConfirmation',
    title: 'Дата и время подтверждения',
    align: 'center',
    width: 150,
    renderBodyCell: ({ row }) => {
      if (!row.timeConfirmation) {
        return 'Не исполнено';
      }
      return row.timeConfirmation;
    },
  },
  {
    field: 'whoConfirm', key: 'whoConfirm', title: 'ФИО подтвердившего', align: 'center', width: 200,
  },
]);

const printForm = () => {
  window.open(`/forms/pdf?type=107.03&&hosp_pk=${props.direction}`);
};

onMounted(getAssignments);

</script>

<style scoped lang="scss">
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

<style lang="scss">
.transparent-button {
  background-color: transparent;
  color: #434A54;
  border: none;
  border-radius: 4px;
  padding: 6px 12px;

  &:hover {
    background-color: #434a54;
    color: #FFF;
  }
  &:active {
    background-color: #37BC9B;
    color: #FFF;
  }
}
.transparent-button-small {
    padding: 0;
}
.table-body-cell-green {
  background: #a9cfbb !important;
}
</style>
