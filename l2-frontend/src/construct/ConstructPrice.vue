<template>
  <div class="filters">
    <h4>Прайс</h4>
    <Treeselect
      v-model="selectedPrice"
      :options="priceList.data"
      :clearable="false"
      placeholder="Выберите прайс"
      value-format="object"
      @input="getCurrentCoastResearchesData(); disabled_status()"
    />
    <h4>Исследования</h4>
    <div class="card-no-hover card card-1">
      <input
        v-model="search"
        class="form-control"
        style="padding-left: 1%"
        placeholder="Поиск исследования"
      >
      <table>
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
          v-for="(coastResearch, idx) in filteredRows"
          :key="idx"
          class="tablerow"
        >
          <td
            class="tablerow"
            style="padding-left: 1%"
          >
            {{ coastResearch.research.title }}
          </td>
          <td>
            <input
              v-model="coastResearch.coast"
              :disabled="disabled"
              type="number"
              min="0"
              step="0.01"
              class="text-right form-control"
            >
          </td>
          <td>
            <button
              v-tippy
              :disabled="disabled"
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
          <td
            style="border: 1px solid #dddddd"
          >
            <input
              v-model="coast"
              :disabled="disabled"
              type="number"
              class="text-right form-control"
              min="0"
              step="0.01"
            >
          </td>
          <td>
            <button
              v-tippy
              :disabled="disabled"
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
      disabled: false,
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
      this.coastResearches = await this.$api('/get-current-coast-researches', this.selectedPrice);
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
    disabled_status() {
      this.disabled = this.selectedPrice.status === false;
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
  border-radius: 0;
  border: none;
  background-color: transparent;
  padding: 6px 0;
}
::v-deep .form-control:focus {
  background-color: greenyellow;
}
::v-deep .card {
  margin: 1rem 0;
}
::v-deep .btn {
  margin: auto;
  display: block;
  border-radius: 0;
}
.tablerow {
  border: 1px solid #dddddd;
}
.tablerow:hover {
  background: #4caf50;
}
</style>
