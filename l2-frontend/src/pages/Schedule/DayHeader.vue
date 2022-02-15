<template>
  <div v-frag>
    <div class="date-display">
      {{ dateDisplay }}
      <a v-if="isEditing" href="#" class="a-under" title="Сгенерировать слоты" @click.prevent="generateSlots()" v-tippy>
        <i class="fas fa-paint-roller"></i>
      </a>
    </div>
    <div class="week-day-name">{{ weekDayName }}</div>

    <MountingPortal mountTo="#portal-place-modal" :name="`DayHeaderPopupSlotsGenerate-${day.date}`" append>
      <transition name="fade">
        <modal
          v-if="open"
          @close="open = false"
          show-footer="true"
          white-bg="true"
          max-width="710px"
          width="100%"
          marginLeftRight="auto"
        >
          <span slot="header">Сгенерировать слоты для даты {{ day.date | formatDate }}</span>
          <div slot="body" class="popup-body">
            <div class="input-group">
              <span class="input-group-addon">Время начала</span>
              <input class="form-control" type="time" v-model="timeStart" />
            </div>
            <div class="input-group">
              <span class="input-group-addon">Длительность, мин</span>
              <input
                class="form-control"
                type="number"
                v-model.number="duration"
                min="3"
                :max="maxDuration"
                :placeholder="`от 3 до ${maxDuration}`"
              />
            </div>
            <div class="input-group">
              <span class="input-group-addon">Количество (1 - {{ countMax }})</span>
              <input class="form-control" type="number" v-model.number="count" min="1" :max="countMax" />
            </div>

            <div class="slots-generated">
              <span class="badge badge-primary" v-for="t in slots" :key="t">{{ t }}</span>
            </div>

            <h5>Источники записи</h5>
            <label> <input type="checkbox" value="portal" v-model="sources" /> Портал пациента </label><br />
            <label> <input type="checkbox" value="local" v-model="sources" /> Текущая система L2 </label>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-6">
                <button @click="open = false" class="btn btn-blue-nb" type="button">Закрыть</button>
              </div>
              <div class="col-xs-6 text-right">
                <button class="btn btn-blue-nb" type="button" :disabled="!isValid" @click="save">Сохранить</button>
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
      timeStart: '08:00',
      duration: 15,
      count: 10,
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
  },
})
export default class Day extends Vue {
  day: any;

  open: boolean;

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
