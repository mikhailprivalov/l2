<template>
  <div class="main">
    <div class="box card-1 card-no-hover">
      <h5 class="text-center">
        Компании
      </h5>
      <input
        v-model="search"
        class="form-control"
        style="margin-bottom: 20px"
        placeholder="Фильтр по названию..."
      >
      <div class="scroll">
        <table class="table table-bordered">
          <colgroup>
            <col>
            <col width="40">
          </colgroup>
          <tr
            v-if="filteredCompany.length === 0"
            class="text-center"
          >
            <td
              class="title"
              colspan="2"
            >
              Нет данных
            </td>
          </tr>
          <tr
            v-for="(company) in filteredCompany"
            :key="company.id"
          >
            <VueTippyTd
              class="title border"
              :text="company.title"
            />
            <td class="border">
              <button
                v-tippy
                title="Редактировать"
                class="btn last btn-blue-nb nbr"
                @click="editCompany(company)"
              >
                <i class="fa fa-pencil" />
              </button>
            </td>
          </tr>
        </table>
      </div>
    </div>
    <div class="box card-1 card-no-hover">
      <h5 class="text-center">
        {{ editCompanyId === -1 ? 'Добавление компании' : 'Редактирование компании' }}
      </h5>
      <div>
        <label>Наименование организации</label>
        <input
          v-model="editCompanyTitle"
          placeholder="Введите наименование организации"
          class="form-control"
        >
        <label>Сокращенное наименование</label>
        <input
          v-model="editCompanyShortTitle"
          placeholder="Введите сокращенное наименование"
          class="form-control"
        >
        <label>Юридический адрес</label>
        <input
          v-model="editCompanyLegalAddress"
          placeholder="Введите адрес"
          class="form-control"
        >
        <label>Фактический адрес</label>
        <input
          v-model="editCompanyFactAddress"
          placeholder="Введите адрес"
          class="form-control"
        >
        <label>ИНН</label>
        <input
          v-model="editCompanyInn"
          maxlength="12"
          placeholder="Введите ИНН"
          class="form-control"
          @input="getOnlyNumber($event, 'editCompanyInn')"
        >
        <label>ОГРН</label>
        <input
          v-model="editCompanyOgrn"
          maxlength="13"
          placeholder="Введите ОГРН"
          class="form-control"
          @input="getOnlyNumber($event, 'editCompanyOgrn')"
        >
        <label>КПП</label>
        <input
          v-model="editCompanyKpp"
          maxlength="9"
          placeholder="Введите КПП"
          class="form-control"
          @input="getOnlyNumber($event, 'editCompanyKpp')"
        >
        <label>БИК</label>
        <input
          v-model="editCompanyBik"
          maxlength="9"
          placeholder="Введите БИК"
          class="form-control"
          @input="getOnlyNumber($event, 'editCompanyBik')"
        >
        <label>Договор</label>
        <Treeselect
          v-model="editCompanyContractId"
          :options="contractList.data"
          :clearable="false"
          style="margin-bottom: 10px"
        />
        <div style="text-align: right">
          <button
            v-tippy
            title="Очистить"
            class="btn btn-blue-nb nbr"
            @click="clearEditCompany"
          >
            Очистить
          </button>
          <button
            v-tippy
            title="Сохранить"
            class="btn btn-blue-nb nbr"
            style="float: right"
            @click="updateCompany"
          >
            Сохранить
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import Treeselect from '@riophae/vue-treeselect';

import VueTippyTd from '@/construct/VueTippyTd.vue';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import * as actions from '@/store/action-types';

