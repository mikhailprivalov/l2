<template>
  <div class="day-root">
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
    <div class="slot" v-for="s in day.slots" :key="s.id" :style="`top: ${getOffset(s)}; height: ${s.duration * 2}px;`">
      {{ s.id }} – {{ s.time }} – {{ s.duration }} min
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import moment from 'moment';

const WEEK_DAY_NAMES = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье'];
const MONTH_LABELS = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];

@Component({
  props: {
    day: {
      type: Object,
      required: true,
    },
    startTime: {
      type: String,
      required: false,
      default: null,
    },
    endTime: {
      type: String,
      required: false,
      default: null,
    },
  },
})
export default class Day extends Vue {
  day: any;

  startTime: string | null;

  endTime: string | null;

  get weekDayName() {
    return WEEK_DAY_NAMES[this.day.weekDay];
  }

  get dateDisplay() {
    const m = moment(this.day.date, 'YYYY-MM-DD');
    const dd = m.format('DD');
    const mm = MONTH_LABELS[m.month()];
    return `${dd} ${mm}`;
  }

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
    return this.allHours.map(h => Number(h.split(':')[0]));
  }

  get slotsByHour() {
    const r = this.allHours.reduce((a, h) => ({ ...a, [h]: [] }), {});

    for (const s of this.day.slots) {
      r[s.hour].push(s);
    }

    return r;
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
$slot-minimal-height: 8px;
$slot-left-offset: 38px;
$slot-padding: 1px;

.day-root {
  width: calc(100% / 7);
  flex: 0 calc(100% / 7);
  border-right: 1px solid $border-color;
  position: relative;
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
  background-color: #fff;
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

.slot {
  position: absolute;
  cursor: pointer;

  left: $slot-left-offset;
  right: 0;
  z-index: 1;

  border-radius: $slot-padding * 3;
  min-height: $slot-minimal-height;
  padding: $slot-padding $slot-padding * 3;
  line-height: 1;
  border: 1px solid rgb(176, 176, 176);
  background: linear-gradient(to bottom, rgb(250, 250, 250) 0%, rgb(219, 219, 219) 100%);
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);

  &:hover {
    box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
    z-index: 2;
    transform: scale(1.008);
  }
}
</style>
