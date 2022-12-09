<template>
  <div class="container">
    <div class="main">
      <div class="box card-1 card-no-hover">
        <h5 class="text-center">
          {{ isNewCompany ? 'Добавить компанию' : 'Обновить компанию' }}
        </h5>
        <h6
          v-if="!isNewCompany"
          class="text-center"
        >
          {{ originShortTitle }}
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
            <div class="button">
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
          </FormulateForm>
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
              <col width="38.25">
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
                  class="form-control padding-left noborder"
                >
              </td>
              <td class="border">
                <button
                  v-tippy
                  title="Сохранить"
                  class="btn last btn-blue-nb nbr"
                  @click="updateDepartment(department)"
                >
                  <i class="fa fa-save" />
                </button>
              </td>
            </tr>
            <tr v-if="editorCompany.pk">
              <td class="border">
                <input
                  v-model="newDepartment"
                  class="form-control padding-left noborder"
                >
              </td>
              <td class="border">
                <button
                  v-tippy
                  title="Добавить"
                  class="btn last btn-blue-nb nbr"
                  @click="addDepartment"
                >
                  <i class="fa fa-plus" />
                </button>
              </td>
            </tr>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">

import VueTippyTd from '@/construct/VueTippyTd.vue';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import * as actions from '@/store/action-types';

export default {
  name: 'ConstructCompany',
  components: { VueTippyTd },
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
  },
  mounted() {
    this.getCompanies();
    this.getContracts();
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
    },
    clearEditCompany() {
      this.getContracts();
      this.editorCompany = {};
      this.departments = [];
      this.originTitle = '';
      this.newDepartment = '';
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
  },
};
</script>

<style scoped>
.box {
  background-color: #FFF;
  margin: 30px 10px;
  flex-basis: 350px;
  flex-grow: 1;
  border-radius: 4px;
  min-height: 390px;
}
.main {
  display: flex;
  flex-wrap: wrap;
}
.scroll {
  overflow-y: auto;
  max-height: 596px;
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
.button {
  display: flex;
  justify-content: flex-end;
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
.noborder {
  border: none;
}
</style>
