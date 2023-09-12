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

<script>
import {
  VeLocale,
  VePagination,
  VeTable,
} from 'vue-easytable';
import 'vue-easytable/libs/theme-default/index.css';

import ruRu from '@/locales/ve';
import EnrolleesApplication from '@/modals/EnrolleesApplication.vue';

VeLocale.use(ruRu);
export default {
  name: 'EnrolleesTable',
  components: { EnrolleesApplication, VeTable, VePagination },
  props: ['enrollees'],
  data() {
    return {
      columns: [],
      showInfoModal: false,
      selectedCardPk: -1,
      selectedFio: '',
      pageSize: 100,
      page: 1,
      pageSizeOption: [100, 300, 500],
      basePk: -1,
    };
  },
  computed: {
    enrolleesPagination() {
      const { page, pageSize } = this;
      return this.enrollees.slice((page - 1) * pageSize, page * pageSize);
    },
  },
  mounted() {
    this.getInternalBase();
    this.getColumns();
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
    async getColumns() {
      const data = await this.$api('/education/get-columns');
      const { result } = data;
      result[result.length - 4].renderBodyCell = ({ row, column }) => {
        const text = row[column.field];
        return text ? <i class="fa fa-check-square" aria-hidden="true" style="color: #37BC9B;" />
          : <i class="fa fa-square-o" aria-hidden="true" />;
      };
      result[result.length - 3].renderBodyCell = ({ row, column }) => {
        const contract = row[column.field];
        return contract ? <button
          class="btn btn-blue-nb button-icon"
          title="Договор"
          v-tippy
          on-click={() => this.openContract(contract)}
        >
          <i
            class="fa-solid fa-folder"
          />
        </button> : '';
      };
      result[result.length - 2].renderBodyCell = ({ row }) => {
        const enrolled = row.is_enrolled;
        const expelled = row.is_expelled;
        if (expelled) { return <p style="color: red">Отчислен</p>; }
        if (enrolled) { return <p style="color: #37BC9B;">Зачислен</p>; }
        return '';
      };
      result.push({
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
                on-click={() => this.openInfo(row.card, row.fio)}
              >
                <i
                  class="fa fa-info-circle"
                  aria-hidden="true"
                />
              </button>
            </div>),
      });
      this.columns = result;
    },
    openCard(cardPk) {
      window.open(`/ui/directions?card_pk=${cardPk}&base_pk=${this.basePk}`);
    },
    openInfo(cardPk, fio) {
      this.showInfoModal = true;
      this.selectedCardPk = cardPk;
      this.selectedFio = fio;
    },
    openContract(contractPk) {
      window.open(`/ui/results/descriptive#{"pk":${contractPk}}`);
    },
  },
};
</script>

<style scoped lang="scss">
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
