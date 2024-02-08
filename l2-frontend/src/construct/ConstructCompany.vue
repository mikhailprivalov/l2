<template>
  <div class="container">
    <div class="flex flex-wrap">
      <div class="box card-1 card-no-hover">
        <h5 class="text-center">
          {{ isNewCompany ? 'Добавить компанию' : 'Обновить компанию' }}
        </h5>
        <h6
          v-if="!isNewCompany"
          class="text-center"
        >
          {{ originShortTitle }} (<strong>UUID:</strong> {{ company_uuid }})
        </h6>
        <div class="margin-right margin-left">
          <FormulateForm
            v-model="editorCompany"
            @submit="updateCompany"
          >
            <FormulateInput
              name="title"
              type="text"
              validation-name=" "
              error-behavior="live"
              label="Полное название"
              required
              validation="required:trim"
            />
            <FormulateInput
              name="shortTitle"
              type="text"
              label="Краткое название"
            />
            <FormulateInput
              name="legalAddress"
              type="text"
              label="Юридический адрес"
            />
            <FormulateInput
              name="factAddress"
              type="text"
              label="Фактический адрес"
            />
            <div class="row f-row">
              <div class="col-xs-6">
                <FormulateInput
                  name="inn"
                  type="text"
                  maxlength="12"
                  validation-name=" "
                  error-behavior="live"
                  label="ИНН"
                  required
                  validation="required:trim|number|"
                  inputmode="numeric"
                  pattern="[0-9]*"
                />
                <FormulateInput
                  name="ogrn"
                  type="text"
                  maxlength="13"
                  label="ОГРН"
                  validation-name=" "
                  error-behavior="live"
                  validation="number"
                  inputmode="numeric"
                  pattern="[0-9]*"
                />
              </div>
              <div class="col-xs-6">
                <FormulateInput
                  name="kpp"
                  type="text"
                  maxlength="9"
                  label="КПП"
                  validation-name=" "
                  error-behavior="live"
                  validation="number"
                  inputmode="numeric"
                  pattern="[0-9]*"
                />
                <FormulateInput
                  name="bik"
                  type="text"
                  maxlength="9"
                  label="БИК"
                  validation-name=" "
                  error-behavior="live"
                  validation="number"
                  inputmode="numeric"
                  pattern="[0-9]*"
                />
              </div>
            </div>
            <FormulateInput
              type="select"
              :options="contracts.data"
              name="contractId"
              label="Договор"
            />
            <div class="flex flex-space-between">
              <div>
                <FormulateInput
                  type="checkbox"
                  name="cppSend"
                  label="Отправлять в ЦПП"
                />
              </div>
              <div class="flex flex-right">
                <FormulateInput
                  class="margin-right"
                  type="button"
                  :label="isNewCompany ? 'Очистить' : 'Отменить'"
                  @click="clearEditCompany"
                />
                <FormulateInput
                  type="submit"
                  class="nbr margin-right"
                  :label="isNewCompany ? 'Добавить' : 'Сохранить'"
                />
              </div>
            </div>
          </FormulateForm>
          <div
            v-if="!isNewCompany"
            class="flex flex-space-between"
          >
            <div class="flex fixed-height">
              <input
                v-model="date"
                type="date"
                class="form-control date-input"
              >
              <button
                v-tippy
                title="Списки на мед. осмотр"
                class="btn last btn-blue-nb nbr load-exam-data"
                @click="getExaminationList"
              >
                Списки
              </button>
              <input
                id="month"
                v-model="month"
                class="margin-left margin-right checkbox-input"
                type="checkbox"
              >
              <div class="month">
                <label
                  for="month"
                  class="month-label"
                >За месяц</label>
              </div>
            </div>
            <div>
              <ul class="nav navbar">
                <LoadFile :company-inn="editorCompany.inn" />
              </ul>
            </div>
          </div>
        </div>
      </div>
      <div class="box card-1 card-no-hover">
        <h5 class="text-center">
          Компании
        </h5>
        <input
          v-model.trim="searchCompany"
          class="form-control nbr search"
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
                <div class="button">
                  <button
                    v-tippy
                    title="Редактировать"
                    class="btn last btn-blue-nb nbr"
                    @click="editCompany(company)"
                  >
                    <i class="fa fa-pencil" />
                  </button>
                </div>
              </td>
            </tr>
          </table>
        </div>
      </div>
      <div class="box card-1 card-no-hover">
        <h5 class="text-center">
          {{ 'Отделы компании' }}
        </h5>
        <input
          v-model.trim="searchDepartment"
          class="form-control nbr search"
          placeholder="Фильтр по названию..."
        >
        <div class="scroll">
          <table class="table">
            <colgroup>
              <col>
              <col width="40">
            </colgroup>
            <tr
              v-if="filteredDepartments.length === 0"
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
              v-for="(department) in filteredDepartments"
              :key="department.id"
            >
              <td class="border">
                <input
                  v-model="department.label"
                  class="form-control padding-left no-border"
                >
              </td>
              <td class="border">
                <div class="button">
                  <button
                    v-tippy
                    title="Сохранить"
                    class="btn last btn-blue-nb nbr"
                    @click="updateDepartment(department)"
                  >
                    <i class="fa fa-save" />
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="editorCompany.pk">
              <td class="border">
                <input
                  v-model="newDepartment"
                  class="form-control padding-left no-border"
                >
              </td>
              <td class="border">
                <div class="button">
                  <button
                    v-tippy
                    title="Добавить"
                    class="btn last btn-blue-nb nbr"
                    @click="addDepartment"
                  >
                    <i class="fa fa-plus" />
                  </button>
                </div>
              </td>
            </tr>
          </table>
        </div>
      </div>
    </div>
    <div
      v-if="showExaminationList"
      class="flex flex-wrap"
    >
      <div class="box exam-box card-1 card-no-hover">
        <h5 class="text-center no-margin">
          {{ originShortTitle + ' мед. осмотры на: ' + dateTitle }}
        </h5>
        <div class="flex">
          Исключить исследования:
        </div>
        <Treeselect
          v-model="excludedResearches"
          :multiple="true"
          :options="researches.data"
          :disable-branch-nodes="true"
          :append-to-body="true"
          placeholder="Выберите исследование"
        />
        <div class="flex flex-right">
          <div :class="needOffloadCpp ? 'button-check' : 'print'">
            <div class="button">
              <button
                v-tippy
                title="Печать"
                class="btn last btn-blue-nb nbr"
                @click="print"
              >
                Набор документов
              </button>
            </div>
          </div>
        </div>
        <VeTable
          :columns="columns"
          :table-data="examListPagination"
          row-key-field-name="card_id"
          :checkbox-option="checkboxOption"
          :cell-selection-option="cellSelectionOption"
        />
        <div
          v-show="examinationList.length === 0"
          class="empty-list"
        >
          Нет записей
        </div>
        <div class="flex flex-space-between">
          <VePagination
            :total="examinationList.length"
            :page-index="page"
            :page-size="pageSize"
            :page-size-option="pageSizeOptions"
            @on-page-number-change="pageNumberChange"
            @on-page-size-change="pageSizeChange"
          />
          <div :class="needOffloadCpp ? 'button-check' : 'print'">
            <div class="button">
              <button
                v-tippy
                title="Печать"
                class="btn last btn-blue-nb nbr"
                @click="print"
              >
                Набор документов
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import {
  VeLocale,
  VePagination,
  VeTable,
} from 'vue-easytable';
import 'vue-easytable/libs/theme-default/index.css';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import ruRu from '@/locales/ve';
import VueTippyTd from '@/construct/VueTippyTd.vue';
import * as actions from '@/store/action-types';
import LoadFile from '@/ui-cards/LoadFile.vue';

