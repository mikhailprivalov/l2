<template>
  <div class="days-grid">
    <Day
      v-for="d in days"
      :key="d.date"
      :day="d"
      :all-hours="allHours"
      :all-hours-values="allHoursValues"
      :current-date="currentDate"
      :current-time="currentTime"
      :mode="mode"
      :is-editing="isEditing"
      :resource="resource"
      :services="services"
      :step="days.length"
      :only-emit="onlyEmit"
    />
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import moment, { Moment } from 'moment';

import Day from './Day.vue';

@Component({
  props: {
    days: {
      type: Array,
      required: true,
    },
    startTime: {
      type: String,
    },
    endTime: {
      type: String,
    },
    mode: {
      type: String,
    },
    isEditing: {
      type: Boolean,
    },
    onlyEmit: {
      type: Boolean,
    },
    resource: {
      type: Number,
      required: true,
    },
    services: {
      type: Array,
      required: true,
    },
  },
  components: {
    Day,
  },
  data() {
    return {
      currentDate: moment().format('YYYY-MM-DD'),
      currentTime: moment().format('HH:mm:ss'),
      timeInterval: null,
    };
  },
  mounted() {
    this.getCurrentTime();
    this.timeInterval = setInterval(() => this.getCurrentTime(), 2000);
  },
  beforeDestroy() {
    clearInterval(this.timeInterval);
  },
})
export default class DaysGridNatural extends Vue {
  date: Moment;

  days: any[];

  startTime: string | null;

  endTime: string | null;

  mode: string | null;

  currentDate: string;

  currentTime: string;

  resource: number;

  get allHours() {
    const h = [];

    if (!this.startTime || !this.endTime) {
      return h;
    }

    const endMoment = moment(this.endTime, 'HH:mm');

    for (let m = moment(this.startTime, 'HH:mm'); m.diff(endMoment, 'hours') < 0; m.add(1, 'hour')) {
      h.push(m.format('HH:mm'));
    }

    if (!h.includes(this.endTime)) {
      h.push(this.endTime);
    }

    return h;
  }

  get allHoursValues() {
    return this.allHours.map((h) => Number(h.split(':')[0]));
  }

  async getCurrentTime() {
    const { date, time } = await this.$api('current-time');
    if (date && time) {
      this.currentDate = date;
      this.currentTime = time;
    }
  }
}
</script>

<style lang="scss" scoped>
.days-grid {
  display: flex;
  flex-wrap: nowrap;
  flex-direction: row;
  justify-content: flex-start;
  align-items: stretch;
}
</style>
