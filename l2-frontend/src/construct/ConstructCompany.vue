<template>
  <div class="main">
    <div class="box card-1 card-no-hover">
      <h5 class="text-center">
        Компании
      </h5>
      <input
        v-model.trim="search"
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
        {{ editorCompany.id ? 'Редактирование компании' : 'Добавление компании' }}
      </h5>
      <div>
        <FormulateForm
          v-model="editorCompany"
          @submit="updateCompany"
        >
          <FormulateInput
            name="title"
            type="text"
            validation-name="Полное наименование"
            error-behavior="live"
            label="Полное наименование"
            required
            validation="required:trim"
          />
          <FormulateInput
            name="shortTitle"
            type="text"
            label="Сокращенное наименование"
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
          <FormulateInput
            name="inn"
            type="text"
            maxlength="12"
            validation-name="ИНН"
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
            validation-name="ОГРН"
            error-behavior="live"
            validation="number"
            inputmode="numeric"
            pattern="[0-9]*"
          />
          <FormulateInput
            name="kpp"
            type="text"
            maxlength="9"
            label="КПП"
            validation-name="КПП"
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
            validation-name="ОГРН"
            error-behavior="live"
            validation="number"
            inputmode="numeric"
            pattern="[0-9]*"
          />
          <label class="labelcon">Договор</label>
          <Treeselect
            v-model="editorCompany.contract_id"
            :options="contractList.data"
            :clearable="false"
            style="margin-bottom: 10px"
          />
          <FormulateInput
            type="button"
            label="Очистить"
            @click="clearEditCompany"
          />
          <FormulateInput
            type="submit"
            label="Сохранить"
          />
        </FormulateForm>
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
      editorCompany: {},
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
      if (this.dataCompanyList.find((company) => company.title === this.editorCompany.title
        || (this.editorCompany.id == null && company.inn === this.editorCompany.inn))) {
        this.$root.$emit('msg', 'error', 'Такая компания уже есть');
      } else {
        await this.$store.dispatch(actions.INC_LOADING);
        const { ok } = await this.$api('update-company', this.editorCompany);
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
      this.currentCompany = await this.$api('get-company', { id: company.id });
      await this.$store.dispatch(actions.DEC_LOADING);
      this.dataCurrentCompany = this.currentCompany.data;
      this.editorCompany = this.dataCurrentCompany;
    },
    clearEditCompany() {
      this.editorCompany = {};
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
  max-height: 723px;
}
.main {
  display: flex;
  flex-wrap: wrap;
}
.scroll {
  overflow-y: auto;
  max-height: 619px;
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
::v-deep .formulate-input {
  margin-bottom: 5px;
}

::v-deep .formulate-input .formulate-input-element {
    max-width: 100%;
}
.border {
  border: 1px solid #ddd;
}
.labelcon {
  font-size: 0.9em;
  font-weight: 600;
}
</style>
