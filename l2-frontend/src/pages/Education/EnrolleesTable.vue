<template>
  <div>
    <VeTable
      :columns="columns"
      :table-data="enrolleesPagination"
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
    <EnrolleesApplication
      v-if="showInfoModal"
      :card_pk="selectedCardPk"
      :fio="selectedFio"
      @hideEnrollees="showInfoModal = false"
    />
  </div>
</template>

<script setup lang="ts">
import {
  computed, defineProps, onMounted, ref,
} from 'vue';
import { VeLocale, VePagination, VeTable } from 'vue-easytable';
import 'vue-easytable/libs/theme-default/index.css';

import ruRu from '@/locales/ve';
import EnrolleesApplication from '@/modals/EnrolleesApplication.vue';
import api from '@/api';

VeLocale.use(ruRu);
const props = defineProps({
  enrollees: {
    type: Array,
    required: true,
  },
});
const columns = ref([]);
const showInfoModal = ref(false);
const selectedCardPk = ref(-1);
const selectedFio = ref('');
const pageSize = ref(50);
const page = ref(1);
const pageSizeOption = ref([50, 100, 300, 500]);
const basePk = ref(-1);
const enrolleesPagination = computed(() => props.enrollees.slice((page.value - 1) * pageSize.value, page.value
  * pageSize.value));
const pageNumberChange = (number) => {
  page.value = number;
};
const pageSizeChange = (size) => {
  pageSize.value = size;
};
const getInternalBase = async () => {
  const baseData = await api('/bases');
  basePk.value = baseData.bases[0].pk;
};
const openCard = (cardPk) => {
  window.open(`/ui/directions?card_pk=${cardPk}&base_pk=${this.basePk}`);
};
const openInfo = (cardPk, fio) => {
  this.showInfoModal = true;
  this.selectedCardPk = cardPk;
  this.selectedFio = fio;
};
const openContract = (contractPk) => {
  window.open(`/ui/results/descriptive#{"pk":${contractPk}}`);
};
const getColumns = async () => {
  const data = await api('/education/get-columns');
  const { result } = data;
  columns.value = result.map((cell) => {
    if (cell.key === 'isOriginal') {
      return {
        key: 'isOriginal',
        fields: 'isOriginal',
        title: 'Оригинал',
        renderBodyCell: ({ row }, h) => h('i', row.isOriginal ? {
          class: 'fa fa-check-square',
          'aria-hidden': 'true',
          style: 'color: #37BC9B;',
        } : { class: 'fa fa-square-o', 'aria-hidden': 'true' }),
      };
    } if (cell.key === 'researchContractId') {
      return {
        key: 'researchContractId',
        fields: 'researchContractId',
        title: 'Договор',
        renderBodyCell: ({ row }, h) => (row.researchContractId ? h('button', {
          class: 'btn btn-blue-nb transparent-button',
          title: 'Договор',
          on: {
            click: () => {
              openContract(row.researchContractId);
            },
          },
        }, [h('i', { class: 'fa-solid fa-folder' })]) : ''),
      };
    } if (cell.key === 'status') {
      return {
        key: 'status',
        fields: 'status',
        title: 'Статус1',
        align: 'center',
        renderBodyCell: '',
      };
    }
    return cell;
  });
  columns.value.push({
    field: 'actions',
    key: 'actions',
    title: 'Действия',
    width: 100,
    renderBodyCell: '',
  });
};
onMounted(() => {
  getInternalBase();
  getColumns();
});
// const async getColumns() {
//    const data = await this.$api('/education/get-columns');
//    const { result } = data;
//    result[result.length - 4].renderBodyCell = ({ row, column }) => {
//      const text = row[column.field];
//      return text ? <i class="fa fa-check-square" aria-hidden="true" style="color: #37BC9B;" />
//        : <i class="fa fa-square-o" aria-hidden="true" />;
//    };
//    result[result.length - 3].renderBodyCell = ({ row, column }) => {
//      const contract = row[column.field];
//      return contract ? <button
//        class="btn btn-blue-nb button-icon"
//        title="Договор"
//        v-tippy
//        on-click={() => this.openContract(contract)}
//      >
//        <i
//          class="fa-solid fa-folder"
//        />
//      </button> : '';
//    };
//    result[result.length - 2].renderBodyCell = ({ row }) => {
//      const enrolled = row.is_enrolled;
//      const expelled = row.is_expelled;
//      if (expelled) { return <p style="color: red">Отчислен</p>; }
//      if (enrolled) { return <p style="color: #37BC9B;">Зачислен</p>; }
//      return '';
//    };
//    result.push({
//      field: 'actions',
//      key: 'actions',
//      title: 'Действия',
//      width: 100,
//      renderBodyCell: ({ row }) => (
//          <div style="display: flex; justify-content: space-evenly">
//            <button
//              class="btn btn-blue-nb button-icon"
//              title="Карта"
//              v-tippy
//              on-click={() => this.openCard(row.card)}
//            >
//              <i
//                class="fa-solid fa-user-graduate"
//                aria-hidden="true"
//              />
//            </button>
//            <button
//              v-tippy
//              title="Информация"
//              class="btn btn-blue-nb button-icon"
//              on-click={() => this.openInfo(row.card, row.fio)}
//            >
//              <i
//                class="fa fa-info-circle"
//                aria-hidden="true"
//              />
//            </button>
//          </div>),
//    });
//    this.columns = result;
//  },
</script>

<style lang="scss">
.empty-list {
  width: 85px;
  margin: 20px auto;
}
.transparent-button1 {
  background-color: transparent !important;
  color: #434A54;
  border: none !important;
}
.transparent-button1:hover {
  background-color: #434a54 !important;
  color: #FFFFFF
}
.transparent-button1:active {
  background-color: #37BC9B !important;
}
</style>
