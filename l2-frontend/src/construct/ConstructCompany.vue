<template>
  <div class="main">
    <div class="box card-1 card-no-hover">
      <h5 class="text-center">
        Компании
      </h5>
      <input
        v-model.trim="search"
        style="margin-top: 36px; padding-left: 9px;"
        class="form-control nbr"
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
        {{ editorCompany.pk ? 'Обновить компанию' : 'Добавить компанию' }}
      </h5>
      <h6
        v-if="editorCompany.pk"
        class="text-center"
      >
        {{ originTitle }}
      </h6>
      <div>
        <FormulateForm
          v-model="editorCompany"
          @submit="updateCompany"
        >
          <FormulateInput
            name="title"
            type="text"
            validation-name=" "
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
          <FormulateInput
            type="select"
            :options="contractList.data"
            name="contractId"
            label="Договор"
          />
          <div class="button">
            <FormulateInput
              style="margin-right: 5px"
              type="button"
              :label="editorCompany.pk ? 'Отменить' : 'Очистить'"
              @click="clearEditCompany"
            />
            <FormulateInput
              type="submit"
              class="nbr"
              style="margin-right: 5px"
              :label="editorCompany.pk ? 'Сохранить' : 'Добавить'"
            />
          </div>
        </FormulateForm>
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
      companyList: {},
      dataCompanyList: [],
      contractList: {},
      search: '',
      currentCompany: {},
      editorCompany: {},
      originTitle: '',
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
        && company.id !== this.editorCompany.id)) {
        this.$root.$emit('msg', 'error', 'Такое название уже есть');
      } else {
        await this.$store.dispatch(actions.INC_LOADING);
        const { ok, message } = await this.$api('update-company', this.editorCompany);
        await this.$store.dispatch(actions.DEC_LOADING);
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Сохранено');
          this.clearEditCompany();
          await this.getCompanyList();
        } else {
          this.$root.$emit('msg', 'error', message);
        }
      }
    },
    async editCompany(company) {
      await this.$store.dispatch(actions.INC_LOADING);
      this.currentCompany = await this.$api('get-company', company, 'pk');
      await this.$store.dispatch(actions.DEC_LOADING);
      this.editorCompany = this.currentCompany.data;
      this.originTitle = this.this.currentCompany.data.shortTitle;
    },
    clearEditCompany() {
      this.editorCompany = {};
      this.originTitle = '';
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
  min-height: 840px;
}
.main {
  display: flex;
  flex-wrap: wrap;
}
.scroll {
  overflow-y: auto;
  max-height: 790px;
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
</style>
