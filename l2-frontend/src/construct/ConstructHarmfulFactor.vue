<template>
  <div>
    <h4>
      Факторы вредности
    </h4>
    <div>
      <input
        v-model.trim="search"
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
            <col width="150">
            <col>
            <col width="150">
            <col width="99">
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
              <th
                class="text-center"
              >
                <strong>Шаблон</strong>
              </th>
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
            v-for="(factor, index) in filteredFactors"
            :key="factor.id"
            class="table-row"
          >
            <td class="table-row">
              <input
                v-model="factor.title"
                class="form-control padding-left"
                @input="onlyFactorsTitle(index, $event)"
              >
            </td>
            <td class="table-row">
              <input
                v-model="factor.description"
                class="form-control padding-left"
              >
            </td>
            <td>
              <Treeselect
                v-model="factor.template_id"
                :options="templates.data"
                :disable-branch-nodes="true"
                :append-to-body="true"
                placeholder="Выберите шаблон"
              />
            </td>
            <td class="table-row">
              <button
                v-tippy
                style="padding: 7px 42px"
                class="btn last btn-blue-nb nbr"
                title="Сохранить фактор"
                @click="updateFactor(factor)"
              >
                <i class="fa fa-save" />
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
          <col width="150">
          <col>
          <col width="150">
          <col width="99px">
        </colgroup>
        <tr>
          <td class="table-row">
            <input
              v-model="title"
              class="form-control padding-left"
              placeholder="Название"
              @input="onlyFactorsTitle(-1, $event, 'title')"
            >
          </td>
          <td class="table-row">
            <input
              v-model="description"
              class="form-control padding-left"
              placeholder="Описание"
            >
          </td>
          <td>
            <Treeselect
              v-model="template_id"
              :disable-branch-nodes="true"
              :append-to-body="true"
              :options="templates.data"
              placeholder="Выберите шаблон"
            />
          </td>
          <td>
            <button
              v-tippy
              class="btn last btn-blue-nb nbr"
              style="padding: 7px 15.4px"
              title="Добавить фактор"
              @click="addFactor"
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
import * as actions from '@/store/action-types';

export default {
  name: 'ConstructHarmfulFactor',
  components: { Treeselect },
  data() {
    return {
      factors: [],
      templates: {},
      search: '',
      title: '',
      description: '',
      template_id: null,
    };
  },
  computed: {
    filteredFactors() {
      return this.factors.filter(factor => {
        const title = factor.title.toLowerCase();
        const description = factor.description.toLowerCase();
        const searchTerm = this.search.toLowerCase();

        return description.includes(searchTerm) || title.includes(searchTerm);
      });
    },
  },
  mounted() {
    this.getFactors();
    this.getTemplates();
  },
  methods: {
    async getFactors() {
      this.factors = await this.$api('/get-harmful-factors');
    },
    async getTemplates() {
      this.templates = await this.$api('/get-templates');
    },
    async updateFactor(factor) {
      if (factor.title && factor.template_id) {
        await this.$store.dispatch(actions.INC_LOADING);
        const { ok, message } = await this.$api('/update-factor', factor);
        await this.$store.dispatch(actions.DEC_LOADING);
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Сохранено');
        } else {
          this.$root.$emit('msg', 'error', message);
        }
      } else {
        this.$root.$emit('msg', 'error', 'Ошибка заполнения');
      }
    },
    async addFactor() {
      if (this.title && this.template_id) {
        await this.$store.dispatch(actions.INC_LOADING);
        const { ok, message } = await this.$api('/add-factor', {
          title: this.title,
          description: this.description,
          template_id: this.template_id,
        });
        await this.$store.dispatch(actions.DEC_LOADING);
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Сохранено');
          await this.getFactors();
          this.title = '';
          this.description = '';
          this.template_id = null;
        } else {
          this.$root.$emit('msg', 'error', message);
        }
      } else {
        this.$root.$emit('msg', 'error', 'Ошибка заполнения');
      }
    },
    onlyFactorsTitle(index, event, title) {
      if (index !== -1) {
        this.filteredFactors[index].title = event.target.value.replace(/[^0-9.]/g, '');
      } else {
        this[title] = event.target.value.replace(/[^0-9.]/g, '');
      }
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
.scroll {
  min-height: 110.5px;
  max-height: calc(100vh - 350px);
  overflow-y: auto;
}
.table-row {
  border: 1px solid #ddd;
  border-radius: 0;
}
.padding-left {
  padding-left: 6px;
}
.sticky {
  position: sticky;
  top: 0;
  z-index: 1;
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
