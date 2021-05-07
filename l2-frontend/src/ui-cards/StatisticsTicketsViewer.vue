<template>
  <div style="height: 100%;width: 100%;position: relative">
    <div class="top-picker">
      <date-field-nav style="width: 166px;align-self: stretch" :val.sync="date" :def="date"/>
      <button class="btn btn-blue-nb" @click="load"
              style="width: 42px;display: inline-block;align-self: stretch">
        <i class="glyphicon glyphicon-refresh"></i>
      </button>
      <button class="btn btn-blue-nb"
              style="width: 94px;display: inline-block;align-self: stretch" @click="print">
        <i class="glyphicon glyphicon-th-list"></i> Экспорт
      </button>
    </div>
    <div class="content-picker">
      <table class="table table-responsive table-bordered table-condensed"
             style="table-layout: fixed;margin-bottom: 0">
        <colgroup>
          <col width="25">
          <col width="150">
          <col width="60">
          <col width="95">
          <col width="55">
          <col>
          <col width="55">
          <col width="110">
          <col width="110">
          <col width="75">
          <col width="110">
          <col width="55">
        </colgroup>
        <thead>
        <tr>
          <th>№</th>
          <th>Пациент, карта</th>
          <th>Дата талона</th>
          <th>Цель посещения</th>
          <th>Первич. приём</th>
          <th>Код диагноза (МКБ 10), виды услуг, виды травм</th>
          <th>Впервые</th>
          <th>Результат обращения</th>
          <th>Исход</th>
          <th>Дисп. учёт</th>
          <th>Врач</th>
          <th></th>
        </tr>
        </thead>
      </table>
      <div style="align-self: stretch;flex: 0 0 calc(100% - 53px);overflow: auto">
        <table class="table table-responsive table-bordered table-condensed"
               style="table-layout: fixed;margin-bottom: 0">
          <colgroup>
            <col width="25">
            <col width="150">
            <col width="60">
            <col width="95">
            <col width="55">
            <col>
            <col width="55">
            <col width="110">
            <col width="110">
            <col width="75">
            <col width="110">
            <col width="55">
          </colgroup>
          <tbody>
          <tr v-for="row in data" :key="row.pk" :class="{invalid: row.invalid}">
            <td>{{row.n}}</td>
            <td>{{row.patinet}}<br/>Карта: {{row.card}}</td>
            <td>{{row.date_ticket}}</td>
            <td>{{row.purpose}}</td>

            <td v-if="row.primary">да</td>
            <td v-else>нет</td>

            <td v-html="row.info"></td>

            <td v-if="row.first_time">да</td>
            <td v-else>нет</td>

            <td>{{row.result}}</td>
            <td>{{row.outcome}}</td>
            <td>{{row.disp}}</td>
            <td class="doc">{{row.doc}}<br/>{{row.department}}</td>

            <td class="control-buttons">
              <div class="flex-wrap" v-if="row.can_invalidate">
                <button class="btn btn-sm btn-blue-nb" v-if="row.invalid"
                        @click="invalidate(row.pk, false)">
                  Вернуть
                </button>
                <button class="btn btn-sm btn-blue-nb" v-else
                        @click="invalidate(row.pk, true)">
                  Отменить
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="data.length === 0">
            <td class="text-center" colspan="11">За выбранную дату нет статталонов</td>
          </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import moment from 'moment';
import DateFieldNav from '../fields/DateFieldNav.vue';
import * as actions from '../store/action-types';
import statisticsTicketsPoint from '../api/statistics-tickets-point';

export default {
  name: 'statistics-tickets-viewer',
  components: {
    DateFieldNav,
  },
  data() {
    return {
      date: moment().format('DD.MM.YYYY'),
      data: [],
    };
  },
  created() {
    this.load();
    this.$root.$on('create-ticket', () => {
      if (this.date === moment().format('DD.MM.YYYY')) {
        this.load();
      }
    });
  },
  watch: {
    date() {
      this.load();
    },
  },
  methods: {
    print() {
      const users = encodeURIComponent(JSON.stringify([this.$store.getters.user_data.doc_pk]));
      const { date } = this;
      window.open(`/statistic/xls?type=statistics-tickets-print&users=${users}&date-start=${date}&date-end=${date}`, '_blank');
    },
    load() {
      this.$store.dispatch(actions.INC_LOADING);
      statisticsTicketsPoint.loadTickets(this, 'date').then((data) => {
        this.data = data.data;
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
      });
    },
    invalidate(pk, invalid) {
      this.$store.dispatch(actions.INC_LOADING);
      statisticsTicketsPoint.invalidateTicket({ pk, invalid }).then((data) => {
        if (!data.ok) {
          window.errmessage(data.message);
        }
        this.load();
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
      });
    },
  },
};
</script>

<style scoped lang="scss">
  .top-picker {
    height: 34px;
    background-color: #AAB2BD;
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    display: flex;
    align-items: stretch;
    justify-content: center;
    align-content: stretch;
  }

  .content-picker {
    overflow: hidden;
    display: flex;
    flex-direction: column;
    position: absolute;
    top: 34px;
    bottom: 0;
    left: 0;
    right: 0;
    font-size: 10px;
  }

  .content-picker .btn-blue-nb {
    font-size: 10px !important;
  }

  .top-picker .form-control, .top-picker .btn {
    border-radius: 0;
    border: none;
  }

  .top-picker .form-control {
    border-bottom: 1px solid #AAB2BD;
  }

  .invalid td:not(:hover):not(.control-buttons) {
    text-decoration: line-through;
    color: #bcbcbc;
  }

  .control-buttons {
    padding: 0;
    position: relative;

    .flex-wrap {
      display: flex;
      position: absolute;
      top: 0;
      left: 0;
      bottom: 0;
      right: 0;
      align-items: stretch;
      justify-content: stretch;

      .btn {
        white-space: normal;
        text-overflow: ellipsis;
        border-radius: 0;
        align-self: stretch;
        width: 100%;
        padding: 2px;
      }
    }
  }

  .doc {
    font-size: 12px;
    word-break: break-word;
  }
</style>
