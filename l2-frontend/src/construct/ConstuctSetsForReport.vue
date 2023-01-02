<template>
  <div>
    <h4>Набор</h4>
    <Treeselect
      v-model="currentSet"
      :options="sets.data"
      :clearable="false"
      placeholder="Набор"
    />
    <h4 v-if="setIsSelected">
      Исследования
    </h4>
    <div v-if="setIsSelected">
      <input
        v-model.trim="search"
        class="form-control search"
        placeholder="Поиск"
      >
    </div>
    <div
      v-if="setIsSelected"
      class="card-no-hover card card-1"
    >
      <div class="scroll">
        <table class="table">
          <colgroup>
            <col>
            <col width="100">
          </colgroup>
          <thead class="sticky">
            <tr>
              <th
                class="text-center"
              >
                <strong>Название</strong>
              </th>
              <th />
            </tr>
          </thead>
          <tr
            v-if="filteredResearches.length === 0"
            class="text-center"
          >
            <td
              colspan="2"
            >
              Нет данных
            </td>
          </tr>
          <tr
            v-for="(i) in filteredResearches"
            :key="i.id"
            class="border"
          >
            <VueTippyTd
              class="research border padding-left"
              :text="i.research.label"
            />
            <td class="border">
              <div class="button">
                <button
                  v-tippy
                  class="btn last btn-blue-nb nbr"
                  title="Удалить из набора"
                >
                  <i class="fa fa-times" />
                </button>
              </div>
            </td>
          </tr>
        </table>
      </div>
    </div>
    <h4 v-if="setIsSelected">
      Добавить исследование в набор
    </h4>
    <div v-if="setIsSelected">
      <table
        class="table-bordered"
      >
        <colgroup>
          <col>
          <col width="100">
        </colgroup>
        <tr>
          <td>
            <Treeselect
              v-model="currentResearch"
              :options="researches.data"
              :disable-branch-nodes="true"
              :append-to-body="true"
              placeholder="Исследование"
            />
          </td>
          <td>
            <div class="button">
              <button
                v-tippy
                class="btn last btn-blue-nb nbr"
                title="Добавить исследование"
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
import VueTippyTd from '@/construct/VueTippyTd.vue';

export default {
  name: 'ConstuctSetsForReport',
  components: { Treeselect, VueTippyTd },
  data() {
    return {
      currentSet: null,
      currentResearch: null,
      sets: [],
      search: '',
      researchesInSet: [],
      researches: [],
    };
  },
  computed: {
    filteredResearches() {
      return this.researchesInSet.filter(i => {
        const title = i.research.label.toLowerCase();
        const searchTerm = this.search.toLowerCase();

        return title.includes(searchTerm);
      });
    },
    setIsSelected() {
      return !!this.currentSet;
    },
  },
  watch: {
    currentSet() {
      this.getResearchesInSet();
    },
  },
  mounted() {
    this.getSets();
    this.getResearches();
  },
  methods: {
    async getSets() {
      this.sets = await this.$api('/get-sets');
    },
    async getResearches() {
      this.researches = await this.$api('/get-research-list');
    },
    async getResearchesInSet() {
      const researches = await this.$api('/get-researches-in-set', this.currentSet);
      this.researchesInSet = researches.data;
    },
  },
};
</script>

<style scoped>
::v-deep .card {
  margin: 1rem 0;
}
.table {
  margin-bottom: 0;
  table-layout: fixed;
}
::v-deep .form-control {
  border: none;
  padding: 6px 0;
  background-color: transparent;
}
.search {
  border: 1px solid #ddd;
  border-radius: 5px;
  padding-left: 6px;
  background-color: white;
}
.scroll {
  min-height: 106px;
  max-height: calc(100vh - 400px);
  overflow-y: auto;
}
.border {
  border: 1px solid #ddd;
  border-radius: 0;
}
.research {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.padding-left {
  padding-left: 6px;
}
.sticky {
  position: sticky;
  top: 0;
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
