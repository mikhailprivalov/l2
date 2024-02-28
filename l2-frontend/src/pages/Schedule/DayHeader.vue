<template>
  <div v-frag>
    <div class="date-display">
      {{ dateDisplay }}
    </div>
    <div class="week-day-name">
      {{ weekDayName }}
    </div>
    <div>
      <a
        v-if="isEditing"
        v-tippy
        href="#"
        class="a-under"
        title="Сгенерировать слоты"
        @click.prevent="generateSlots()"
      >
        <i class="fas fa-paint-roller" />
      </a>
      <a
        v-if="isEditing"
        v-tippy
        href="#"
        class="a-under"
        title="Удалить слоты"
        @click.prevent="deleteDaySlots()"
      >
        <i class="fa-solid fa-trash-can" />
      </a>
      <a
        v-if="isEditing"
        v-tippy
        href="#"
        class="a-under"
        title="Скопировать слоты"
        @click.prevent="copyDaySlots()"
      >
        <i class="fa-solid fa-copy" />
      </a>
    </div>

    <MountingPortal
      mount-to="#portal-place-modal"
      :name="`DayHeaderPopupSlotsGenerate-${day.date}`"
      append
    >
      <transition name="fade">
        <modal
          v-if="open"
          show-footer="true"
          white-bg="true"
          max-width="710px"
          width="100%"
          margin-left-right="auto"
          @close="open = false"
        >
          <span slot="header">Сгенерировать слоты для даты {{ day.date | formatDate }}</span>
          <div
            slot="body"
            class="popup-body"
          >
            <div class="input-group">
              <span class="input-group-addon">Время начала</span>
              <input
                v-model="timeStart"
                class="form-control"
                type="time"
              >
            </div>
            <div class="input-group">
              <span class="input-group-addon">Длительность, мин</span>
              <input
                v-model.number="duration"
                class="form-control"
                type="number"
                min="3"
                :max="maxDuration"
                :placeholder="`от 3 до ${maxDuration}`"
              >
            </div>
            <div class="input-group">
              <span class="input-group-addon">Количество (1 - {{ countMax }})</span>
              <input
                v-model.number="count"
                class="form-control"
                type="number"
                min="1"
                :max="countMax"
              >
            </div>

            <div class="slots-generated">
              <span
                v-for="t in slots"
                :key="t"
                class="badge badge-primary"
              >{{ t }}</span>
            </div>

            <h5>Источники записи</h5>
            <label> <input
              v-model="sources"
              type="checkbox"
              value="portal"
            > Портал пациента </label><br>
            <label> <input
              v-model="sources"
              type="checkbox"
              value="local"
            > Текущая система L2 </label>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-6">
                <button
                  class="btn btn-blue-nb"
                  type="button"
                  @click="open = false"
                >
                  Закрыть
                </button>
              </div>
              <div class="col-xs-6 text-right">
                <button
                  class="btn btn-blue-nb"
                  type="button"
                  :disabled="!isValid"
                  @click="save"
                >
                  Сохранить
                </button>
              </div>
            </div>
          </div>
        </modal>
        <modal
          v-if="isCopyDaySlots"
          show-footer="true"
          white-bg="true"
          max-width="710px"
          width="100%"
          margin-left-right="auto"
          @close="isCopyDaySlots = false"
        >
          <span slot="header">Скопировать слоты для даты {{ day.date | formatDate }}</span>
          <div
            slot="body"
            class="popup-body"
          >
            <div class="input-group">
              <span class="input-group-addon">Количество (1 - {{ countMax }})</span>
              <input
                v-model.number="countDaysToCopy"
                class="form-control"
                type="number"
                min="1"
                :max="countMax"
              >
            </div>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-6">
                <button
                  class="btn btn-blue-nb"
                  type="button"
                  @click="isCopyDaySlots = false"
                >
                  Закрыть
                </button>
              </div>
              <div class="col-xs-6 text-right">
                <button
                  class="btn btn-blue-nb"
                  type="button"
                  :disabled="!isValid"
                  @click="copySchedule"
                >
                  Сохранить
                </button>
              </div>
            </div>
          </div>
        </modal>
      </transition>
    </MountingPortal>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import moment from 'moment';

import * as actions from '@/store/action-types';
import Modal from '@/ui-cards/Modal.vue';

const WEEK_DAY_NAMES = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье'];
const MONTH_LABELS = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];

