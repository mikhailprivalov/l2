<template>
  <date-picker
    ref="datepicker"
    :key="a.plan"
    v-model="a.plan"
    class="td-calendar"
    is-dark
    color="teal"
    :available-dates="avDates"
    :masks="masks"
    @popoverWillShow="onShow"
  >
    <template #default="{ togglePopover }">
      <div
        v-tippy="{ html: '#' + tippyId, ...commonTippy, trigger: a.planYear === v.year ? 'mouseenter focus' : 'manual' }"
        class="td-calendar-inner"
        @click="togglePopover"
      >
        <template v-if="a.planYear === v.year">
          {{ a.plan.replace(`.${v.year}`, '') }}
        </template>
      </div>
      <div
        v-if="a.planYear === v.year"
        :id="tippyId"
        class="tp"
      >
        <button
          class="btn btn-blue-nb btn-transparent btn-sm"
          @click="clearPlan"
        >
          <i class="fas fa-times" />
        </button>
      </div>
    </template>
  </date-picker>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
// @ts-ignore
import DatePicker from 'v-calendar/src/components/DatePicker.vue';
import moment from 'moment';

@Component({
  components: {
    DatePicker,
  },
  props: {
    a: {
      type: Object,
      required: true,
    },
    researchPk: {
      type: Number,
      required: true,
    },
    v: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      masks: {
        iso: 'DD.MM.YYYY',
        data: ['DD.MM.YYYY'],
        input: ['DD.MM.YYYY'],
      },
      tippyId: `tippy-date-${Math.floor(Math.random() * 100000)}`,
      commonTippy: {
        placement: 'left',
        reactive: true,
        interactive: true,
        arrow: true,
      },
    };
  },
  watch: {
    planDate() {
      if (!this.planDate) {
        this.$emit('updated', this.researchPk, this.a);
        return;
      }

      let hasChanges = false;

      const newDate = typeof this.planDate === 'string' && this.planDate.split('.').length === 3
        ? this.planDate
        : moment(this.planDate).format('DD.MM.YYYY');

      if (newDate !== this.planDate) {
        this.a.plan = newDate;
        hasChanges = true;
      }

      const year = Number(newDate.split('.')[2]);

      if (this.a.planYear !== year) {
        this.a.planYear = year;
        hasChanges = true;
      }

      if (hasChanges) {
        this.$emit('updated', this.researchPk, this.a);
      }
    },
  },
})
export default class ScreeningDate extends Vue {
  a: any;

  cardPk: any;

  researchPk: any;

  v: any;

  masks: any;

  get avDates() {
    return { start: new Date(this.v.year, 0, 1), end: new Date(this.v.year, 11, 31) };
  }

  get planDate() {
    return this.a.plan;
  }

  onShow() {
    let datepicker: any;
    // eslint-disable-next-line prefer-const
    datepicker = this.$refs.datepicker;

    let date;

    if (!this.planDate) {
      date = new Date(this.v.year, 0, 1);
    } else {
      const newDate = typeof this.planDate === 'string' && this.planDate.split('.').length === 3
        ? this.planDate
        : moment(this.planDate).format('DD.MM.YYYY');
      date = moment(newDate, 'DD.MM.YYYY');
      date = date.year() === this.v.year ? date.toDate() : new Date(this.v.year, 0, 1);
    }

    if (date) {
      datepicker.move(new Date(date));
    }
  }

  get isCurrent() {
    if (!this.planDate) {
      return false;
    }

    const currentDate = typeof this.planDate === 'string' && this.planDate.split('.').length === 3
      ? this.planDate
      : moment(this.planDate).format('DD.MM.YYYY');
    return moment(currentDate, 'DD.MM.YYYY').year() === this.v.year;
  }

  clearPlan() {
    if (this.isCurrent) {
      this.a.planYear = null;
      this.a.plan = null;
    }
  }
}
</script>

<style scoped lang="scss">
.td-calendar,
.td-calendar-inner {
  display: block;
  height: 100%;
}

.td-calendar-inner {
  line-height: 27px;
}

.btn-transparent {
  background: transparent !important;
  border: 1px solid #fff !important;
  color: #fff !important;

  &:hover {
    background: #fff !important;
    border: 1px solid #fff !important;
    color: #000 !important;
  }
}

.td-r {
  .a-under-reversed {
    opacity: 0;

    color: #fff;
  }

  &:hover .a-under-reversed {
    opacity: 1;
  }
}
</style>
