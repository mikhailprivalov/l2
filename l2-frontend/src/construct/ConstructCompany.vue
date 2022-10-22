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
              class="title"
              :text="company.title"
            />
            <td>
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
        Создание/Редактирование
      </h5>
      <div>
        <label>Наименование организации</label>
        <input
          v-model="companyEditor.title"
          placeholder="Введите наименование организации"
          class="form-control"
        >
        <label>Сокращенное наименование</label>
        <input
          v-model="companyEditor.shortTitle"
          placeholder="Введите сокращенное наименование"
          class="form-control"
        >
        <label>Юридический адрес</label>
        <input
          v-model="companyEditor.legalAddress"
          placeholder="Введите адрес"
          class="form-control"
        >
        <label>Фактический адрес</label>
        <input
          v-model="companyEditor.factAddress"
          placeholder="Введите адрес"
          class="form-control"
        >
        <label>ИНН</label>
        <input
          v-model="companyEditor.inn"
          type="number"
          min="0"
          placeholder="Введите ИНН"
          class="form-control"
          @input="maxlength(12, companyEditor.inn)"
        >
        <label>ОГРН</label>
        <input
          v-model="companyEditor.ogrn"
          type="number"
          min="0"
          placeholder="Введите ОГРН"
          class="form-control"
          @input="maxlength(13, companyEditor.ogrn)"
        >
        <label>КПП</label>
        <input
          v-model="companyEditor.kpp"
          type="number"
          min="0"
          placeholder="Введите КПП"
          class="form-control"
          @input="maxlength(9, companyEditor.kpp)"
        >
        <label>БИК</label>
        <input
          v-model="companyEditor.bik"
          maxlength="9"
          type="number"
          min="0"
          placeholder="Введите БИК"
          class="form-control"
          @input="maxlength(9, companyEditor.bik)"
        >
        <label>Договор</label>
        <Treeselect
          v-model="companyEditor.contractId"
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
            @click="saveCompany"
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

export default {
  name: 'ConstructCompany',
  components: { VueTippyTd, Treeselect },
  data() {
    return {
      companyList: {},
      dataCompanyList: [],
      contractList: {},
      search: '',
      companyEditor: {
        id: -1,
        title: '',
        shortTitle: '',
        legalAddress: '',
        factAddress: '',
        inn: '',
        ogrn: '',
        kpp: '',
        bik: '',
        contractId: -1,
      },
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
    async saveCompany() {
      console.log('привет');
    },
    editCompany(company) {
      this.companyEditor.id = company.id;
      this.companyEditor.title = company.title;
      this.companyEditor.shortTitle = company.short_title;
      this.companyEditor.legalAddress = company.legal_address;
      this.companyEditor.factAddress = company.fact_address;
      this.companyEditor.inn = company.inn;
      this.companyEditor.ogrn = company.ogrn;
      this.companyEditor.kpp = company.kpp;
      this.companyEditor.bik = company.bik;
      this.companyEditor.contractId = company.contract_id;
    },
    clearEditCompany() {
      this.companyEditor.id = -1;
      this.companyEditor.title = '';
      this.companyEditor.shortTitle = '';
      this.companyEditor.legalAddress = '';
      this.companyEditor.factAddress = '';
      this.companyEditor.inn = '';
      this.companyEditor.ogrn = '';
      this.companyEditor.kpp = '';
      this.companyEditor.bik = '';
      this.companyEditor.contractId = -1;
    },
    maxlength(maxlength, data) {
      console.log(data, maxlength);
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
  max-height: 70%;
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
</style>
