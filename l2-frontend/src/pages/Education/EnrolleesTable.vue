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
  computed, defineProps, onMounted, ref, useCssModule,
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
const $style = useCssModule();
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
  window.open(`/ui/directions?card_pk=${cardPk}&base_pk=${basePk.value}`);
};
const openInfo = (cardPk, fio) => {
  showInfoModal.value = true;
  selectedCardPk.value = cardPk;
  selectedFio.value = fio;
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
        } : { class: 'fa fa-square-o', 'aria-hidden': true }),
      };
    } if (cell.key === 'researchContractId') {
      return {
        key: 'researchContractId',
        fields: 'researchContractId',
        title: 'Договор',
        renderBodyCell: ({ row }, h) => (row.researchContractId ? h('button', {
          class: $style.transparentButton,
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
        title: 'Статус',
        align: 'center',
        renderBodyCell: ({ row }, h) => {
          if (row.isExpelled) { return h('p', { class: $style.expelledText }, 'Отчислен'); }
          if (row.isEnrolled) { return h('p', { class: $style.enrolledText }, 'Зачислен'); }
          return '';
        },
      };
    }
    return cell;
  });
  columns.value.push({
    field: 'actions',
    key: 'actions',
    title: 'Действия',
    renderBodyCell: ({ row }, h) => (
      h('div', { class: $style.action }, [
        h(
          'button',
          { class: $style.transparentButton, on: { click: () => { openCard(row.card); } } },
          [h('i', { class: 'fa-solid fa-user-graduate', 'aria-hidden': true })],
        ),
        h(
          'button',
          { class: $style.transparentButton, on: { click: () => { openInfo(row.card, row.fio); } } },
          [h('i', { class: 'fa fa-info-circle', 'aria-hidden': true })],
        ),
      ])
    ),
  });
};
onMounted(() => {
  getInternalBase();
  getColumns();
});
</script>

<style module lang="scss">
.emptyList {
  width: 85px;
  margin: 20px auto;
}
.transparentButton {
  background-color: transparent;
  color: #434A54;
  border: none;
  border-radius: 4px;
  padding: 6px 12px;
}
.transparentButton:hover {
  background-color: #434a54;
  color: #FFFFFF;
  border: none;
}
.transparentButton:active {
  background-color: #37BC9B;
  color: #FFFFFF;
}
.expelledText {
  color: red;
  margin: auto 0;
}
.enrolledText {
  color: #37BC9B;
  margin: auto 0;
}
.action {
  display: flex;
  justify-content: space-evenly;
}
</style>
