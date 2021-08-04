<template>
  <div>
    <vue-meeting-selector
      v-model="meeting"
      :date="date"
      :loading="loading"
      :meetings-days="meetingsDays"
      :calendar-options="calendarOptions"
      @next-date="nextDate"
      @previous-date="previousDate"
    />
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import moment from 'moment';
// @ts-ignore
import VueMeetingSelector from 'vue-meeting-selector';
import api from '@/api';

@Component({
  components: {
    VueMeetingSelector,
  },
  data() {
    return {
      date: moment()
        .startOf('isoWeek')
        .toDate(),
      meeting: null,
      loading: false,
      meetingsDays: [],
      calendarOptions: {
        loadingLabel: 'Загрузка',
        limit: 24,
        daysLabel: ['Вск', 'Пнд', 'Втр', 'Срд', 'Чтв', 'Птн', 'Суб', 'Вск'],
        monthsLabel: ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'],
        disabledDate() {
          return false;
        },
      },
    };
  },
  async mounted() {
    this.loading = true;
    this.meetingsDays = await this.getMeetings(this.date);
    this.loading = false;
  },
})
export default class Schedule extends Vue {
  loading: boolean;

  date: Date;

  meetingsDays: any[];

  meeting: any;

  calendarOptions: any;

  // eslint-disable-next-line class-methods-use-this
  async getMeetings(date) {
    const { days } = await api('/schedule/days', {
      date: typeof date === 'string' ? date : moment(date).format('YYYY-MM-DD'),
    });

    return days;
  }

  async nextDate() {
    this.loading = true;
    const date = new Date(this.date);
    date.setDate(date.getDate() + 7);
    this.meetingsDays = await this.getMeetings(date);
    this.date = date;
    this.loading = false;
  }

  async previousDate() {
    this.loading = true;
    const date = new Date(this.date);
    date.setDate(date.getDate() - 7);
    this.meetingsDays = await this.getMeetings(date);
    this.date = date;
    this.loading = false;
  }
}
</script>

<style lang="scss" scoped></style>
