<template>
  <div>
    <form class="panel panel-default panel-flt" style="margin: 20px;" @submit.prevent="load(null)">
      <div class="panel-body" style="overflow: visible;">
        <div class="row" style="margin-top:5px;">
          <div class="col-xs-6">
            <div class="input-group treeselect-noborder-left">
              <span class="input-group-addon">Больница</span>
              <treeselect :multiple="false" :disable-branch-nodes="true" :options="hospitals"
                          placeholder="Больница не выбрана" v-model="params.hospital"
                          :disabled="Boolean(params.number)"
                          :clearable="false" class="treeselect-wide"
              />
            </div>
          </div>
          <div class="col-xs-2">
            <div class="input-group date-time">
              <span class="input-group-addon">Дата</span>
              <span class="input-group-addon" style="padding: 0;border: none;">
                <date-field-nav-2 v-model="params.date" right
                                  :disabled="Boolean(params.number || params.without_date)"
                                  w="140px" :brn="false"/>
              </span>
            </div>
          </div>
          <div class="col-xs-1"></div>
          <div class="col-xs-3">
            <div class="input-group treeselect-noborder-left">
              <span class="input-group-addon">Статус</span>
              <select v-model="params.status" :readonly="Boolean(params.number)" class="form-control">
                <option :value="0">Все</option>
                <option :value="1">Новые</option>
                <option :value="2">Выполнены</option>
              </select>
            </div>
          </div>
        </div>
        <div style="margin-top: 5px">
          <a href="#" class="a-under pull-right" @click.prevent="print">
            Печать
          </a>
          <a href="#" class="a-under pull-right" @click.prevent="show_statistics_message_tickets" style="padding-right: 10px">
             Статистика
          </a>
        </div>
      </div>
    </form>
    <div class="not-loaded" v-if="!loaded">
      Данные не загружены<br/>
      <a class="a-under" href="#" @click.prevent="load(null)">загрузить</a>
    </div>
    <div v-else class="data">
      <table class="table table-bordered table-condensed table-hover">
        <colgroup>
          <col style="width: 45px">
          <col style="width: 75px">
          <col style="width: 15px">
          <col style="width: 20px">
          <col style="width: 70px">
          <col style="width: 25px">
          <col style="width: 25px">
          <col style="width: 30px">
          <col style="width: 15px">
        </colgroup>
        <thead>
        <tr>
          <td>Медицинская организация</td>
          <td>Пациент</td>
          <td>№ заявки</td>
          <td>Дата заявки</td>
          <td>Эпид №</td>
          <td>№ в базе</td>
          <td>Эпид № - дата</td>
          <td>Исполнитель</td>
          <td>Заполнить</td>
        </tr>
        </thead>
        <tbody>
        <tr v-for="r in rows" :key="r.pk">
          <DocCallRow :r="r"/>
        </tr>
        </tbody>
      </table>
      <div class="founded">
        Найдено записей: <strong>{{ params.total }}</strong>
      </div>
    </div>
    <statistics-message-print-modal v-if="statistics_tickets" :hospitals="hospitals"/>
  </div>
</template>

<script lang="ts">
import moment from 'moment';
import _ from 'lodash';

import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import api from '@/api';
import * as actions from '@/store/action-types';
import DocCallRow from '@/pages/DocCallRow.vue';
import DateFieldNav2 from '@/fields/DateFieldNav2.vue';
import StatisticsMessagePrintModal from '@/modals/StatisticsMessagePrintModal.vue';

export default {
  name: 'ExtraNotification',
  components: {
    DateFieldNav2, DocCallRow, Treeselect, StatisticsMessagePrintModal,
  },
  data() {
    return {
      districts: [],
      purposes: [],
      docs_assigned: [],
      hospitals: [],
      rows: [],
      loaded: false,
      params: {
        date: moment().format('YYYY-MM-DD'),
        status: 0,
        hospital: -1,
      },
    };
  },
  beforeMount() {
    this.$store.dispatch(actions.GET_USER_DATA);
    this.$store.watch((state) => state.user.data, (oldValue, newValue) => {
      this.params.hospital = newValue.hospital || -1;
    });
  },
  computed: {
    watchParams() {
      return _.pick(this.params, [
        'date',
        'status',
        'hospital',
      ]);
    },
  },
  watch: {
    watchParams: {
      deep: true,
      handler() {
        this.load(null);
      },
    },
    watchParamsDebounce: {
      deep: true,
      handler: _.debounce(function () {
        this.load(null);
      }, 400),
    },
    l2_only_doc_call: {
      handler() {
        if (this.l2_only_doc_call) {
          // Подумать над этим
          // this.params.is_external = true;
        }
      },
      immediate: true,
    },
  },
  async mounted() {
    await this.$store.dispatch(actions.INC_LOADING);
    const data = await api('actual-districts');
    const { hospitals } = await api('hospitals', { filterByUserHospital: true });

    this.districts = data.rows;
    this.docs_assigned = data.docs;
    this.purposes = [{ id: -1, label: 'Не выбрана' }, ...data.purposes];
    this.hospitals = hospitals;
    this.$root.$on('hide_message_tickets', () => this.hide_statistcs());
    await this.$store.dispatch(actions.DEC_LOADING);
  },
  methods: {
    print() {
      const { params } = this;
      // eslint-disable-next-line max-len
      window.open(`/forms/pdf?type=109.02&date=${params.date}&time_start=${params.time_start}&time_end=${params.time_end}&district=${params.district || -1}&doc=${params.doc_assigned || -1}&purpose=${params.purpose || -1}&hospital_pk=${params.hospital || -1}&external=${params.is_external ? 0 : 1}&cancel=${params.is_canceled ? 0 : 1}`);
    },
    async load() {
      await this.$store.dispatch(actions.INC_LOADING);
      const data = await api('extra-notification/search', this.params);
      this.params.pages = data.pages;
      this.params.page = data.page;
      this.params.total = data.total;
      this.rows = data.rows;
      await this.$store.dispatch(actions.DEC_LOADING);
      this.loaded = true;
    },
    show_statistics_message_tickets() {
      this.statistics_tickets = true;
    },
    hide_statistcs() {
      this.statistics_tickets = false;
    },
  },
};

</script>

<style>
.pagination {
  margin-top: 0 !important;
}
</style>

<style lang="scss" scoped>
.not-loaded {
  text-align: center;
  color: grey;
}

.data {
  padding: 0 20px;
}

.founded {
  text-align: center;
  padding: 5px;
  margin-top: -5px;
}

.addon-splitter {
  background-color: #fff;
  &.disabled {
    opacity: .4;
  }
}

.date-time {
  input {
    line-height: 1;
  }
}
</style>
