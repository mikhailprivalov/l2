<template>
  <div
    class="day-root"
    :class="[currentDate === day.date && 'day-today', mode === 'list' ? 'day-list' : 'day-natural']"
    :style="styleRoot"
  >
    <div
      v-if="step !== 1"
      class="day-header"
    >
      <DayHeader
        :day="day"
        :is-editing="isEditing"
        :resource="resource"
      />
    </div>
    <div
      v-if="mode !== 'list'"
      class="hours"
    >
      <div
        v-for="h in allHours"
        :key="h"
        class="hour"
      >
        <div class="hour-label">
          {{ h }}
        </div>
        <div
          v-if="isEditing"
          class="hour-buttons"
        >
          <a
            v-tippy
            href="#"
            class="a-under"
            title="Создать слот"
            @click.prevent="createSlot(h)"
          ><i class="fa fa-plus" /></a>
        </div>
        <div class="hour-border" />
      </div>
    </div>
    <TimeSlot
      v-for="s in day.slots"
      :key="s.id"
      :data="s"
      :mode="mode"
      :services="services"
      :all-hours-values="allHoursValues"
      :simple="step === 1"
      :only-emit="onlyEmit"
    />
    <TimeMarker
      v-if="currentDate === day.date && mode !== 'list'"
      :time="currentTime"
      :all-hours-values="allHoursValues"
    />
    <button
      v-if="isEditing"
      class="btn btn-blue-nb btn-sm btn-block nbr"
      @click.prevent="createSlot()"
    >
      Создать слот
    </button>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';

import TimeSlot from './TimeSlot.vue';
import TimeMarker from './TimeMarker.vue';
import DayHeader from './DayHeader.vue';

@Component({
  components: {
    TimeSlot,
    TimeMarker,
    DayHeader,
  },
  props: {
    day: {
      type: Object,
      required: true,
    },
    currentDate: {
      type: String,
      required: true,
    },
    currentTime: {
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
    step: {
      type: Number,
      required: true,
    },
    services: {
      type: Array,
      required: true,
    },
  },
})
export default class Day extends Vue {
  day: any;

  allHours: any[];

  allHoursValues: any[];

  currentDate: string;

  currentTime: string;

  mode: string | null;

  resource: number;

  step: number;

  services: any[];

  getOffset(s) {
    const offset = s.minute * 2 + this.allHoursValues.indexOf(s.hourValue) * 120 + (this.step === 1 ? 0 : 51);
    return `${offset}px`;
  }

  createSlot(time) {
    this.$root.$emit('schedule:create-one-slot', this.day.date, time);
  }

  get width() {
    return `calc(100% / ${this.step})`;
  }

  get styleRoot() {
    return `width: ${this.width};flex: 0 ${this.width}`;
  }
}
</script>

<style lang="scss" scoped>
$border-color: #000;
$hour-height: 120px;

.day-root {
  min-height: 100%;
  border-right: 1px solid $border-color;
  position: relative;
  background-color: #fff;

  &.day-today {
    background-color: #f4fffc;
  }

  &:last-child {
    border-right: none;
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
  height: 65px;
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

  &-buttons {
    position: absolute;
    top: 18px;
    left: 3px;
    font-size: 12px;
  }
}
</style>
