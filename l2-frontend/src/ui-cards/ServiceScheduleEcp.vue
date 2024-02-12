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

    <div class="week-selector doc-selector">
      <button
        v-for="d in availableDoctorsByDate"
        :key="d"
        class="btn btn-link availableDate"
        :class="[d === activeDoctor && 'active']"
        @click="activeDoctor = d"
      >
        {{ doctorFioByResource[d] }}
      </button>
    </div>

    <div
      v-if="slots.length > 0 && activeDoctor && activeDate"
      class="resource"
    >
      <div class="resource-title">
        Доступное время <span
          v-if="showLimitMessage"
          class="messageAgeLimit"
        >{{ showLimitMessage }}</span>
      </div>
      <div class="resource-slots">
        <div
          v-for="s in slots"
          :key="s.pk"
          class="resource-slot"
          :class="[{'doctor-self-slot': s.slotTypeId === '10', 'forbidden-slot': s.slotTypeId === '8'},
                   activeSlot === s.pk && 'active' ]"
          @click="selectSlot(s.pk, s.title, s.typeSlot, s.slotTypeId)"
        >
          {{ s.title }}
        </div>
      </div>

      <button
        class="btn btn-link availableDate"
        :disabled="!activeSlot"
        @click="fillSlot"
      >
        Записать пациента
      </button>
    </div>
  </div>
</template>

<script lang="ts">
import moment from 'moment';

import * as actions from '@/store/action-types';

export default {
  props: {
    servicePk: {
      type: Number,
      required: true,
    },
    cardId: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      startDate: moment().startOf('isoWeek'),
      datesAvailable: {},
      loading: false,
      activeDate: moment().format('YYYY-MM-DD'),
      doctorsAtDate: {},
      activeDoctor: null,
      slots: [],
      activeSlot: null,
      activeSlotTitle: null,
      typeSlot: null,
      slotTypeId: null,
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
    availableDoctorsByDate() {
      const r = [];

      for (const [resourceKey, doctor] of Object.entries<any>(this.doctorsAtDate)) {
        if (doctor.dates.includes(this.activeDate)) {
          r.push(resourceKey);
        }
      }

      return r;
    },
    doctorFioByResource() {
      const r = {};

      for (const [resourceKey, doctor] of Object.entries<any>(this.doctorsAtDate)) {
        r[resourceKey] = doctor.fio;
      }

      return r;
    },
    serviceTitle() {
      return this.$store.getters.researches_obj[this.servicePk]?.title;
    },
    showLimitMessage() {
      return this.doctorsAtDate[this.activeDoctor].messageAgeLimit;
    },
  },
  watch: {
    displayDates: {
      immediate: true,
      async handler() {
        await this.loadAvailableDates();
        this.checkDate();
        this.checkDoctor();
      },
    },
    activeDate: {
      immediate: true,
      handler() {
        const r = this.checkDate();
        const r2 = this.checkDoctor();

        if (r && r2) {
          this.loadSlots();
        }
      },
    },
    activeDoctor: {
      handler() {
        this.checkDoctor();
        this.loadSlots();
      },
    },
    slots() {
      this.checkSlot();
    },
  },
  methods: {
    selectSlot(slotPk, slotTitle, typeSlot, slotTypeId) {
      this.activeSlot = slotPk;
      this.activeSlotTitle = slotTitle;
      this.typeSlot = typeSlot;
      this.slotTypeId = slotTypeId;
    },
    async loadSlots() {
      await this.$store.dispatch(actions.INC_LOADING);
      if (!this.activeDoctor || !this.activeDate) {
        await this.$store.dispatch(actions.DEC_LOADING);
        return;
      }
      const { result } = await this.$api('ecp/available-slots', {
        doctor_pk: this.activeDoctor,
        date: this.activeDate,
        research_pk: this.servicePk,
      });
      if (!result) {
        this.slots = [];
      } else {
        this.slots = result;
      }
      this.checkSlot();
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
    checkDoctor() {
      if (!this.availableDoctorsByDate.includes(this.activeDoctor)) {
        if (this.availableDoctorsByDate.length === 1) {
          // eslint-disable-next-line prefer-destructuring
          this.activeDoctor = this.availableDoctorsByDate[0];
        } else {
          this.activeDoctor = null;
        }
        return false;
      }
      return true;
    },
    checkSlot() {
      if (!this.slots.find(s => s.pk === this.activeSlot)) {
        this.activeSlot = null;
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
      this.slots = [];
      this.doctorsAtDate = {};
      this.activeDoctor = null;
      if (!this.startDate) {
        return;
      }
      this.loading = true;
      const {
        data: {
          doctors_has_free_date: doctors,
          unique_date: dates,
        } = {
          doctors_has_free_date: {},
          unique_date: [],
        },
      } = await this.$api('ecp/available-slots-of-dates', {
        research_pk: this.servicePk,
        date_start: this.displayDates[0],
        date_end: this.displayDates[this.displayDates.length - 1],
      });
      this.datesAvailable = (dates || []).reduce((acc, d) => {
        acc[d] = true;
        return acc;
      }, {});
      this.doctorsAtDate = doctors;
      this.loading = false;
      this.checkDate(true);
      this.checkDoctor();
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async fillSlot() {
      if (!this.activeSlot) {
        return;
      }
      await this.$store.dispatch(actions.INC_LOADING);
      const { register, message } = await this.$api('ecp/fill-slot', {
        slot_id: this.activeSlot,
        card_pk: this.cardId,
        type_slot: this.typeSlot,
        slot_type_id: this.slotTypeId,
        doctor_pk: this.activeDoctor,
        date: this.activeDate,
        slot_title: this.activeSlotTitle,
        research_pk: this.servicePk,
      });
      if (register) {
        this.$root.$emit('msg', 'ok', 'Пациент записан на прием');
        this.activeSlot = null;
        this.$emit('fill-slot-ok', this.servicePk);
      } else {
        this.$root.$emit('msg', 'error', message || 'Ошибка записи пациента на прием');
      }
      await this.$store.dispatch(actions.DEC_LOADING);
      await this.loadAvailableDates();
      await this.loadSlots();
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
.messageAgeLimit {
  float: right;
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

.doc-selector .btn-link {
  white-space: normal;
  display: inline-block;
}

.resource-slots {
  margin-bottom: 5px;

  & + .btn {
    display: block;
    margin: 0 auto;

    &:hover {
      background: rgba(#048493, 0.4);
    }

    &:active {
      background: rgba(#048493, 0.3);
    }
  }
}

.doctor-self-slot {
  background: rgba(#4cae4c, 0.6);
}

.forbidden-slot {
  background: rgba(#042693, 0.3);
}

</style>
