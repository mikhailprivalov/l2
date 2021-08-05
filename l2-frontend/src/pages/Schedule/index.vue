<template>
  <div class="root">
    <Day v-for="d in days" :key="d.date" :day="d" :start-time="startTime" :end-time="endTime" />
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import moment, { Moment } from 'moment';
import api from '@/api';
import Day from './Day.vue';

@Component({
  components: {
    Day,
  },
  data() {
    return {
      date: moment().startOf('isoWeek'),
      days: [],
      startTime: null,
      endTime: null,
    };
  },
  mounted() {
    this.getScheduleWeek();
  },
})
export default class Schedule extends Vue {
  loading: boolean;

  date: Moment;

  days: any[];

  startTime: string | null;

  endTime: string | null;

  async getScheduleWeek() {
    const { days, startTime, endTime } = await api('/schedule/days', {
      date: this.date.format('YYYY-MM-DD'),
    });

    this.days = days;
    this.startTime = startTime;
    this.endTime = endTime;
  }

  async nextDate() {
    this.date = moment(this.date).add(7, 'weeks');
    await this.getScheduleWeek();
  }

  async previousDate() {
    this.date = moment(this.date).subtract(7, 'weeks');
    await this.getScheduleWeek();
  }
}
</script>

<style lang="scss" scoped>
.root {
  display: flex;
  flex-wrap: nowrap;
  flex-direction: row;
  justify-content: flex-start;
  align-items: flex-start;

  position: absolute;
  top: 36px;
  left: 0;
  right: 0;
  bottom: 0;

  overflow-x: hidden;
  overflow-y: auto;
}
</style>
