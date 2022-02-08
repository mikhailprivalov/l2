<template>
  <div class="root">
    <div class="schedule-control">
      <div class="row">
        <div class="col-xs-4" style="padding-right: 0">
          <Treeselect
            :multiple="false"
            class="treeselect-wide treeselect-nbr treeselect-34px"
            :async="true"
            :append-to-body="true"
            :disable-branch-nodes="true"
            :clearable="true"
            v-model="resourceSelected"
            :zIndex="5001"
            placeholder="Ресурс"
            :load-options="loadOptions"
            :default-options="defaultResourceOptions"
            loadingText="Загрузка"
            noResultsText="Не найдено"
            searchPromptText="Начните писать для поиска"
            :cache-options="true"
            openDirection="bottom"
            :openOnFocus="true"
            :default-expand-level="1"
            :key="`resource-treeselect-${loaded}`"
          />
        </div>
        <div class="col-xs-2" style="padding-left: 0; padding-right: 0">
          <select v-model="mode" class="form-control">
            <option value="natural">часовой вид</option>
            <option value="list">списочный вид</option>
          </select>
        </div>
        <div class="col-xs-1" style="padding-left: 0">
          <select v-model.number="displayDays" class="form-control">
            <option :value="7">7 дней</option>
            <option :value="14">14 дней</option>
            <option :value="21">21 день</option>
          </select>
        </div>
        <div class="col-xs-5 text-right" v-if="hasResource">
          <label> <input type="checkbox" v-model="editingMode" /> режим редактирования </label>
          <button class="btn btn-blue-nb nbr" @click="previousDate"><i class="fa fa-arrow-left"></i> Назад</button>
          <button class="btn btn-blue-nb nbr" @click="nextDate">Вперёд <i class="fa fa-arrow-right"></i></button>
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
        />
      </template>
      <div class="days-message" v-else>не выбран ресурс</div>
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
      startTime: null,
      endTime: null,
      resourceSelected: null,
      editingMode: false,
      displayDays: 7,
      mode: 'natural',
      defaultResourceOptions: [],
      loaded: false,
    };
  },
  watch: {
    resourceSelected() {
      this.getScheduleWeek();
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

  async loadCurrentUserInfo() {
    const { pk, title, options } = await this.$api('/schedule/get-first-user-resource');
    if (pk) {
      this.resourceSelected = pk;
    }

    if (options) {
      this.defaultResourceOptions = options;
    }
  }

  async getScheduleWeek() {
    if (!this.resourceSelected) {
      return;
    }
    await this.$store.dispatch(actions.INC_LOADING);
    const { days, startTime, endTime } = await this.$api('/schedule/days', this, ['displayDays'], {
      date: this.date.format('YYYY-MM-DD'),
      resource: this.resourceSelected,
    });

    this.days = days;
    this.startTime = startTime;
    this.endTime = endTime;
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  async nextDate() {
    this.date = moment(this.date).add(7, 'weeks');
    await this.getScheduleWeek();
  }

  async previousDate() {
    this.date = moment(this.date).subtract(7, 'weeks');
    await this.getScheduleWeek();
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
  overflow: hidden;
}

.days-message {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
</style>