export default {
  name: 'ConstructCompany',
  components: { VueTippyTd, Treeselect },
  data() {
    return {
      companyList: {},
      dataCompanyList: [],
      contractList: {},
      search: '',
      currentCompany: {},
      dataCurrentCompany: {},
      editCompanyId: -1,
      editCompanyTitle: '',
      editCompanyShortTitle: '',
      editCompanyLegalAddress: '',
      editCompanyFactAddress: '',
      editCompanyInn: '',
      editCompanyOgrn: '',
      editCompanyKpp: '',
      editCompanyBik: '',
      editCompanyContractId: -1,
    };
  },
  computed: {
    filteredCompany() {
      return this.dataCompanyList.filter(company => {
        const companyTitle = company.title.toLowerCase();
        const searchTerm = this.search.toLowerCase();

        return companyTitle.includes(searchTerm);
      });
    },
  },
  mounted() {
    this.getCompanyList();
    this.getContractList();
  },
  methods: {
    async getCompanyList() {
      this.companyList = await this.$api('/get-company-list');
      this.dataCompanyList = this.companyList.data;
    },
    async getContractList() {
      this.contractList = await this.$api('get-contract-list');
    },
    async updateCompany() {
      if (!this.editCompanyTitle) {
        this.$root.$emit('msg', 'error', 'Не заполнено название');
      } else if (this.editCompanyContractId === -1) {
        this.$root.$emit('msg', 'error', 'Не выбран договор');
      } else if (this.editCompanyId === -1 && this.dataCompanyList.find((company) => company.title === this.editCompanyTitle)) {
        this.$root.$emit('msg', 'error', 'Такая компания уже есть');
      } else {
        await this.$store.dispatch(actions.INC_LOADING);
        const { ok } = await this.$api('update-company', {
          id: this.editCompanyId,
          title: this.editCompanyTitle,
          shortTitle: this.editCompanyShortTitle,
          legalAddress: this.editCompanyLegalAddress,
          factAddress: this.editCompanyFactAddress,
          inn: this.editCompanyInn,
          ogrn: this.editCompanyOgrn,
          kpp: this.editCompanyKpp,
          bik: this.editCompanyBik,
          contractId: this.editCompanyContractId,
        });
        await this.$store.dispatch(actions.DEC_LOADING);
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Сохранено');
          await this.getCompanyList();
          this.clearEditCompany();
        } else {
          this.$root.$emit('msg', 'error', 'Ошибка');
        }
      }
    },
    async editCompany(company) {
      await this.$store.dispatch(actions.INC_LOADING);
      this.currentCompany = await this.$api('get-current-company', { id: company.id });
      await this.$store.dispatch(actions.DEC_LOADING);
      this.dataCurrentCompany = this.currentCompany.data;
      this.editCompanyId = company.id;
      this.editCompanyTitle = company.title;
      this.editCompanyShortTitle = this.dataCurrentCompany.short_title;
      this.editCompanyLegalAddress = this.dataCurrentCompany.legal_address;
      this.editCompanyFactAddress = this.dataCurrentCompany.fact_address;
      this.editCompanyInn = this.dataCurrentCompany.inn;
      this.editCompanyOgrn = this.dataCurrentCompany.ogrn;
      this.editCompanyKpp = this.dataCurrentCompany.kpp;
      this.editCompanyBik = this.dataCurrentCompany.bik;
      this.editCompanyContractId = this.dataCurrentCompany.contract_id;
    },
    clearEditCompany() {
      this.editCompanyId = -1;
      this.editCompanyTitle = '';
      this.editCompanyShortTitle = '';
      this.editCompanyLegalAddress = '';
      this.editCompanyFactAddress = '';
      this.editCompanyInn = '';
      this.editCompanyOgrn = '';
      this.editCompanyKpp = '';
      this.editCompanyBik = '';
      this.editCompanyContractId = -1;
    },
    getOnlyNumber(event, vModel) {
      this[vModel] = event.target.value.replace(/[^0-9.]/g, '');
    },
  },
};
</script>

<style scoped>
.box {
  background-color: #FFF;
  margin: 10px 10px;
  flex-basis: 350px;
  flex-grow: 1;
  border-radius: 4px;
  max-height: 627px;
}

.main {
  display: flex;
  flex-wrap: wrap;
}
.scroll {
  overflow-y: auto;
  max-height: 523px;
}
.title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-left: 12px;
}
.table {
  margin-bottom: 0;
  table-layout: fixed;
}
label {
  margin-left: 12px;
}
.border {
  border: 1px solid #ddd;
}
</style>
