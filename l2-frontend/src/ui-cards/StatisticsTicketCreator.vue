<template>
  <div style="align-self: stretch;overflow-y: auto;width: 100%;overflow-x: hidden;">
    <div class="input-group">
      <span class="input-group-addon">Цель посещения</span>
      <div
        class="input-group-btn"
        style="width: 100%;"
      >
        <SelectPickerB
          v-model="visit"
          no-border-left="true"
          :options="visit_select"
        />
      </div>
    </div>
    <div
      class="form-group basic-textarea"
      style="margin-top: 5px;margin-bottom: 0"
    >
      <label style="width: 100%;font-weight: normal;">Код диагноза (МКБ 10), виды услуг, виды травм:
        <textarea
          v-model="info"
          class="form-control"
          rows="2"
          style="resize: none;width: 100%"
        />
      </label>
    </div>
    <div
      class="row"
      style="margin-top: 5px;"
    >
      <div class="col-xs-6">
        <label style="display: block;font-weight: normal;">
          Впервые: <input
            v-model="first_time"
            type="checkbox"
          > {{ first_time? 'да': 'нет' }}
        </label>
      </div>
      <div class="col-xs-6">
        <label style="display: block;font-weight: normal;">
          Первичный приём: <input
            v-model="primary_visit"
            type="checkbox"
          > {{ primary_visit? 'да': 'нет' }}
        </label>
      </div>
    </div>

    <div class="input-group flex-group">
      <span class="input-group-addon">Диспансерный учёт</span>
      <div class="input-group-btn">
        <SelectPickerB
          v-model="disp"
          no-border-left="true"
          :options="disp_select"
        />
      </div>
    </div>

    <div
      v-show="disp === '1' || disp === '2' || disp === '3'"
      class="input-group flex-group"
    >
      <span class="input-group-addon">Диагноз учёта</span>
      <input
        v-model="disp_diagnos"
        type="text"
        class="form-control"
      >
    </div>

    <div
      v-show="disp === '3'"
      class="input-group flex-group"
    >
      <span class="input-group-addon">Причина снятия</span>
      <div class="input-group-btn">
        <SelectPickerB
          v-model="exclude"
          no-border-left="true"
          :options="exclude_select"
        />
      </div>
    </div>

    <div class="input-group flex-group">
      <span class="input-group-addon">Результат обращения</span>
      <div class="input-group-btn">
        <SelectPickerB
          v-model="result"
          no-border-left="true"
          :options="result_select"
        />
      </div>
    </div>

    <div class="input-group flex-group">
      <span class="input-group-addon">Исход</span>
      <div class="input-group-btn">
        <SelectPickerB
          v-model="outcome"
          no-border-left="true"
          :options="outcome_select"
        />
      </div>
    </div>

    <div class="input-group flex-group">
      <span class="input-group-addon">Дата талона</span>
      <DateField2
        v-model="date_ticket"
        class="text-date-left"
      />
    </div>

    <button
      class="btn btn-blue-nb"
      :disabled="card_pk === -1"
      style="margin-top: 10px;margin-bottom: 5px;width: 100%"
      @click="create"
    >
      Сохранить
    </button>
  </div>
</template>

<script lang="ts">
import moment from 'moment';

import * as actions from '@/store/action-types';
import statisticsTicketsPoint from '@/api/statistics-tickets-point';
import SelectPickerB from '@/fields/SelectPickerB.vue';
import DateField2 from '@/fields/DateField2.vue';

