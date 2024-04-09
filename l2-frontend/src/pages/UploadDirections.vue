<template>
  <div class="root">
    <div class="top-block row">
      <div class="col-xs-6">
        <div class="radio-wrapper">
          <RadioFieldById
            v-model="filters.mode"
            :variants="modesAvailable"
            :disabled="disabledByNumber"
          />
        </div>
        <treeselect
          v-if="filters.mode === 'department'"
          v-model="filters.department"
          class="treeselect-wide treeselect-34px"
          :multiple="false"
          :disable-branch-nodes="true"
          :options="deps"
          :clearable="false"
          placeholder="Подразделение не выбано"
          :disabled="disabledByNumber"
        />
      </div>
      <div class="col-xs-6">
        <div class="radio-wrapper">
          <RadioFieldById
            v-model="filters.status"
            :variants="STATUSES"
            :disabled="disabledByNumber"
          />
        </div>
        <div class="row">
          <div class="col-xs-6">
            <DateFieldNav2
              v-model="filters.date"
              w="100%"
              :brn="false"
              :disabled="disabledByNumber"
            />
          </div>
          <div class="col-xs-6">
            <input
              v-model.trim="filters.number"
              type="text"
              class="form-control"
              placeholder="номер направления"
            >
          </div>
        </div>
      </div>
    </div>

    <button
      class="top-button btn btn-blue-nb2 btn-block"
      type="button"
      @click="load(null)"
    >
      <i class="fa fa-search" /> Поиск
    </button>

    <div
      v-if="!loaded || error"
      class="not-loaded"
    >
      Данные не загружены
      <br>
      <span class="status-error">{{ message }}</span>
    </div>
    <div
      v-else
      class="data"
    >
      <div>
        <button
          class="btn btn-blue-nb float-right"
          @click="sendDirection"
        >
          Отправить в ЕЦП
        </button>
        <paginate
          v-model="page"
          :page-count="pages"
          :page-range="4"
          :margin-pages="2"
          :click-handler="load"
          prev-text="Назад"
          next-text="Вперёд"
          container-class="pagination"
        />
      </div>
      <table class="table table-bordered table-condensed">
        <colgroup>
          <col style="width: 190px">
          <col>
          <col>
          <col style="width: 160px">
          <col style="width: 25px">
        </colgroup>
        <thead>
          <tr>
            <th>
              № направления
            </th>
            <th>
              Подтверждено
            </th>
            <th>
              Услуги
            </th>
            <th>
              Статус
            </th>
            <td
              :key="`check_${globalCheckStatus}`"
              class="x-cell"
            >
              <label
                @click.prevent="toggleGlobalCheck"
              >
                <input
                  type="checkbox"
                  :checked="globalCheckStatus"
                >
              </label>
            </td>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="r in rows"
            :key="r.pk"
          >
            <td>
              {{ r.pk }}
              <span
                v-if="!r.hasSnils"
                class="status-error"
              > <i class="fa fa-exclamation-triangle" />СНИЛС</span>
            </td>
            <td>{{ r.confirmedAt }}, {{ r.docConfirmation }}</td>
            <td>
              {{ r.services.join('; ') }}
            </td>
            <td class="eds-td cl-td">
              <div />
              <div
                class="m-error uploading-status"
              >
                {{ r.ecpDirectionNumber}}
              </div>
            </td>
            <td class="x-cell">
              <label>
                <input
                  v-model="r.checked"
                  type="checkbox"
                >
              </label>
            </td>
          </tr>
        </tbody>
      </table>
      <div>
        <button
          class="btn btn-blue-nb float-right"
          style="padding-left: 10px"
          @click="sendDirection"
        >
          Отправить в ЕЦП
        </button>
        <paginate
          v-model="page"
          :page-count="pages"
          :page-range="4"
          :margin-pages="2"
          :click-handler="load"
          prev-text="Назад"
          next-text="Вперёд"
          container-class="pagination"
        />
      </div>
      <div class="founded">
        Найдено записей: <strong>{{ total }}</strong>
      </div>
    </div>
  </div>
</template>

<script lang="ts">

import moment from 'moment';
import Vue from 'vue';
import Component from 'vue-class-component';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import Paginate from 'vuejs-paginate';

import * as actions from '@/store/action-types';
import usersPoint from '@/api/user-point';
import RadioFieldById from '@/fields/RadioFieldById.vue';
import DateFieldNav2 from '@/fields/DateFieldNav2.vue';
import EDSDirection from '@/ui-cards/EDSDirection.vue';

const MODES = [
  { id: 'department', label: 'Подразделение' },
  { id: 'my', label: 'Мои документы' },
];

const STATUSES = [
  { id: 'need', label: 'Требуют отправки' },
  { id: 'ok-role', label: 'Отправлены' },
];