VeLocale.use(ruRu);

export default {
  name: 'ConstructCompany',
  components: {
    LoadFile, VueTippyTd, VeTable, VePagination, Treeselect,
  },
  data() {
    return {
      companies: [],
      contracts: [],
      searchCompany: '',
      searchDepartment: '',
      currentCompany: {},
      departments: [],
      newDepartment: '',
      editorCompany: {},
      originShortTitle: '',
      date: '',
      showExaminationList: false,
      examinationList: [],
      selectedCards: [],
      dateTitle: '',
      checkboxOption: {
        selectedRowChange: ({ selectedRowKeys }) => {
          this.selectedCards = selectedRowKeys;
        },
        selectedAllChange: ({ selectedRowKeys }) => {
          this.selectedCards = selectedRowKeys;
        },
      },
      basePk: -1,
      cellSelectionOption: {
        enable: false,
      },
      columns: [],
      page: 1,
      pageSize: 25,
      pageSizeOptions: [25, 50, 100],
      excludedResearches: [],
      researches: [],
      month: false,
      company_uuid: '',
      companySppSend: false,
    };
  },
  computed: {
    filteredCompany() {
      return this.companies.filter(company => {
        const companyTitle = company.title.toLowerCase();
        const searchTerm = this.searchCompany.toLowerCase();

        return companyTitle.includes(searchTerm);
      });
    },
    filteredDepartments() {
      return this.departments.filter(department => {
        const departmentTitle = department.label.toLowerCase();
        const searchTerm = this.searchDepartment.toLowerCase();

        return departmentTitle.includes(searchTerm);
      });
    },
    isNewCompany() {
      return !this.editorCompany.pk;
    },
    needOffloadCpp() {
      return this.companySppSend === true;
    },
    examListPagination() {
      return this.examinationList.slice((this.page - 1) * this.pageSize, this.page * this.pageSize);
    },
  },
  mounted() {
    this.getCompanies();
    this.getContracts();
    this.getInternalBase();
  },
  methods: {
    async getCompanies() {
      const companies = await this.$api('/get-companies');
      this.companies = companies.data;
    },
    async getContracts() {
      this.contracts = await this.$api('get-contracts');
    },
    async updateCompany() {
      if (this.companies.find((company) => company.title === this.editorCompany.title
        && company.id !== this.editorCompany.id)) {
        this.$root.$emit('msg', 'error', 'Такое название уже есть');
      } else {
        await this.$store.dispatch(actions.INC_LOADING);
        const { ok, message } = await this.$api('update-company', this.editorCompany);
        await this.$store.dispatch(actions.DEC_LOADING);
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Сохранено');
          this.clearEditCompany();
          await this.getContracts();
          await this.getCompanies();
        } else {
          this.$root.$emit('msg', 'error', message);
        }
      }
    },
    async editCompany(company) {
      await this.getContracts();
      await this.$store.dispatch(actions.INC_LOADING);
      this.currentCompany = await this.$api('get-company', company, 'pk');
      await this.$store.dispatch(actions.DEC_LOADING);
      if (this.currentCompany.data.contractData) {
        this.contracts.data.push({ ...this.currentCompany.data.contractData });
      }
      await this.getDepartments(company.pk);
      this.editorCompany = this.currentCompany.data;
      this.originShortTitle = this.editorCompany.shortTitle;
      this.company_uuid = this.editorCompany.uuid;
      this.companySppSend = this.editorCompany.cppSend;
      this.examinationList = [];
      this.getColumns();
    },
    clearEditCompany() {
      this.getContracts();
      this.editorCompany = {};
      this.departments = [];
      this.originTitle = '';
      this.newDepartment = '';
      this.examinationList = [];
    },
    async getDepartments(companyId) {
      const depart = await this.$api('company-departments-find', { company_db: companyId });
      this.departments = depart.data;
    },
    async updateDepartment(department) {
      if (!department.label) {
        this.$root.$emit('msg', 'error', 'Название не заполнено');
      } else if (this.departments.find((depart) => depart.label === department.label
        && depart.id !== department.id)) {
        this.$root.$emit('msg', 'error', 'Такое название уже есть');
      } else {
        await this.$store.dispatch(actions.INC_LOADING);
        const { ok, message } = await this.$api('update-department', department);
        await this.$store.dispatch(actions.DEC_LOADING);
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Сохранено');
        } else {
          this.$root.$emit('msg', 'error', message);
        }
      }
    },
    async addDepartment() {
      if (!this.newDepartment) {
        this.$root.$emit('msg', 'error', 'Название не заполнено');
      } else if (this.departments.find((depart) => depart.label === this.newDepartment)) {
        this.$root.$emit('msg', 'error', 'Такое название уже есть');
      } else {
        await this.$store.dispatch(actions.INC_LOADING);
        const { ok, message } = await this.$api('add-department', {
          department: this.newDepartment,
          company_id: this.editorCompany.pk,
        });
        await this.$store.dispatch(actions.DEC_LOADING);
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Сохранено');
          await this.getDepartments(this.editorCompany.pk);
          this.newDepartment = '';
        } else {
          this.$root.$emit('msg', 'error', message);
        }
      }
    },
    getColumns() {
      const columnsTemplate = [
        {
          field: 'number',
          key: 'number',
          title: '№',
          align: 'center',
          width: 30,
          renderBodyCell: ({ rowIndex }) => rowIndex + 1,
        },
        {
          field: 'card',
          key: 'card',
          title: '',
          align: 'center',
          width: 30,
          renderBodyCell: ({ row }, h) => (
            h('div', { class: 'button' }, [
              h(
                'button',
                { class: this.button.transparentButton, on: { click: () => { this.openCard(row.card_id); } } },
                [h('i', { class: 'fa-solid fa-user' })],
              ),
            ])
          ),
        },
        {
          field: 'fio',
          key: 'fio',
          title: 'Пациент',
          align: 'left',
          width: 300,
        },
        {
          field: 'date', key: 'date', title: 'Дата', align: 'center', width: 50,
        },
        {
          field: 'harmful_factors', key: 'harmful_factors', title: 'Вредные факторы', align: 'left', width: 200,
        },
        {
          field: 'research_titles', key: 'research_titles', title: 'Исследования', align: 'left',
        },
        {
          field: 'print',
          key: 'print',
          title: '',
          align: 'center',
          width: 30,
          renderBodyCell: ({ row }, h) => (
            h('div', { class: 'button' }, [
              h(
                'button',
                {
                  class: this.button.transparentButton,
                  on: {
                    click: () => {
                      this.print(
                        row.date,
                        row.research_id,
                        row.card_id,
                      );
                    },
                  },
                },
                [h('i', { class: 'fa-solid fa-print' })],
              ),
            ])
          ),
        },
        {
          field: '', key: 'select', title: '', align: 'center', width: 30, type: 'checkbox',
        },
      ];
      if (this.needOffloadCpp) {
        const cppCol = {
          field: 'cppSendStatus',
          key: 'cppSendStatus',
          title: 'ЦПП',
          align: 'center',
          width: 100,
        };
        columnsTemplate.splice(-2, 0, cppCol);
      }
      this.columns = columnsTemplate;
    },
    async getExaminationList() {
      if (!this.date) {
        this.$root.$emit('msg', 'error', 'Дата не выбрана');
      } else {
        await this.$store.dispatch(actions.INC_LOADING);
        const medicalExamination = await this.$api('get-examination-list', {
          date: this.date,
          company: this.editorCompany.pk,
          month: this.month,
        });
        await this.$store.dispatch(actions.DEC_LOADING);
        this.showExaminationList = true;
        this.examinationList = medicalExamination.data;
        await this.getResearches();
        if (this.month) {
          this.dateTitle = this.date.split('-').reverse().slice(-2).join('.');
        } else {
          this.dateTitle = this.date.split('-').reverse().join('.');
        }
      }
    },
    async getResearches() {
      this.researches = await this.$api('/get-research-list');
    },
    async getInternalBase() {
      await this.$store.dispatch(actions.DEC_LOADING);
      const baseData = await this.$api('/bases');
      await this.$store.dispatch(actions.DEC_LOADING);
      this.basePk = baseData.bases[0].pk;
    },
    openCard(cardPk) {
      window.open(`/ui/directions?card_pk=${cardPk}&base_pk=${this.basePk}`);
    },
    pageNumberChange(number: number) {
      this.page = number;
    },
    pageSizeChange(size: number) {
      this.pageSize = size;
    },
    async print(date = '', researchId = [], cardId = -1) {
      let printData = [];
      if (cardId === -1 && this.selectedCards.length > 0) {
        printData = this.examinationList.filter((exam) => {
          const card = exam.card_id;
          const selectCard = this.selectedCards;
          return selectCard.includes(card);
        }).map((exam) => ({
          card_id: exam.card_id,
          date: exam.date,
          research: exam.research_id.filter(id => !this.excludedResearches.includes(id)),
        }));
      } else if (cardId !== -1) {
        printData = [{ card_id: cardId, date, research: researchId.filter(id => !this.excludedResearches.includes(id)) }];
      }
      if (printData.length > 0) {
        await this.$store.dispatch(actions.INC_LOADING);
        const result = await this.$api('print-medical-examination-data', {
          cards: printData,
        });
        await this.$store.dispatch(actions.DEC_LOADING);
        if (result.id) {
          window.open(`/forms/pdf?type=112.03&id=${encodeURIComponent(JSON.stringify(result.id))}`, '_blank');
        }
      } else {
        this.$root.$emit('msg', 'error', 'Пациенты не выбраны');
      }
    },
  },
};
</script>

