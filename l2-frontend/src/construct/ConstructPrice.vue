<template>
  <div>
    <h4>
      Прайс
    </h4>
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
    <div v-if="selectedPrice.id !== -1">
      <input
        v-model="search"
        class="form-control search"
        placeholder="Поиск исследования"
      >
    </div>
    <div
      v-if="selectedPrice.id !== -1"
      class="card-no-hover card card-1"
    >
      <div class="scroll">
        <table class="table">
          <colgroup>
            <col>
            <col width="100">
            <col
              v-if="selectedPrice.status === true"
              width="39"
            >
            <col
              v-if="selectedPrice.status === true"
              width="35.8"
            >
          </colgroup>
          <thead class="sticky">
            <tr>
              <th
                class="text-center"
                style="border-right: 1px solid #ddd; border-left: 1px solid #ddd"
              >
                <strong>Название</strong>
              </th>
              <th
                class="text-center"
                style="border-right: 1px solid #ddd"
              >
                <strong>Цена</strong>
              </th>
              <th v-if="selectedPrice.status === true" />
              <th
                v-if="selectedPrice.status === true"
                style="border-right: 1px solid #ddd"
              />
            </tr>
          </thead>
          <tr
            v-if="filteredRows.length === 0"
            class="text-center"
          >
            <td
              colspan="4"
              style="border-top: 1px solid #ddd"
            >
              Нет данных
            </td>
          </tr>
          <tr
            v-for="(coastResearch) in filteredRows"
            :key="coastResearch.id"
            class="tablerow"
          >
            <VueTippyTd
              class="research tablerow"
              style="padding-left: 6px"
              :text="coastResearch.research.title"
            />
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
            <td
              v-if="selectedPrice.status === true"
              class="tablerow"
            >
              <button
                v-tippy
                class="btn last btn-blue-nb nbr"
                title="Сохранить цену"
                @click="updateCoastResearchInPrice(coastResearch)"
              >
                <i class="fa fa-save" />
              </button>
            </td>
            <td v-if="selectedPrice.status === true">
              <button
                v-tippy
                class="btn last btn-blue-nb nbr"
                title="Удалить исследование"
                @click="deleteResearchInPrice(coastResearch)"
              >
                <i class="fa fa-times" />
              </button>
            </td>
          </tr>
        </table>
      </div>
    </div>
    <h4 v-if="selectedPrice.status === true">
      Добавить исследование в прайс
    </h4>
    <div v-if="selectedPrice.status === true">
      <table
        class="table-bordered"
      >
        <colgroup>
          <col>
          <col width="99">
          <col width="92">
        </colgroup>
        <tr>
          <td>
            <Treeselect
              v-model="selectedResearch"
              :options="researchList.data"
              :disable-branch-nodes="true"
              :append-to-body="true"
              placeholder="Выберите исследование"
            />
          </td>
          <td>
            <input
              v-model="coast"
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
              class="btn last btn-blue-nb nbr"
              style="padding: 7px 12px;"
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
import VueTippyTd from '@/construct/VueTippyTd.vue';

export default {
  name: 'ConstructPrice',
  components: { VueTippyTd, Treeselect },
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
      try {
        await this.$dialog.confirm('Подтвердите удаление исследования из прайса');
      } catch (_) {
        return;
      }
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, message } = await this.$api('/delete-research-in-price', { coastResearchId: coastResearch.id });
      await this.$store.dispatch(actions.DEC_LOADING);
      if (ok) {
        this.$root.$emit('msg', 'ok', 'Исследование удалено');
        await this.getCurrentCoastResearchesInPrice();
      } else {
        this.$root.$emit('msg', 'error', message);
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
.tablerow {
  border: 1px solid #ddd;
  border-radius: 0;
}
.scroll {
  min-height: 106px;
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
.research {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.search {
  border: 1px solid #ddd;
  border-radius: 5px;
  padding-left: 6px;
  background-color: white;
}
</style>
