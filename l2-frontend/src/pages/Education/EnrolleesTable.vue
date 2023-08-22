<template>
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
</template>

<script>
import {
  VeLocale,
  VePagination,
  VeTable,
} from 'vue-easytable';
import 'vue-easytable/libs/theme-default/index.css';

import ruRu from '@/locales/ve';

VeLocale.use(ruRu);
export default {
  name: 'EnrolleesTable',
  components: { VeTable, VePagination },
  props: ['enrollees'],
  data() {
    return {
      columns: [
        { field: 'card', key: 'card', title: 'Дело' },
        { field: 'fio', key: 'fio', title: 'ФИО' },
        { field: 'application', key: 'application', title: 'Заявление' },
        { field: 'сhemistry', key: 'сhemistry', title: 'Хим.' },
        { field: 'biology', key: 'biology', title: 'Био.' },
        { field: 'mathematics', key: 'mathematics', title: 'Мат.' },
        { field: 'russian_language', key: 'russian_language', title: 'Рус.' },
        { field: 'ia', key: 'ia', title: 'ИД' },
        { field: 'iaPlus', key: 'ia+', title: 'ИД+' },
        { field: 'amount', key: 'amount', title: 'Сумм' },
        {
          field: 'is_original',
          key: 'is_original',
          title: 'Оригинал',
          renderBodyCell: ({ row, column }) => {
            const text = row[column.field];
            return text ? <span style="font-size: 18px;">&#9745;</span> : <span style="font-size: 25px;">&#9633;</span>;
          },
        },
        { field: 'status', key: 'status', title: 'Статус' },
        { field: 'create_date', key: 'create_date', title: 'Создано' },
        {
          field: 'actions',
          key: 'actions',
          title: 'Действия',
          width: 100,
          renderBodyCell: ({ row }) => (
            <div style="display: flex; justify-content: space-evenly">
              <button
                class="btn btn-blue-nb button-icon"
                title="Карта"
                v-tippy
                on-click={() => this.openCard(row.card)}
              >
                <i
                  class="fa-solid fa-user-graduate"
                  aria-hidden="true"
                />
              </button>
              <button
                v-tippy
                title="Информация"
                class="btn btn-blue-nb button-icon"
              >
                <i
                  class="fa fa-info-circle"
                  aria-hidden="true"
                />
              </button>
            </div>),
        },
      ],
      pageSize: 30,
      page: 1,
      pageSizeOption: [30, 50, 100, 300],
      basePk: -1,
    };
  },
  mounted() {
    this.getInternalBase();
  },
  methods: {
    pageNumberChange(number) {
      this.page = number;
    },
    pageSizeChange(size) {
      this.pageSize = size;
    },
    async getInternalBase() {
      const baseData = await this.$api('/bases');
      this.basePk = baseData.bases[0].pk;
    },
    openCard(cardPk) {
      window.open(`/ui/directions?card_pk=${cardPk}&base_pk=${this.basePk}`);
    },
  },
};
</script>

<style scoped>
.empty-list {
  width: 85px;
  margin: 20px auto;
}
.button-icon {
  background-color: transparent !important;
  color: grey;
  border: none !important;
  font-size: 12px;
}
.button-icon:hover {
  background-color: #434a54 !important;
  color: #FFFFFF
}
.button-icon:active {
  background-color: #37BC9B !important;
}
</style>
