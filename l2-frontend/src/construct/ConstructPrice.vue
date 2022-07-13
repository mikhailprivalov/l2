<template>
  <div class="filters">
    <div class="card-no-hover card card-1 card-bottom opac">
      <Treeselect
        v-model="selectedPrice"
        :options="priceList.data"
        placeholder="Выберите прайс"
        @input="getCurrentCoastResearchesData"
      />
      <br>
      <table>
        <colgroup>
          <col width="60%">
          <col width="30%">
          <col width="10%">
        </colgroup>
        <tr
          v-for="(coastResearch, idx) in coastResearches.data"
          :key="idx"
        >
          <td class="border-cell">
            <input
              disabled
              :value="coastResearch.research.title"
              class="form-control"
            >
          </td>
          <td class="border-cell">
            <input
              v-model="coastResearch.coast"
              type="number"
              class="text-center form-control"
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
        <br>
        <tr>
          <td>
            <Treeselect
              v-model="selectedResearch"
              :options="researchList.data"
              placeholder="Выберите исследование"
            />
          </td>
          <td>
            <input
              v-model="coast"
              type="number"
              class="text-center form-control"
            >
          </td>
          <td>
            <button
              v-tippy
              class="btn btn-blue-nb"
              title="Добавить исследование"
              @click="updateResearchListInPrice"
            >
              <i class="glyphicon glyphicon-plus" />
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
      coastResearches: [],
    };
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

<style scoped lang="scss">
.filters {
  padding: 10px;
  margin: 10px 8%;
}
.card-bottom {
  margin-bottom: 5%;
}
::v-deep .form-control {
  background-color: #fff;
  border-radius: 0;
}
//::v-deep .form-control:hover {
//  background: red;
//}
::v-deep .btn {
  margin: auto;
  display: block;
  border-radius: 0;
}
.no-first-border-top {
  border-top: none;
  border-bottom: none;
}
.border-cell {
  border: 1px solid #dddddd;
}
</style>
