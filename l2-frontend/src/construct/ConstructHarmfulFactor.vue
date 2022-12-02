<template>
  <div>
    <h4>
      Факторы вредности
    </h4>
    <div>
      <input
        v-model="search"
        class="form-control search"
        placeholder="Поиск исследования"
      >
    </div>
    <div
      class="card-no-hover card card-1"
    >
      <div class="scroll">
        <table class="table">
          <colgroup>
            <col>
            <col>
            <col style="width: 300px">
            <col style="width: 99px">
          </colgroup>
          <thead class="sticky">
            <tr>
              <th
                class="text-center"
              >
                <strong>Название</strong>
              </th>
              <th
                class="text-center"
              >
                <strong>Описание</strong>
              </th>
              <th>Шаблон</th>
              <th />
            </tr>
          </thead>
          <tr
            v-if="filteredFactors.length === 0"
            class="text-center"
          >
            <td
              colspan="4"
            >
              Нет данных
            </td>
          </tr>
          <tr
            v-for="(factor) in filteredFactors"
            :key="factor.pk"
            class="td-table"
          >
            <td class="td-table">
              <input
                v-model="factor.title"
                class="form-control"
              >
            </td>
            <td class="td-table">
              <input
                v-model="factor.description"
                class="form-control"
              >
            </td>
            <td>
              <Treeselect
                v-model="factor.template"
                :options="templateList.data"
                :disable-branch-nodes="true"
                :append-to-body="true"
                placeholder="Выберите шаблон"
              />
            </td>
            <td>
              <button
                v-tippy
                style="padding: 7px 12px"
                class="btn last btn-blue-nb nbr"
                title="Сохранить фактор"
              >
                Сохранить
              </button>
            </td>
          </tr>
        </table>
      </div>
    </div>
    <h4>
      Добавить фактор вредности
    </h4>
    <div>
      <table class="table table-bordered">
        <colgroup>
          <col>
          <col>
          <col style="width: 300px">
          <col style="width: 99px">
        </colgroup>
        <tr>
          <td class="td-table">
            <input
              v-model="title"
              class="form-control"
              placeholder="Название"
            >
          </td>
          <td class="td-table">
            <input
              v-model="description"
              class="form-control"
              placeholder="Описание"
            >
          </td>
          <td>
            <Treeselect
              v-model="template_id"
              :disable-branch-nodes="true"
              :append-to-body="true"
              :options="templateList.data"
              placeholder="Выберите шаблон"
            />
          </td>
          <td>
            <button
              v-tippy
              class="btn last btn-blue-nb nbr"
              style="padding: 7px 16px"
              title="Добавить фактор"
            >
              Добавить
            </button>
          </td>
        </tr>
      </table>
    </div>
  </div>
</template>

<script lang="ts">

import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

export default {
  name: 'ConstructPrice',
  components: { Treeselect },
  data() {
    return {
      factorList: [],
      templateList: {},
      search: '',
      title: '',
      description: '',
      template_id: -1,
    };
  },
  computed: {
    filteredFactors() {
      return this.factorList.filter(factor => {
        const title = factor.title.toLowerCase();
        const searchTerm = this.search.toLowerCase();

        return title.includes(searchTerm);
      });
    },
  },
  mounted() {
    this.getFactorList();
    this.getTemplateList();
  },
  methods: {
    async getFactorList() {
      const factors = await this.$api('/get-factor-list');
      this.factorList = factors.data;
    },
    async getTemplateList() {
      this.templateList = await this.$api('/get-template-list');
    },
  },
};
</script>

<style scoped>
::v-deep .form-control {
  border: none;
  padding: 6px 0;
  background-color: transparent;
}
::v-deep .card {
  margin: 1rem 0;
}
.table {
  margin-bottom: 0;
  table-layout: fixed;
}
.td-table {
  border: 1px solid #ddd;
  padding-left: 6px;
}
.scroll {
  min-height: 119px;
  max-height: calc(100vh - 400px);
  overflow-y: auto;
}
.sticky {
  position: sticky;
  top: 0;
  background-color: white;
}
.table > thead > tr > th {
  border-bottom: 0;
}
.search {
  border: 1px solid #ddd;
  border-radius: 5px;
  padding-left: 6px;
  background-color: white;
}
</style>
