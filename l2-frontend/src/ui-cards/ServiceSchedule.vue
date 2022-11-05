<template>
  <div>
    <div class="schedule-title">
      Запись на услугу {{ serviceTitle }}
    </div>

    <div class="week-selector">
      <button
        class="btn btn-link"
        @click="decDate"
      >
        <i class="fa fa-arrow-left" />
      </button>
      <button
        v-for="d in displayDates"
        :key="d"
        class="btn btn-link"
        :class="[d === activeDate && 'active', !!datesAvailable[d] ? 'availableDate' : 'unavailableDate']"
        :disabled="!datesAvailable[d]"
        @click="activeDate = d"
      >
        {{ d | formatDateShort }}
      </button>
      <button
        class="btn btn-link"
        @click="incDate"
      >
        <i class="fa fa-arrow-right" />
      </button>
    </div>

    <div
      v-for="r in slots"
      :key="r.resourcePk"
      class="resource"
    >
      <div class="resource-title">
        {{ r.resourceTitle || `Ресурс ${r.resourcePk}` }}
      </div>
      <div class="resource-slots">
        <div
          v-for="s in r.slots"
          :key="s.pk"
          class="resource-slot"
          :class="activeSlot === s.pk && 'active'"
          @click="selectSlot(s.pk, s.title, r.resourcePk)"
        >
          {{ s.title }}
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import moment from 'moment';

import * as actions from '@/store/action-types';

export default {
  model: {
    event: 'modified',
  },
  props: {
    value: {
      type: Number,
      required: false,
    },
    servicePk: {
      type: Number,
      required: true,
    },
    serviceTitle: {
      type: String,
      required: true,
    },
    initialDate: {
      type: String,
      required: false,
    },
    slotDate: {
      type: String,
      required: false,
    },
    slotResource: {
      type: Number,
      required: false,
    },
  },
  data() {
    return {
      startDate: (this.initialDate ? moment(this.initialDate, 'DD.MM.YYYY') : moment()).startOf('isoWeek'),
      datesAvailable: {},
      loading: false,
      activeDate: (this.initialDate ? moment(this.initialDate, 'DD.MM.YYYY') : moment()).format('YYYY-MM-DD'),
      slots: [],
      activeSlot: null,
      activeSlotTitle: null,
      activeSlotResource: null,
    };
  },
  computed: {
    displayDates() {
      if (!this.startDate) {
        return [];
      }
      const dates = [];
      for (let i = 0; i < 7; i++) {
        dates.push(this.startDate.clone().add(i, 'days').format('YYYY-MM-DD'));
      }
      return dates;
    },
  },
  watch: {
    displayDates: {
      immediate: true,
      async handler() {
        await this.loadAvailableDates();
        this.checkDate();
      },
    },
    activeDate: {
      immediate: true,
      handler() {
        const r = this.checkDate();
        if (!r) {
          return;
        }
        this.loadSlots();
        this.$emit('update:slotDate', this.activeDate);
      },
    },
    activeSlotResource() {
      this.$emit('update:slotResource', this.activeSlotResource);
    },
    slots() {
      let sameSlot = null;
      for (const r of this.slots) {
        for (const s of r.slots) {
          if (s.pk === this.activeSlot) {
            return;
          }
          if (this.activeSlotResource === r.resourcePk && s.title === this.activeSlotTitle) {
            sameSlot = s.pk;
          }
        }
      }

      this.activeSlot = sameSlot;
      if (!sameSlot) {
        this.activeSlotResource = null;
        this.activeSlotTitle = null;
      }
    },
    activeSlot: {
      immediate: true,
      handler() {
        this.changeValue(this.activeSlot);
      },
    },
  },
  methods: {
    selectSlot(slotPk, slotTitle, resourcePk) {
      this.activeSlot = slotPk;
      this.activeSlotTitle = slotTitle;
      this.activeSlotResource = resourcePk;
    },
    async loadSlots() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { result } = await this.$api('schedule/available-slots', {
        research_pk: this.servicePk,
        date_start: this.activeDate,
        date_end: this.activeDate,
      });
      if (!result.dates) {
        this.slots = [];
      } else if (result.dates[this.activeDate]) {
        this.slots = result.dates[this.activeDate];
      } else {
        this.slots = [];
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    checkDate(forced = false) {
      if (this.displayDates.length > 0 && (forced || !this.displayDates.includes(this.activeDate))) {
        for (const dd of this.displayDates) {
          if (this.datesAvailable[dd]) {
            this.activeDate = dd;
            return false;
          }
        }
        // eslint-disable-next-line prefer-destructuring
        this.activeDate = this.displayDates[0];
        return false;
      }
      return true;
    },
    decDate() {
      this.startDate = this.startDate.clone().subtract(7, 'days');
    },
    incDate() {
      this.startDate = this.startDate.clone().add(7, 'days');
    },
    async loadAvailableDates() {
      await this.$store.dispatch(actions.INC_LOADING);
      if (!this.startDate) {
        return;
      }
      this.loading = true;
      const { data } = await this.$api('schedule/available-slots-of-dates', {
        research_pk: this.servicePk,
        date_start: this.displayDates[0],
        date_end: this.displayDates[this.displayDates.length - 1],
      });
      this.datesAvailable = data;
      this.loading = false;
      this.checkDate(true);
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    changeValue(newVal) {
      this.$emit('modified', newVal);
    },
  },
};
</script>

<style lang="scss" scoped>
.week-selector {
  display: flex;
  justify-content: stretch;
  flex-wrap: nowrap;
  margin-bottom: 10px;

  .btn {
    align-self: stretch;
    flex: 1;
    border-radius: 3px;

    &:hover {
      background: rgba(0, 0, 0, 0.06);
    }

    &.active {
      font-weight: bold;
      background-color: rgba(#048493, 0.65);
    }
  }
}

.unavailableDate {
  color: #000;
  background: rgba(0, 0, 0, 0.06);
}

.availableDate {
  color: black;
  font-weight: bold;
  background-color: rgba(#048493, 0.16);
}

.resource {
  margin: 5px;
  padding: 5px;
  border-radius: 5px;
  background: rgba(#048493, 0.15);

  &-title {
    font-weight: bold;
    margin-bottom: 5px;
    padding-bottom: 3px;
    border-bottom: 1px solid rgba(#048493, 0.7);
  }

  &-slot {
    display: inline-block;
    font-family: 'Courier New', Courier, monospace;
    padding: 4px;
    border-radius: 4px;
    margin-right: 3px;
    margin-bottom: 4px;
    background: rgba(#048493, 0.15);
    cursor: pointer;

    &.active {
      font-weight: bold;
      background: rgba(#048493, 0.3);
    }

    &:hover {
      background: rgba(#048493, 0.4);
    }
  }
}

.schedule-title {
  font-weight: bold;
  font-size: 18px;
  margin-bottom: 10px;
}
</style>