@Component({
  components: {
    Treeselect,
    RadioFieldById,
    DateFieldNav2,
    Paginate,
    EDSDirection,
  },
  data() {
    return {
      checked: false,
      filters: {
        mode: null,
        department: null,
        status: STATUSES[0].id,
        number: '',
        date: moment().format('YYYY-MM-DD'),
      },
      MODES,
      STATUSES,
      users: [],
      page: 1,
      pages: 0,
      total: 0,
      loaded: false,
      error: false,
      message: '',
      rows: [],
    };
  },
  mounted() {
    this.loadUsers();
  },
  watch: {
    modesAvailable: {
      immediate: true,
      handler() {
        if (!this.modesAvailable.find(m => m.id === this.filters.mode)) {
          this.filters.mode = this.modesAvailable[0].id;
        }
      },
    },
  },
})
export default class EDS extends Vue {
  checked: boolean;

  filters: any;

  MODES: any[];

  users: any[];

  page: number;

  pages: number;

  total: number;

  loaded: boolean;

  error: boolean;

  message: string;

  rows: any[];

  get accessToMO() {
    return (this.$store.getters.user_data.groups || []).includes('ЭЦП Медицинской организации');
  }

  get modesAvailable() {
    return this.MODES.filter(m => m.id !== 'mo' || this.accessToMO);
  }

  get disabledByNumber() {
    return Boolean(this.filters.number);
  }

  get deps() {
    return [
      ...this.users.map(d => ({ id: d.id, label: d.label })),
      { id: -1, label: 'Все отделения' },
    ];
  }

  get globalCheckStatus() {
    return this.rows.every(r => r.checked);
  }

  async loadUsers() {
    await this.$store.dispatch(actions.INC_LOADING);
    const { users } = await usersPoint.loadUsersByGroup({ group: '*' });
    this.users = users;
    this.filters.department = this.$store.getters.user_data?.department?.pk || null;
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  async load(pageToLoad) {
    if (pageToLoad !== null) {
      this.page = pageToLoad;
    } else {
      this.page = 1;
    }
    await this.$store.dispatch(actions.INC_LOADING);
    const {
      rows, page, pages, total, error, message,
    } = await this.$api('/directions/results/need-send-ecp', this, ['filters', 'page']);
    this.rows = rows.map(r => ({ ...r, checked: false }));
    this.page = page;
    this.pages = pages;
    this.total = total;
    this.error = error;
    this.message = message;
    await this.$store.dispatch(actions.DEC_LOADING);
    this.loaded = true;
  }

  toggleGlobalCheck() {
    const newStatus = !this.globalCheckStatus;
    this.rows = this.rows.map(r => ({ ...r, checked: newStatus }));
  }

  async sendDirection() {
    const dataSend = this.rows.filter(d => d.checked).map(d => d.pk);
    console.log(dataSend);
    const result = await this.$api('/directions/results/send-ecp', { directions: dataSend });
  }
}
</script>

<style lang="scss" scoped>
.eds-preloader {
  padding: 20px;
  text-align: center;
}

.status {
  &-error {
    color: #cf3a24;
  }

  &-ok {
    color: #049372;
  }
}

.cert-info {
  font-size: 12px;
}

.eds-status {
  padding: 5px 0;
}

.top-block {
  margin: 0 0 10px 0;
  padding: 5px 0;
  border-radius: 4px;
  box-shadow: 0 0 5px rgba(0, 0, 0, 0.4);
  background: #fff;

  &.row,
  &.eds-preloader {
    min-height: 44px;
  }
}

.root {
  margin: -10px auto 0 auto;
  max-width: 1200px;
  padding: 0 10px;
}

.radio-wrapper {
  margin-bottom: 5px;
}

.top-button {
  margin-bottom: 15px;
}

.not-loaded {
  text-align: center;
  color: grey;
}

.data {
  padding: 0 20px;
}

.founded {
  text-align: center;
  padding: 5px;
  margin-top: -5px;
}

.tr-ok {
  background-color: rgba(#049372, 0.1);
}

.tr-error {
  background-color: rgba(#930425, 0.1);
}

.m-ok {
  font-weight: bold;
  color: #049372;
}

.m-error {
  font-weight: bold;
  color: #930425;
}

.eds-td > div {
  display: flex;
  flex-direction: row;
  margin-left: -5px;
}

.signing {
  &-root {
    position: fixed;
    width: 100%;
    height: 100%;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(1px);
    z-index: 100000;
  }

  &-inner {
    margin: 0 auto;
    max-width: 1200px;
    width: 100%;
    padding: 0 10px;
    height: 100%;
    padding: 50px 0;
    overflow-y: auto;

    .btn {
      width: auto !important;
      margin: 10px auto 20px auto !important;
      display: block;
    }

    .table {
      background: #fff;
    }
  }

  &-header {
    text-align: center;
    margin-bottom: 10px;
    color: #fff;
    font-size: 20px;
    font-weight: bold;
  }
}

.uploading-status {
  margin-left: 0 !important;
  text-align: center;
  display: block !important;
}
</style>

<style>
.pagination {
  margin-top: 0 !important;
}
</style>