<style lang="scss" scoped>
.box {
  background-color: #FFF;
  margin: 30px 10px;
  flex-basis: 350px;
  flex-grow: 1;
  border-radius: 4px;
  min-height: 426px;
}
.exam-box {
  min-height: 0;
}
.flex-wrap {
  flex-wrap: wrap;
}
.scroll {
  overflow-y: auto;
  max-height: 653px;
}
.title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-left: 9px;
}
.table {
  margin-bottom: 0;
  table-layout: fixed;
}
::v-deep .formulate-input-element {
  max-width: 100%;
}
::v-deep .formulate-input-label {
  padding-left: 9px;
}
::v-deep .formulate-input-error {
  padding-left: 9px;
}
.border {
  border: 1px solid #ddd;
}
.flex-space-between {
  justify-content: space-between;
}
.flex-right {
  justify-content: flex-end;
}
.flex {
  display: flex;
}
.fixed-height {
  height: 42px;
}
.flex-bottom {
  align-items: flex-end;
}
.no-margin {
  margin-top: 0;
  margin-bottom: 0;
}
.margin-right {
  margin-right: 5px;
}
.margin-left {
  margin-left: 5px;
}
.container {
  width: 90%;
  margin: auto;
}
.padding-left {
  padding-left: 9px;
}
.search {
  margin-top: 36px;
  padding-left: 9px;
}
.no-border {
  border: none;
}
.add-file {
  width: 130px;
  margin: 0 auto;
}
::v-deep .navbar {
  margin-bottom: 0;
}
.add-file {
  width: 140px;
}
.load-exam-data {
  width: 80px;
}
.date-input {
  width: 120px;
  padding-top: 20px;
  padding-bottom: 20px;
  border-radius: 0
}
.empty-list {
  width: 85px;
  margin: 20px auto;
}
.month {
  margin-top: 10px;
}
.checkbox-input {
  margin-top: 0;
  margin-bottom: 0;
}
.margin-bottom {
  margin-bottom: 5px;
}
.button-check {
  width: 310px;
}
.print {
  width: 155px;
}
.row-div {
  width: 100%;
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
.month-label {
  font-weight: 600;
}
</style>

<style module="button">
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
</style>
