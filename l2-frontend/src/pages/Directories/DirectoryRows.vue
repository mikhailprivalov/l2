<template>
  <div v-frag>
    <template
      v-if="directoryRows"
    >
      <div
        style="max-width: 400px;margin-bottom: 5px;"
        class="input-group"
      >
        <input
          v-model="tmpQ"
          type="text"
          class="form-control"
          placeholder="Поиск"
          :readonly="!!q"
        >
        <div class="input-group-btn">
          <button
            v-if="!q"
            v-tippy
            class="btn btn-blue-nb"
            :disabled="!tmpQ"
            title="Поиск"
            @click="search"
          >
            <span class="fa fa-search" />
          </button>
          <button
            v-else
            v-tippy
            class="btn btn-blue-nb"
            title="Отмена"
            @click="clearSearch"
          >
            <span class="fa fa-times" />
          </button>
        </div>
      </div>
      <table class="table table-bordered table-condensed">
        <thead>
          <tr>
            <th>Название</th>
            <th>Код</th>
            <th
              v-for="(f, fpk) in fields"
              :key="fpk"
            >
              {{ f.title }}
            </th>
            <th v-if="canEdit" />
          </tr>
        </thead>
        <tbody>
          <DirectoryRow
            v-for="r in directoryRows"
            :key="r.pk"
            :row="r"
            :fields="fields"
            :can-edit="canEdit"
          />
        </tbody>
      </table>
      <Paginate
        v-model="page"
        :page-count="pages"
        :page-range="4"
        :margin-pages="2"
        :click-handler="loadPage"
        prev-text="Назад"
        next-text="Вперёд"
        container-class="pagination"
      />
    </template>
  </div>
</template>

<script lang="ts">
import Paginate from 'vuejs-paginate';

import * as actions from '@/store/action-types';

import DirectoryRow from './DirectoryRow.vue';

export default {
  name: 'DirectoryRows',
  components: {
    Paginate,
    DirectoryRow,
  },
  props: {
    pk: {
      type: Number,
      required: true,
    },
    canEdit: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      tmpQ: '',
      q: '',
      directoryRows: null,
      page: 1,
      pages: 1,
      fields: {},
    };
  },
  mounted() {
    this.loadPage(1);
    this.$root.$on('directory-row-editor:saved', () => {
      this.loadPage(this.page);
    });
  },
  methods: {
    search() {
      this.q = this.tmpQ;
      this.loadPage(1);
    },
    clearSearch() {
      this.q = '';
      this.loadPage(1);
    },
    async loadPage(p) {
      await this.$store.dispatch(actions.INC_LOADING);
      const {
        page, pages, fields, rows,
      } = await this.$api('dynamic-directory/rows', this, ['pk', 'q'], { page: p });
      this.page = page;
      this.pages = pages;
      this.fields = fields;
      this.directoryRows = rows;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
};
</script>

<style>
.pagination {
  margin-top: 0 !important;
}
</style>

<style lang="scss" scoped>
  .td-empty {
    text-align: center;
    color: #999;
    font-style: italic;
  }
</style>
