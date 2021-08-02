<template>
  <div class="table-root">
    <div class="inner" ref="scroll">
      <div class="filters">
        <treeselect
          :multiple="true"
          :disable-branch-nodes="true"
          :options="monitorings"
          placeholder="Все мониторинги"
          v-model="filterResearches"
        />
      </div>
      <table class="table table-bordered table-condensed table-sm-pd layout">
        <colgroup>
          <col style="width: 80px" />
          <col />
          <col />
          <col style="width: 150px" />
          <col />
          <col style="width: 140px" />
          <col style="width: 40px" />
        </colgroup>
        <thead>
          <tr>
            <th>№</th>
            <th>Название</th>
            <th>Параметры</th>
            <th>Последнее действие</th>
            <th>Автор</th>
            <th>Статус</th>
            <th class="text-center">
              <a class="a-under" href="#" @click.prevent="reload()" title="Перезагрузить список" v-tippy>
                <i class="fa fa-refresh"></i>
              </a>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rows" :key="r.pk" :class="[r.isSaved && 'row-saved', r.isConfirmed && 'row-confirmed']">
            <td>{{ r.pk }}</td>
            <td>{{ r.title }}</td>
            <td>
              <ul>
                <li v-for="(p, i) in r.params" :key="i">
                  <strong v-if="p.title">{{ p.title }}:</strong>
                  <span class="empty-v" v-if="!p.value">пусто</span>
                  <span v-else>{{ p.value }}</span>
                </li>
              </ul>
            </td>
            <td>{{ r.lastActionAt }}</td>
            <td>{{ r.author }}</td>
            <th v-if="r.isConfirmed">подтверждено</th>
            <th v-else-if="r.isSaved">сохранено</th>
            <th v-else>не сохранено</th>
            <td class="cl-td">
              <button class="btn btn-blue-nb btn-sm btn-block" @click="openForm(r.pk)" title="Открыть форму" v-tippy>
                <i class="fas fa-eye " v-if="r.isConfirmed"></i>
                <i class="fa fa-pencil" v-else></i>
              </button>
            </td>
          </tr>
          <tr v-if="nextOffset !== null">
            <td class="text-center" colspan="7">
              <button class="btn btn-blue-nb btn-sm" @click="loadNext()" ref="loadButton">
                <span class="hidden-spinner"><i class="fa fa-spinner"></i></span>
                Загрузить ещё
                <span :class="!listLoading && 'hidden-spinner'" class="loader"><i class="fa fa-spinner"></i></span>
              </button>
            </td>
          </tr>
          <tr v-if="inited">
            <td class="text-center" colspan="7">показано {{ rows.length }} из {{ total | pluralRecords }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import { mapGetters } from 'vuex';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import * as actions from '@/store/action-types';
import api from '@/api';

interface Param {
  title: string;
  value: string;
}

interface Row {
  pk: number;
  title: string;
  lastActionAt: string;
  author: string;
  isSaved: boolean;
  isConfirmed: boolean;
  params: Param[];
}

@Component({
  components: {
    Treeselect,
  },
  data() {
    return {
      rows: [],
      nextOffset: 0,
      total: 0,
      listLoading: false,
      inited: false,
      filterResearches: [],
    };
  },
  mounted() {
    this.loadNext();
    this.$root.$on('embedded-form:hide', pk => this.reloadPk(pk));
    this.$root.$on('embedded-form:open', () => this.reload());
  },
  computed: {
    ...mapGetters(['researches']),
    monitorings() {
      return (this.researches['-12'] || []).map(r => ({ id: r.pk, label: r.title }));
    },
  },
  watch: {
    filterResearches: {
      handler() {
        this.reload();
      },
      deep: true,
    },
  },
})
export default class MonitoringHistoryViewer extends Vue {
  rows: Row[];

  nextOffset: number;

  total: number;

  listLoading: boolean;

  inited: boolean;

  researches: any;

  monitorings: any;

  filterResearches: any;

  clear() {
    this.rows = [];
    this.nextOffset = 0;
  }

  async reload() {
    this.inited = false;
    this.nextOffset = 0;
    await this.loadNext(true);
    this.scrollToTop();
  }

  scrollToTop() {
    setTimeout(() => {
      if (this.$refs.scroll) {
        window.$(this.$refs.scroll).scrollTop(0);
      }
    }, 0);
  }

  async reloadPk(pk) {
    await this.$store.dispatch(actions.INC_LOADING);
    const { rows: [data] = [] } = await api('/monitorings/history', { pk });
    if (data) {
      this.rows = this.rows.map(r => (r.pk === pk ? data : r));
    }
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  async loadNext(replace = false) {
    this.listLoading = true;
    await this.$store.dispatch(actions.INC_LOADING);
    const { rows, nextOffset, totalCount } = await api('/monitorings/history', {
      offset: this.nextOffset,
      filterResearches: this.filterResearches,
    });
    this.rows = replace ? rows : [...this.rows, ...rows];
    this.nextOffset = nextOffset;
    this.total = totalCount;
    await this.$store.dispatch(actions.DEC_LOADING);
    this.listLoading = false;
    this.inited = true;
    if (this.$refs.loadButton) {
      window.$(this.$refs.loadButton).blur();
    }
  }

  openForm(pk) {
    this.$root.$emit('embedded-form:open', pk);
  }
}
</script>

<style lang="scss" scoped>
.layout {
  table-layout: fixed;
  font-size: 12px;
}

.empty-v {
  opacity: 0.8;
}

.table-root {
  height: 100%;
  width: 100%;
  overflow-y: auto;

  table {
    thead th {
      position: sticky;
      top: -1px;
      background: #fff;
      box-shadow: 0 1px 1px rgba(0, 0, 0, 0.2);
      z-index: 11;
    }

    ul {
      padding-left: 20px;
    }
  }
}

.inner {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow-y: auto;
}

.hidden-spinner {
  opacity: 0;
  display: inline-block;
}

.loader {
  display: inline-block;
  animation: rotating 1.5s linear infinite;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.row-saved {
  background: #fcfbe3;
}

.row-confirmed {
  background: #e3fce8;
}
</style>
