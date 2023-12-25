<template>
  <div class="root">
    <div class="schedule-control">
      <div class="row">
        <div
          class="col-xs-4"
          style="padding-right: 0"
        >
          <Treeselect
            :key="`resource-treeselect-${loaded}`"
            v-model="resourceSelected"
            :multiple="false"
            class="treeselect-wide treeselect-nbr treeselect-34px"
            :async="true"
            :append-to-body="true"
            :disable-branch-nodes="true"
            :clearable="true"
            :z-index="5001"
            placeholder="Ресурс"
            :load-options="loadOptions"
            :default-options="defaultResourceOptions"
            loading-text="Загрузка"
            no-results-text="Не найдено"
            search-prompt-text="Начните писать для поиска"
            :cache-options="true"
            open-direction="bottom"
            :open-on-focus="true"
            :default-expand-level="1"
          />
        </div>
        <div
          class="col-xs-2"
          style="padding-left: 0; padding-right: 0"
        >
          <select
            v-model="mode"
            class="form-control"
          >
            <option value="natural">
              часовой вид
            </option>
            <option value="list">
              списочный вид
            </option>
          </select>
        </div>
        <div
          class="col-xs-1"
          style="padding-left: 0"
        >
          <select
            v-model.number="displayDays"
            class="form-control"
          >
            <option :value="7">
              7 дней
            </option>
            <option :value="14">
              14 дней
            </option>
            <option :value="21">
              21 день
            </option>
          </select>
        </div>
        <div
          v-if="hasResource"
          class="col-xs-5 text-right no-wrap"
        >
          <label v-if="canChangeSchedule"> <input
            v-model="editingMode"
            type="checkbox"
          > редактирование </label>
          <button
            class="btn btn-blue-nb nbr"
            @click="refresh"
          >
            <i class="fa fa-refresh" />
          </button>
          <button
            class="btn btn-blue-nb nbr"
            @click="previousDate"
          >
            <i class="fa fa-arrow-left" /> Назад
          </button>
          <button
            class="btn btn-blue-nb nbr"
            @click="nextDate"
          >
            Вперёд <i class="fa fa-arrow-right" />
          </button>
        </div>
      </div>
    </div>
    <div class="days-wrapper">
      <template v-if="hasResource">
        <DaysGridNatural
          :mode="mode"
          :days="days"
          :start-time="startTime"
          :end-time="endTime"
          :is-editing="editingMode"
          :resource="resourceSelected"
          :services="services"
        />
      </template>
      <div
        v-else
        class="days-message"
      >
        не выбран ресурс
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import Treeselect, { ASYNC_SEARCH } from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import Vue from 'vue';
import Component from 'vue-class-component';
import moment, { Moment } from 'moment';

import * as actions from '@/store/action-types';
import UrlData from '@/UrlData';

import DaysGridNatural from './DaysGridNatural.vue';

@Component({
  components: {
    DaysGridNatural,
    Treeselect,
  },
  data() {
    return {
      date: moment().startOf('isoWeek'),
      days: [],
      services: [],
      startTime: null,
      endTime: null,
      resourceSelected: null,
      editingMode: false,
      displayDays: 7,
      mode: 'natural',
      defaultResourceOptions: [],
      loaded: false,
      userGroups: [],
      canChangeSchedule: false,
    };
  },
  watch: {
    async resourceSelected() {
      this.canChangeSchedule = false;
      await this.getScheduleWeek();
      const { ok } = await this.$api('schedule/schedule-access', { resourcePk: this.resourceSelected });
      this.canChangeSchedule = !!ok;

      UrlData.set({ resourceSelected: this.resourceSelected });
    },
    displayDays() {
      this.getScheduleWeek();
    },
  },
  async mounted() {
    this.$root.$on('reload-slots', () => this.getScheduleWeek());
    await this.loadCurrentUserInfo();
    this.loaded = true;
  },
})
export default class Schedule extends Vue {
  date: Moment;

  days: any[];

  startTime: string | null;

  endTime: string | null;

  resourceSelected: any;

  defaultResourceOptions: any[];

  displayDays: number;

  userGroups: any[];

  canChangeSchedule: boolean;

  services: any[];

  async loadCurrentUserInfo() {
    const { pk, options } = await this.$api('/schedule/get-first-user-resource');
    if (pk) {
      this.resourceSelected = pk;
    }

    if (options) {
      this.defaultResourceOptions = options;
    }

    const urlPk = UrlData.getKey('resourceSelected');

    if (urlPk !== undefined && urlPk !== null && options.find(({ children }) => children.find(({ id }) => id === urlPk))) {
      this.resourceSelected = urlPk;
    }

    this.userGroups = this.$store.getters.user_data.groups || [];
  }

  async getScheduleWeek() {
    if (!this.resourceSelected) {
      return;
    }
    await this.$store.dispatch(actions.INC_LOADING);
    const {
      days, startTime, endTime, services,
    } = await this.$api('/schedule/days', this, ['displayDays'], {
      date: this.date.format('YYYY-MM-DD'),
      resource: this.resourceSelected,
    });

    this.days = days;
    this.startTime = startTime;
    this.endTime = endTime;
    this.services = services;
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  async nextDate() {
    this.date = moment(this.date).add(this.displayDays, 'days');
    await this.getScheduleWeek();
  }

  async previousDate() {
    this.date = moment(this.date).subtract(this.displayDays, 'days');
    await this.getScheduleWeek();
  }

  refresh() {
    this.getScheduleWeek();
  }

  async loadOptions({ action, searchQuery, callback }) {
    if (action === ASYNC_SEARCH) {
      const { rows } = await this.$api(`/schedule/search-resource?query=${searchQuery}`);
      callback(null, rows);
    }
  }

  get hasResource() {
    return !!this.resourceSelected;
  }
}
</script>

<style lang="scss" scoped>
.schedule-control {
  position: absolute;
  top: 36px;
  left: 0;
  right: 0;
  height: 34px;
  overflow-x: hidden;
}

.days-wrapper {
  position: absolute;
  top: 70px;
  left: 0;
  right: 0;
  bottom: 0;
  overflow-x: hidden;
  overflow-y: auto;
}

.days-message {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.no-wrap {
  white-space: nowrap;
}
</style>
