<template>
  <div class="filters">
    <h4>Прайс</h4>
    <Treeselect
      v-model="selectedPrice"
      :options="priceList.data"
      :clearable="false"
      placeholder="Выберите прайс"
      value-format="object"
    />
    <h4 v-if="selectedPrice.id !== -1">
      Исследования
    </h4>
    <div
      v-if="selectedPrice.id !== -1"
      class="card-no-hover card card-1"
    >
      <input
        v-model="search"
        class="form-control"
        style="padding-left: 6px"
        placeholder="Поиск исследования"
      >
      <table class="table table-bordered">
        <colgroup>
          <col width="85%">
          <col width="15%">
        </colgroup>
        <tr>
          <td class="text-center">
            <strong>Название</strong>
          </td>
          <td class="text-center">
            <strong>Цена</strong>
          </td>
        </tr>
        <tr
          v-if="filteredRows.length === 0"
          class="text-center"
        >
          <td colspan="2">
            Нет данных
          </td>
        </tr>
        <tr
          v-for="(coastResearch) in filteredRows"
          :key="coastResearch.id"
          class="tablerow table-hover"
        >
          <td
            class="tablerow table-hover"
            style="padding-left: 6px"
          >
            {{ coastResearch.research.title }}
          </td>
          <td>
            <input
              v-model="coastResearch.coast"
              :disabled="!selectedPrice.status"
              type="number"
              min="0.01"
              step="0.01"
              class="text-right form-control"
            >
          </td>
          <td class="tablerow">
            <button
              v-tippy
              :disabled="!selectedPrice.status"
              class="btn btn-blue-nb"
              title="Сохранить цену"
              @click="updateCoastResearchInPrice(coastResearch)"
            >
              <i class="fa fa-save" />
            </button>
          </td>
          <td>
            <button
              v-tippy
              :disabled="!selectedPrice.status"
              class="btn btn-blue-nb"
              title="Удалить исследование"
              @click="deleteResearchInPrice(coastResearch)"
            >
              <i class="fa fa-times" />
            </button>
          </td>
        </tr>
      </table>
    </div>
    <h4 v-if="selectedPrice.id !== -1 && selectedPrice.status === true">
      Добавить исследование в прайс
    </h4>
    <div v-if="selectedPrice.id !== -1 && selectedPrice.status === true">
      <table
        class="table table-bordered"
      >
        <colgroup>
          <col width="85%">
          <col width="15%">
        </colgroup>
        <tr>
          <Treeselect
            v-model="selectedResearch"
            :options="researchList.data"
            :disable-branch-nodes="true"
            :append-to-body="true"
            placeholder="Выберите исследование"
          />
          <td>
            <input
              v-model="coast"
              :disabled="!selectedPrice.status"
              type="number"
              class="text-right form-control"
              min="0.01"
              step="0.01"
              placeholder="Цена"
            >
          </td>
          <td>
            <button
              v-tippy
              :disabled="!selectedPrice.status"
              class="btn btn-blue-nb"
              title="Добавить исследование"
              @click="updateResearchListInPrice"
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
  name: 'ConstructPrice',
  components: { Treeselect },
  data() {
    return {
      priceList: {},
      selectedPrice: { id: -1, label: 'Выберите прайс', status: false },
      selectedResearch: null,
      coast: '',
      researchList: {},
      search: '',
      coastResearches: [],
      originalCoastResearch: [],
    };
  },
  computed: {
    filteredRows() {
      return this.originalCoastResearch.filter(coastResearch => {
        const research = coastResearch.research.title.toLowerCase();
        const searchTerm = this.search.toLowerCase();

        return research.includes(searchTerm);
      });
    },
  },
  watch: {
    selectedPrice() {
      this.getCurrentCoastResearchesInPrice();
    },
  },
  mounted() {
    this.getPriceList();
    this.getResearchList();
  },
  methods: {
    async getPriceList() {
      this.priceList = await this.$api('/get-price-list');
    },
    async getResearchList() {
      this.researchList = await this.$api('/get-research-list');
    },
    async getCurrentCoastResearchesInPrice() {
      this.coastResearches = await this.$api('/get-current-coast-researches-in-price', this.selectedPrice);
      this.originalCoastResearch = this.coastResearches.data;
    },
    async updateCoastResearchInPrice(coastResearch) {
      if (Number(coastResearch.coast) > 0) {
        await this.$store.dispatch(actions.INC_LOADING);
        const { ok, message } = await this.$api('/update-coast-research-in-price', {
          coastResearchId: coastResearch.id,
          coast: coastResearch.coast,
        });
        await this.$store.dispatch(actions.DEC_LOADING);
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Цена обновлена');
        } else {
          this.$root.$emit('msg', 'error', message);
        }
      } else {
        this.$root.$emit('msg', 'error', 'Неверная цена');
      }
    },
    async deleteResearchInPrice(coastResearch) {
      // eslint-disable-next-line no-alert
      if (window.confirm('Исследование будет удалено из прайса')) {
        await this.$store.dispatch(actions.INC_LOADING);
        const { ok, message } = await this.$api('/delete-research-in-price', { coastResearchId: coastResearch.id });
        await this.$store.dispatch(actions.DEC_LOADING);
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Исследование удалено');
          await this.getCurrentCoastResearchesInPrice();
        } else {
          this.$root.$emit('msg', 'error', message);
        }
      }
    },
    async updateResearchListInPrice() {
      if (!(this.selectedResearch && this.coast && this.selectedPrice.id !== -1)) {
        this.$root.$emit('msg', 'error', 'Данные не заполнены');
      } else if (this.coastResearches.data.find((i) => i.research.id === this.selectedResearch)) {
        this.$root.$emit('msg', 'error', 'Исследование уже есть в прайсе');
      } else if (Number(this.coast) <= 0) {
        this.$root.$emit('msg', 'error', 'Неверная цена');
      } else {
        await this.$store.dispatch(actions.INC_LOADING);
        const { ok, message } = await this.$api('/update-research-list-in-price', {
          priceId: this.selectedPrice.id,
          researchId: this.selectedResearch,
          coast: this.coast,
        });
        await this.$store.dispatch(actions.DEC_LOADING);
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Исследование добавлено');
          await this.getCurrentCoastResearchesInPrice();
          this.selectedResearch = null;
          this.coast = '';
        } else {
          this.$root.$emit('msg', 'error', message);
        }
      }
    },
  },
};
</script>

<style scoped>
.filters {
  padding: 10px;
  margin: 10px 50px;
}
::v-deep .form-control {
  border: none;
  background-color: transparent;
  padding: 6px 0;
}
::v-deep .card {
  margin: 1rem 0;
}
::v-deep .btn {
  margin: auto;
  display: block;
  border-radius: 0;
  padding: 7px 12px;
}
.tablerow {
  border: 1px solid #dddddd;
}
</style>
