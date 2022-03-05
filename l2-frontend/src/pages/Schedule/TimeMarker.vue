<template>
  <div class="time-marker" :style="`top: ${offset}`" v-if="offset" />
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';

@Component({
  props: {
    time: {
      type: String,
      required: true,
    },
    allHoursValues: {
      type: Array,
      required: true,
    },
  },
})
export default class TimeMarker extends Vue {
  time: string;

  allHoursValues: any[];

  get offset() {
    const [hS, mS, sS] = this.time.split(':');
    const h = Number(hS);
    const m = Number(mS);
    const s = Number(sS);
    if (!this.allHoursValues.includes(h)) {
      return null;
    }
    const offset = (Number(m) + Number(s) / 60) * 2 + this.allHoursValues.indexOf(h) * 120 + 50;
    return `${offset}px`;
  }
}
</script>

<style lang="scss" scoped>
.time-marker {
  position: absolute;

  left: 0;
  right: 0;
  z-index: 0;

  height: 1px;
  background: #f00;
  opacity: 0.8;

  &:before {
    content: '';
    position: absolute;
    left: 0;
    top: -2px;
    border-radius: 50%;
    width: 5px;
    height: 5px;
    background: #f00;
  }
}
</style>
