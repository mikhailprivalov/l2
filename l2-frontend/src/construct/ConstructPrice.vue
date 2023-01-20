<template>
  <div>
    <h4>
      Прайс
    </h4>
    <Treeselect
      v-model="selectedPrice"
      :options="prices.data"
      placeholder="Выберите прайс"
      class="select-price"
    />
    <div class="edit-price">
      <table class="table">
        <colgroup>
          <col>
          <col width="120">
          <col width="120">
          <col width="200">
          <col
            v-if="priceIsActive"
            width="100"
          >
        </colgroup>
        <thead>
          <tr>
            <th class="text-center">
              <strong>Название</strong>
            </th>
            <th class="text-center">
              <strong>Дата начала</strong>
            </th>
            <th class="text-center">
              <strong>Дата конца</strong>
            </th>
            <th class="text-center">
              <strong>Компания</strong>
            </th>
            <th v-if="priceIsActive" />
          </tr>
        </thead>
        <tr>
          <td class="border">
            <input
              v-model.trim="priceData.title"
              class="form-control"
              :disabled="!priceIsActive"
            >
          </td>
          <td class="border">
            <input
              v-model="priceData.start"
              type="date"
              class="form-control"
              :disabled="!priceIsActive"
            >
          </td>
          <td class="border">
            <input
              v-model="priceData.end"
              type="date"
              class="form-control"
              :disabled="!priceIsActive"
            >
          </td>
          <td class="border">
            <Treeselect
              v-model="priceData.company"
              :options="companies.data"
              :normalizer="normalizer"
              placeholder="Выберите компанию"
              :disabled="!priceIsActive"
            />
          </td>
          <td
            v-if="priceIsActive"
            class="border"
          >
            <div class="button">
              <button
                v-tippy
                class="btn last btn-blue-nb nbr"
                :title="priceIsSelected ? 'Сохранить прайс' : 'Добавить прайс'"
                :disabled="!priceDataIsFilled"
                @click="updatePrice"
              >
                {{ priceIsSelected ? 'Сохранить' : 'Добавить' }}
              </button>
            </div>
          </td>
        </tr>
      </table>
    </div>
    <h4 v-if="priceIsSelected">
      Исследования
    </h4>
    <div
      v-if="priceIsSelected"
      class="margin-bottom"
    >
      <input
        v-model.trim="search"
        class="form-control search"
        placeholder="Поиск исследования"
      >
    </div>
    <div
      v-if="priceIsSelected"
      class="card-no-hover card card-1"
    >
      <div class="scroll">
        <table class="table">
          <colgroup>
            <col>
            <col width="100">
            <col
              v-if="priceIsActive"
              width="100"
            >
          </colgroup>
          <thead class="sticky">
            <tr class="border-no-top">
              <th
                class="text-center border-right"
              >
                <strong>Название</strong>
              </th>
              <th
                class="text-center border-right"
              >
                <strong>Цена</strong>
              </th>
              <th
                v-if="priceIsActive"
                class="border-right"
              />
            </tr>
          </thead>
          <tr
            v-if="filteredRows.length === 0"
            class="text-center"
          >
            <td
              colspan="3"
              class="border-top"
            >
              Нет данных
            </td>
          </tr>
          <tr
            v-for="(coastResearch) in filteredRows"
            :key="coastResearch.id"
          >
            <VueTippyTd
              class="research border padding-left"
              :text="coastResearch.research.title"
            />
            <td class="border">
              <input
                v-model="coastResearch.coast"
                :disabled="!priceIsActive"
                type="number"
                min="0.01"
                step="0.01"
                class="text-right form-control"
              >
            </td>
            <td
              v-if="priceIsActive"
              class="border"
            >
              <div class="button">
                <button
                  v-tippy
                  class="btn last btn-blue-nb nbr"
                  title="Сохранить цену"
                  @click="updateCoastResearchInPrice(coastResearch)"
                >
                  <i class="fa fa-save" />
                </button>
                <button
                  v-tippy
                  class="btn last btn-blue-nb nbr"
                  title="Удалить исследование"
                  @click="deleteResearchInPrice(coastResearch)"
                >
                  <i class="fa fa-times" />
                </button>
              </div>
            </td>
          </tr>
        </table>
      </div>
    </div>
    <h4 v-if="priceIsActive && priceIsSelected">
      Добавить исследование в прайс
    </h4>
    <div v-if="priceIsActive && priceIsSelected">
      <table>
        <colgroup>
          <col>
          <col width="100">
          <col width="100">
        </colgroup>
        <tr>
          <td class="border">
            <Treeselect
              v-model="selectedResearch"
              :options="researchList.data"
              :disable-branch-nodes="true"
              :append-to-body="true"
              placeholder="Выберите исследование"
            />
          </td>
          <td class="border">
            <input
              v-model="coast"
              type="number"
              class="text-right form-control"
              min="0.01"
              step="0.01"
              placeholder="Цена"
            >
          </td>
          <td class="border">
            <div class="button">
              <button
                v-tippy
                class="btn last btn-blue-nb nbr"
                title="Добавить исследование"
                :disabled="!selectedResearch"
                @click="addResearchInPrice"
              >
                Добавить
              </button>
            </div>
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
      prices: {},
      priceData: {},
      activeStatus: {
        ok: true,
      },
      selectedPrice: null,
      selectedResearch: null,
      coast: '',
      researchList: {},
      search: '',
      coastResearches: [],
      companies: [],
    };
  },
  computed: {
    filteredRows() {
      return this.coastResearches.filter(coastResearch => {
        const research = coastResearch.research.title.toLowerCase();
        const searchTerm = this.search.toLowerCase();

        return research.includes(searchTerm);
      });
    },
    priceIsActive() {
      return this.activeStatus.ok;
    },
    priceIsSelected() {
      return !!this.selectedPrice;
    },
    priceDataIsFilled() {
      return !(!this.priceData.title || !this.priceData.start || !this.priceData.end || !this.priceData.company);
    },
  },
  watch: {
    selectedPrice() {
      if (!this.selectedPrice) {
        this.priceData = {
          title: '',
          start: '',
          end: '',
          company: null,
        };
        this.activeStatus.ok = true;
      } else {
        this.getCoastsResearchesInPrice();
        this.checkPriceHidden();
        this.getPriceData();
      }
    },
  },
  mounted() {
    this.getPrices();
    this.getResearchList();
    this.getCompanies();
  },
  methods: {
    normalizer(node) {
      return {
        id: node.pk,
        label: node.title,
      };
    },
    async getPrices() {
      this.prices = await this.$api('/get-prices');
    },
    async updatePrice() {
      if (!this.priceDataIsFilled) {
        this.$root.$emit('msg', 'error', 'Данные не заполнены');
      } else if (new Date(this.priceData.end) <= new Date(this.priceData.start)) {
        this.$root.$emit('msg', 'error', 'Дата конца раньше даты начала');
      } else if (this.priceIsSelected) {
        await this.$store.dispatch(actions.INC_LOADING);
        const { ok, message } = await this.$api('update-price', {
          id: this.selectedPrice,
          title: this.priceData.title,
          start: this.priceData.start,
          end: this.priceData.end,
          company: this.priceData.company,
        });
        await this.$store.dispatch(actions.DEC_LOADING);
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Прайс обновлен');
          await this.getPrices();
        } else {
          this.$root.$emit('msg', 'error', message);
        }
      } else {
        await this.$store.dispatch(actions.INC_LOADING);
        const { ok, message } = await this.$api('update-price', {
          id: -1,
          title: this.priceData.title,
          start: this.priceData.start,
          end: this.priceData.end,
          company: this.priceData.company,
        });
        await this.$store.dispatch(actions.DEC_LOADING);
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Прайс добавлен');
          await this.getPrices();
          this.priceData = {
            title: '',
            start: '',
            end: '',
            company: null,
          };
        } else {
          this.$root.$emit('msg', 'error', message);
        }
      }
    },
    async checkPriceHidden() {
      if (this.selectedPrice) {
        this.activeStatus = await this.$api('/check-price-active', { id: this.selectedPrice });
      }
    },
    async getPriceData() {
      const price = await this.$api('/get-price-data', { id: this.selectedPrice });
      this.priceData = price.data;
    },
    async getResearchList() {
      this.researchList = await this.$api('/get-research-list');
    },
    async getCompanies() {
      this.companies = await this.$api('/get-companies');
    },
    async getCoastsResearchesInPrice() {
      const coast = await this.$api('/get-coasts-researches-in-price', { id: this.selectedPrice });
      this.coastResearches = coast.data;
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
        await this.getCoastsResearchesInPrice();
      } else {
        this.$root.$emit('msg', 'error', message);
      }
    },
    async addResearchInPrice() {
      if (!(this.selectedResearch && this.coast && this.selectedPrice)) {
        this.$root.$emit('msg', 'error', 'Данные не заполнены');
      } else if (this.coastResearches.find((i) => i.research.id === this.selectedResearch)) {
        this.$root.$emit('msg', 'error', 'Исследование уже есть в прайсе');
      } else if (Number(this.coast) <= 0) {
        this.$root.$emit('msg', 'error', 'Неверная цена');
      } else {
        await this.$store.dispatch(actions.INC_LOADING);
        const { ok, message } = await this.$api('/add-research-in-price', {
          priceId: this.selectedPrice,
          researchId: this.selectedResearch,
          coast: this.coast,
        });
        await this.$store.dispatch(actions.DEC_LOADING);
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Исследование добавлено');
          await this.getCoastsResearchesInPrice();
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
  padding: 6px 6px;
  background-color: transparent;
}
::v-deep .card {
  margin: 0;
}
.table {
  margin-bottom: 0;
  table-layout: fixed;
}
.margin-bottom {
  margin-bottom: 20px;
}
.border {
  border: 1px solid #ddd;
}
.select-price {
  border: 1px solid #ddd;
  border-radius: 5px;
}
::v-deep .vue-treeselect__control {
  border: 0;
}
.edit-price {
  margin: 20px 0;
}
.scroll {
  min-height: 106px;
  max-height: calc(100vh - 600px);
  overflow-y: auto;
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
.research {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.border-right {
  border-right: 1px solid #ddd;
}
.border-top {
  border-top: 1px solid #ddd;
}
.border-no-top {
  border-right: 1px solid #ddd;
  border-left: 1px solid #ddd;
  border-bottom: 1px solid #ddd;
}
.padding-left {
  padding-left: 6px;
}
.search {
  border: 1px solid #ddd;
  border-radius: 5px;
  padding-left: 6px;
  background-color: white;
}
.button {
  width: 100%;
  display: flex;
  flex-wrap: nowrap;
  flex-direction: row;
  justify-content: stretch;
}
  .btn {
    align-self: stretch;
    flex: 1;
    padding: 7px 0;
  }
</style>