const zPadLeft = (n) => {
  if (n < 10) {
    return `0${n}`;
  }

  return String(n);
};

const minutesToTime = (mins) => {
  const h = Math.trunc(mins / 60);
  const m = mins % 60;

  return `${zPadLeft(h)}:${zPadLeft(m)}`;
};

@Component({
  components: { Modal },
  props: {
    day: {
      type: Object,
      required: true,
    },
    isEditing: {
      type: Boolean,
    },
    resource: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      open: false,
      isCopyDaySlots: false,
      timeStart: '08:00',
      duration: 15,
      count: 10,
      countDaysToCopy: 1,
      sources: ['portal', 'local'],
    };
  },
  watch: {
    count() {
      this.fixCount();
    },
    duration() {
      this.fixCount();
    },
    timeStartMinutes() {
      this.fixCount();
    },
  },
  mounted() {
    this.$root.$on('schedule:create-one-slot', (date, atTime) => {
      if (date !== this.day.date) {
        return;
      }
      if (atTime) {
        this.timeStart = atTime;
      }

      this.count = 1;

      this.open = true;
    });

    this.$root.$on('schedule:copy-schedule', () => {
      this.count = 1;
      this.isCopyDaySlots = true;
    });
  },
})
export default class Day extends Vue {
  day: any;

  open: boolean;

  isCopyDaySlots: boolean;

  timeStart: string;

  duration: number;

  count: number;

  sources: string[];

  resource: number;

  get weekDayName() {
    return WEEK_DAY_NAMES[this.day.weekDay];
  }

  get dateDisplay() {
    const m = moment(this.day.date, 'YYYY-MM-DD');
    const dd = m.format('DD');
    const mm = MONTH_LABELS[m.month()];
    return `${dd} ${mm}`;
  }

  get timeStartMinutes() {
    const [h, m] = this.timeStart.split(':');

    return Number(h) * 60 + Number(m);
  }

  get maxDuration() {
    return 1440 - this.timeStartMinutes;
  }

  get countMax() {
    const restMinutes = 1440 - this.timeStartMinutes;

    return Math.floor(restMinutes / this.duration);
  }

  get slots() {
    const r = [];

    for (let i = 0; i < this.count; i++) {
      const minutesStart = this.timeStartMinutes + this.duration * i;
      const minutesEnd = this.timeStartMinutes + this.duration * (i + 1);

      r.push(`${minutesToTime(minutesStart)} — ${minutesToTime(minutesEnd)}`);
    }

    return r;
  }

  get isValid() {
    return this.slots.length > 0 && this.sources.length > 0;
  }

  fixCount() {
    this.count = Math.min(this.count, this.countMax);
  }

  generateSlots() {
    this.open = true;
  }

  copyDaySlots() {
    this.isCopyDaySlots = true;
  }

  async save() {
    await this.$store.dispatch(actions.INC_LOADING);
    const { ok, message } = await this.$api('/schedule/create-slots', this, ['slots', 'sources', 'duration', 'resource'], {
      date: this.day.date,
    });
    if (!ok) {
      this.$root.$emit('msg', 'error', message);
      return;
    }
    this.open = false;
    await this.$store.dispatch(actions.DEC_LOADING);
    this.$root.$emit('reload-slots');
  }

  async deleteDaySlots() {
    await this.$store.dispatch(actions.INC_LOADING);
    const { ok, message } = await this.$api('/schedule/delete-day-slots', this, ['resource'], {
      date: this.day.date,
    });
    if (!ok) {
      this.$root.$emit('msg', 'error', message);
      return;
    }
    await this.$store.dispatch(actions.DEC_LOADING);
    this.$root.$emit('reload-slots');
  }

  async copySchedule() {
    await this.$store.dispatch(actions.INC_LOADING);
    const { ok, message } = await this.$api('/schedule/copy-day-slots', this, ['resource', 'countDaysToCopy'], {
      date: this.day.date,
    });
    if (!ok) {
      this.$root.$emit('msg', 'error', message);
      return;
    }
    await this.$store.dispatch(actions.DEC_LOADING);
    this.$root.$emit('reload-slots');
  }
}
</script>

<style lang="scss" scoped>
.date-display {
  font-weight: bold;
}

.popup-body {
  .input-group {
    margin-bottom: 3px;
  }
}
</style>