export default {
  name: 'StatisticsTicketCreator',
  components: { SelectPickerB, DateField2 },
  props: {
    base: {
      type: Object,
      required: true,
    },
    card_pk: {
      type: Number,
    },
    ofname: {
      type: Number,
    },
  },
  data() {
    return {
      types: {
        visit: [],
        result: [],
        outcome: [],
        exclude: [],
        disp: [
          { pk: 0, title: 'Не состоит' },
          { pk: 1, title: 'Состоит' },
          { pk: 2, title: 'Взят' },
          { pk: 3, title: 'Снят' },
        ],
      },
      visit: -1,
      result: -1,
      outcome: -1,
      exclude: -1,
      disp: -1,
      disp_diagnos: '',
      date_ticket: moment().format('DD.MM.YYYY'),
      info: '',
      first_time: false,
      primary_visit: true,
    };
  },
  computed: {
    exclude_val() {
      if (this.disp === '3') {
        return this.exclude;
      }
      return -1;
    },
    disp_diagnos_val() {
      if (this.disp === '1' || this.disp === '2' || this.disp === '3') {
        return this.disp_diagnos;
      }
      return '';
    },
    outcome_select() {
      const r = [];
      for (const row of this.types.outcome) {
        r.push({ value: row.pk, label: row.title });
      }
      return r;
    },
    exclude_select() {
      const r = [];
      for (const row of this.types.exclude) {
        r.push({ value: row.pk, label: row.title });
      }
      return r;
    },
    visit_select() {
      const r = [];
      for (const row of this.types.visit) {
        r.push({ value: row.pk, label: row.title });
      }
      return r;
    },
    disp_select() {
      const r = [];
      for (const row of this.types.disp) {
        r.push({ value: row.pk, label: row.title });
      }
      return r;
    },
    result_select() {
      const r = [];
      for (const row of this.types.result) {
        r.push({ value: row.pk, label: row.title });
      }
      return r;
    },
    selected_visit() {
      for (const row of this.types.visit) {
        if (row.pk === this.visit) {
          return row;
        }
      }
      return { pk: -1, title: 'Не выбрано' };
    },
    selected_result() {
      for (const row of this.types.result) {
        if (row.pk === this.result) {
          return row;
        }
      }
      return { pk: -1, title: 'Не выбрано' };
    },
    selected_disp() {
      for (const row of this.types.disp) {
        if (row.pk === this.disp) {
          return row;
        }
      }
      return { pk: -1, title: 'Не выбрано' };
    },
  },
  created() {
    this.$store.dispatch(actions.INC_LOADING);
    statisticsTicketsPoint.getTicketsTypes().then((data) => {
      this.types.visit = data.visit;
      if (data.visit.length > 0) this.visit = data.visit[0].pk;
      this.types.result = data.result;
      if (data.result.length > 0) this.result = data.result[0].pk;
      this.disp = this.types.disp[0].pk;

      this.types.outcome = data.outcome;
      if (data.outcome.length > 0) this.outcome = data.outcome[0].pk;
      this.types.exclude = data.exclude;
      if (data.exclude.length > 0) this.exclude = data.exclude[0].pk;
    }).finally(() => {
      this.$store.dispatch(actions.DEC_LOADING);
    });
  },
  mounted() {
    window.$('.dropdown:not(.dropdown-large)').on('show.bs.dropdown', function () {
      const $btnDropDown = window.$(this).find('.dropdown-toggle');
      const $listHolder = window.$(this).find('.dropdown-menu');

      window.$(this).css('position', 'static');
      $listHolder.css({
        top: `${$btnDropDown.offset().top + $btnDropDown.outerHeight(true)}px`,
        left: `${$btnDropDown.offset().left}px`,
      });
      $listHolder.data('open', true);
    }).on('hidden.bs.dropdown', function () {
      const $listHolder = window.$(this).find('.dropdown-menu');
      $listHolder.data('open', false);
    });
  },
  methods: {
    create() {
      this.$store.dispatch(actions.INC_LOADING);
      statisticsTicketsPoint.sendTicket(
        this,
        [
          'card_pk',
          'visit',
          'info',
          'first_time',
          'primary_visit',
          'disp',
          'result',
          'outcome',
          'ofname',
          'date_ticket',
        ],
        {
          exclude: this.exclude_val,
          disp_diagnos: this.disp_diagnos_val,
        },
      )
        .then(() => {
          this.clear();
          this.$root.$emit('msg', 'ok', 'Статталон добавлен');
          this.$root.$emit('create-ticket');
        }).finally(() => {
          this.$store.dispatch(actions.DEC_LOADING);
        });
    },
    clear() {
      this.info = '';
      this.disp_diagnos = '';
      this.date_ticket = moment().format('DD.MM.YYYY');
    },
  },
};
</script>

<style scoped lang="scss">
  .flex-group {
    display: flex;
    flex-direction: row;
    margin-bottom: 5px;

    .input-group-addon {
      display: flex;
      flex: 0 0 175px;
      align-self: stretch;
      align-items: center;
      text-align: left;
    }

    & > .input-group-btn {
      width: 100%;
    }
  }
</style>

<style lang="scss">
  .text-date-left {
    text-align: left !important;
    padding-left: 10px !important;
  }

  .dropdown {
    position: inherit;
  }
</style>
