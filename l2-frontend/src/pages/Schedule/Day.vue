<template>
  <div class="day-root" :class="today === day.date && 'day-today'">
    <div class="day-header">
      <div class="date-display">{{ dateDisplay }}</div>
      <div class="week-day-name">{{ weekDayName }}</div>
    </div>
    <div class="hours">
      <div class="hour" v-for="h in allHours" :key="h">
        <div class="hour-label">{{ h }}</div>
        <div class="hour-border"></div>
      </div>
    </div>
    <TimeSlot v-for="s in day.slots" :key="s.id" :data="s" :allHoursValues="allHoursValues" />
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import moment from 'moment';
import TimeSlot from './TimeSlot.vue';

const WEEK_DAY_NAMES = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье'];
const MONTH_LABELS = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];

@Component({
  components: {
    TimeSlot,
  },
  props: {
    day: {
      type: Object,
      required: true,
    },
    today: {
      type: String,
      required: true,
    },
    allHours: {
      type: Array,
      required: true,
    },
    allHoursValues: {
      type: Array,
      required: true,
    },
  },
})
export default class Day extends Vue {
  day: any;

  allHours: any[];

  allHoursValues: any[];

  today: string;

  get weekDayName() {
    return WEEK_DAY_NAMES[this.day.weekDay];
  }

  get dateDisplay() {
    const m = moment(this.day.date, 'YYYY-MM-DD');
    const dd = m.format('DD');
    const mm = MONTH_LABELS[m.month()];
    return `${dd} ${mm}`;
  }

  getOffset(s) {
    const offset = s.minute * 2 + this.allHoursValues.indexOf(s.hourValue) * 120 + 51;
    return `${offset}px`;
  }
}
</script>

<style lang="scss" scoped>
$border-color: #000;
$hour-height: 120px;

.day-root {
  width: calc(100% / 7);
  flex: 0 calc(100% / 7);
  border-right: 1px solid $border-color;
  position: relative;
  background-color: #fff;

  &.day-today {
    background-color: #f4fffc;
  }
}

.day-today .day-header {
  background-color: #d3efe7;
}

.day-header {
  border-bottom: 1px solid $border-color;
  padding: 5px;
  text-align: center;
  position: sticky;
  top: 0;
  z-index: 3;
  background-color: #fff;
  height: 51px;
}

.date-display {
  font-weight: bold;
}

.hour {
  position: relative;
  height: $hour-height;
  width: 100%;
  overflow: visible;
  padding-bottom: 1px;

  &-border {
    content: '';
    display: block;
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 1px;
    background-color: $border-color;
    z-index: 0;
  }

  &-label {
    position: absolute;
    top: 3px;
    left: 3px;
    font-size: 12px;
  }
}
</style>
