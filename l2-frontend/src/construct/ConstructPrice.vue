<template>
  <div class="filters">
    <h4>Прайс</h4>
    <Treeselect
      v-model="selectedPrice"
      :options="priceList.data"
      :clearable="false"
      placeholder="Выберите прайс"
      @input="getCurrentCoastResearchesData"
    />
    <h4>Исследования</h4>
    <div class="card-no-hover card card-1">
      <input
        v-model="search"
        class="form-control"
        placeholder="Поиск исследования"
      >
      <table>
        <colgroup>
          <col width="85%">
          <col width="15%">
        </colgroup>
        <tr>
          <td class="text-center"><strong>Название</strong></td>
          <td class="text-center"><strong>Цена</strong></td>
        </tr>
        <tr
          v-for="(coastResearch, idx) in filteredRows"
          :key="idx"
        >
          <td
            class="border-cell"
            style="padding-left: 1%"
          >
            {{ coastResearch.research.title }}
          </td>
          <td class="border-cell">
            <input
              v-model="coastResearch.coast"
              type="number"
              min="0"
              step="0.01"
              class="text-right form-control"
            >
          </td>
          <td class="border-cell">
            <button
              v-tippy
              class="btn btn-blue-nb"
              title="Сохранить цену"
              @click="updateCoastResearchInPrice(coastResearch)"
            >
              <i class="fa fa-save" />
            </button>
          </td>
        </tr>
      </table>
    </div>
    <h4>Добавить исследование в прайс</h4>
    <div>
      <table>
        <colgroup>
          <col width="85%">
          <col width="15%">
        </colgroup>
        <tr>
          <Treeselect
            v-model="selectedResearch"
            :options="researchList.data"
            placeholder="Выберите исследование"
          />
          <td class="border-cell">
            <input
              v-model="coast"
              type="number"
              class="text-right form-control"
              min="0"
              step="0.01"
            >
          </td>
          <td class="border-cell">
            <button
              v-tippy
              class="btn btn-blue-nb border-cell"
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

<script>

import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

export default {
  name: 'ConstructPrice',
  components: { Treeselect },
  data() {
    return {
      priceList: {},
      selectedPrice: null,
      selectedResearch: null,
      coast: null,
      researchList: {},
      search: '',
      coastResearches: [],
      originalCoastResearch: [],
    };
  },
  computed: {
    filteredRows() {
      return this.originalCoastResearch.filter(CoastResearch => {
        const research = CoastResearch.research.title.toString().toLowerCase();
        const searchTerm = this.search.toLowerCase();

        return research.includes(searchTerm);
      });
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
    async getCurrentCoastResearchesData() {
      this.coastResearches = await this.$api('/get-current-coast-researches', { id: this.selectedPrice });
      this.originalCoastResearch = this.coastResearches.data;
    },
    async updateCoastResearchInPrice(coastResearch) {
      const { ok } = await this.$api('/update-coast-research-in-price', {
        coastResearchId: coastResearch.id,
        coast: coastResearch.coast,
      });
      if (ok) {
        this.$root.$emit('msg', 'ok', 'Цена обновлена');
      } else {
        this.$root.$emit('msg', 'error', 'Цена не обновлена');
      }
    },
    async updateResearchListInPrice() {
      if (!(this.selectedResearch && this.coast && this.selectedPrice)) {
        this.$root.$emit('msg', 'error', 'Данные не заполнены');
      } else if (this.coastResearches.data.find((i) => i.research.id === this.selectedResearch)) {
        this.$root.$emit('msg', 'error', 'Исследование уже есть в прайсе');
      } else {
        const { ok } = await this.$api('/update-research-list-in-price', {
          priceId: this.selectedPrice,
          researchId: this.selectedResearch,
          coast: this.coast,
        });
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Исследование добавлено');
          await this.getCurrentCoastResearchesData();
          this.selectedResearch = null;
          this.coast = null;
        } else {
          this.$root.$emit('msg', 'error', 'Исследование не добавлено');
        }
      }
    },
  },
};
</script>

<style scoped>
.filters {
  padding: 10px;
  margin: 10px 8%;
}
::v-deep .form-control {
  background-color: #fff;
  border-radius: 0;
  border: none;
}
::v-deep .card {
  margin: 1rem 0;
}
::v-deep .btn {
  margin: auto;
  display: block;
  border-radius: 0;
}
.border-cell {
  border: 1px solid #dddddd;
}
tr:hover {
  background: darkgreen;
}
</style>
