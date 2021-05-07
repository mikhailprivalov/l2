<template>
  <div>
    <form class="panel panel-default panel-flt" style="margin: 20px;" @submit.prevent="load(null)">
      <div class="panel-body" style="overflow: visible;">
        <div class="row">
          <div class="col-xs-6">
            <div class="input-group date-time">
              <span class="input-group-addon">Дата и время</span>
              <span class="input-group-addon" style="padding: 0;border: none;">
                <date-field-nav-2 v-model="params.date" right
                                  :disabled="Boolean(params.number || params.without_date)"
                                  w="140px" :brn="false"/>
              </span>
              <span class="input-group-addon addon-splitter"
                    :class="{disabled: Boolean(params.number || params.without_date)}"
                    style="height: 34px;width: 1px"></span>
              <input v-model="params.time_start" type="time" class="form-control"
                     :disabled="Boolean(params.number|| params.without_date)"/>
              <span class="input-group-addon addon-splitter"
                    :class="{disabled: Boolean(params.number || params.without_date)}"
                    style="color: #000; height: 34px">&mdash;</span>
              <input v-model="params.time_end" type="time" class="form-control"
                     :disabled="Boolean(params.number|| params.without_date)"/>
            </div>
          </div>
          <div class="col-xs-2">
            <div class="input-group treeselect-noborder-left">
              <span class="input-group-addon">Цель</span>
              <treeselect :multiple="false" :disable-branch-nodes="true" :options="purposes"
                          placeholder="Цель не казана" v-model="params.purpose" :disabled="Boolean(params.number)"
                          :append-to-body="true" :clearable="false"
              />
            </div>
          </div>
          <div class="col-xs-2">
            <div class="input-group treeselect-noborder-left">
              <span class="input-group-addon">Статус</span>
              <select v-model="params.status" :readonly="Boolean(params.number)" class="form-control">
                <option :value="-1">Все</option>
                <option :value="1">Новая заявка</option>
                <option :value="2">В работе</option>
                <option :value="3">Выполнено</option>
                <option :value="4">Отмена</option>
              </select>
            </div>
          </div>
          <div class="col-xs-2">
            <div class="input-group treeselect-noborder-left">
              <span class="input-group-addon">Номер</span>
              <input v-model.trim="params.number" class="form-control" placeholder="без других параметров"/>
            </div>
          </div>
        </div>
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
          <div class="col-xs-3">
            <div class="input-group treeselect-noborder-left">
              <span class="input-group-addon">Участок</span>
              <treeselect :multiple="false" :disable-branch-nodes="true" :options="districts"
                          placeholder="Участок не выбран" v-model="params.district"
                          :append-to-body="true" :disabled="Boolean(params.number)"
                          :clearable="false"
              />
            </div>
          </div>
          <div class="col-xs-3">
            <div class="input-group treeselect-noborder-left">
              <span class="input-group-addon">Врач</span>
              <treeselect :multiple="false" :disable-branch-nodes="true" :options="docs_assigned"
                          placeholder="Врач не выбран" v-model="params.doc_assigned"
                          :append-to-body="true" :disabled="Boolean(params.number)"
                          :clearable="false"
              />
            </div>
          </div>
        </div>
        <div style="margin: 5px 0">
          <patient-picker-doc-call v-model="params.card_pk"
                                   :disabled="Boolean(params.number)"/>
        </div>
        <div style="margin-top: 5px">
          <a href="#" class="a-under pull-right" @click.prevent="print">
            Печать
          </a>
          <a href="#" class="a-under pull-right" @click.prevent="show_statistics_message_tickets" style="padding-right: 10px">
             Статистика
          </a>
          <label class="checkbox-inline">
            <input type="checkbox" v-model="params.is_external" :disabled="Boolean(params.number)"> Внешние заявки
          </label>
          <label class="checkbox-inline">
            <input type="checkbox" v-model="params.without_date" :disabled="Boolean(params.number)"> Искать по всем
            датам
          </label>
          <label class="checkbox-inline">
            <input type="checkbox" v-model="params.is_canceled"
                   :disabled="Boolean(params.number)"> Показать отмененные
          </label>
          <label class="checkbox-inline">
            <input type="checkbox" v-model="params.my_requests"
                   :disabled="Boolean(params.number)"> Мои заявки
          </label>
        </div>
      </div>
    </form>
    <div class="not-loaded" v-if="!loaded">
      Данные не загружены<br/>
      <a class="a-under" href="#" @click.prevent="load(null)">загрузить</a>
    </div>
    <div v-else class="data">
      <div>
        <button class="btn btn-blue-nb pull-right" @click="load(params.page)">
          <i class="fa fa-refresh"></i>
        </button>
        <paginate
          v-model="params.page"
          :page-count="params.pages"
          :page-range="4"
          :margin-pages="2"
          :click-handler="load"
          prev-text="Назад"
          next-text="Вперёд"
          container-class="pagination"
        />
      </div>
      <table class="table table-bordered table-condensed table-hover">
        <colgroup>
          <col>
          <col style="width: 95px">
          <col>
          <col style="width: 125px">
          <col style="width: 150px">
          <col>
          <col style="width: 150px">
          <col style="width: 95px">
          <col style="width: 90px">
        </colgroup>
        <thead>
        <tr>
          <td>Номер</td>
          <td>Создан</td>
          <td>Пациент</td>
          <td>Телефон</td>
          <td>Цель</td>
          <td>Примечания</td>
          <td>Исполнитель</td>
          <td>Статус</td>
          <td>История</td>
        </tr>
        </thead>
        <tbody>
        <tr v-for="r in rows" :key="r.pk">
          <DocCallRow :r="r"/>
        </tr>
        </tbody>
      </table>
      <div>
        <button class="btn btn-blue-nb pull-right" @click="load(params.page)">
          <i class="fa fa-refresh"></i>
        </button>
        <paginate
          v-model="params.page"
          :page-count="params.pages"
          :page-range="4"
          :margin-pages="2"
          :click-handler="load"
          prev-text="Назад"
          next-text="Вперёд"
          container-class="pagination"
        />
      </div>
      <div class="founded">
        Найдено записей: <strong>{{ params.total }}</strong>
      </div>
    </div>
    <statistics-message-print-modal v-if="statistics_tickets" :hospitals="hospitals"/>
  </div>
</template>

<script>
import moment from 'moment';
import _ from 'lodash';

import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import Paginate from 'vuejs-paginate';
import api from '@/api';
import * as actions from '@/store/action-types';
import DocCallRow from '@/pages/DocCallRow.vue';
import DateFieldNav2 from '@/fields/DateFieldNav2.vue';
import StatisticsMessagePrintModal from '@/modals/StatisticsMessagePrintModal.vue';
import PatientPickerDocCall from '@/ui-cards/PatientPickerDocCall.vue';

export default {
  name: 'DocCall',
  components: {
    DateFieldNav2, DocCallRow, Treeselect, Paginate, StatisticsMessagePrintModal, PatientPickerDocCall,
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
        card_pk: -1,
        status: -1,
        district: -1,
        is_canceled: false,
        my_requests: false,
        without_date: false,
        is_external: false,
        purpose: -1,
        doc_assigned: -1,
        hospital: -1,
        time_start: '00:00',
        time_end: '23:59',
        pages: 0,
        page: 1,
        total: 0,
        number: '',
      },
      statistics_tickets: false,
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
        'card_pk',
        'status',
        'district',
        'without_date',
        'is_canceled',
        'my_requests',
        'is_external',
        'purpose',
        'doc_assigned',
        'hospital',
      ]);
    },
    watchParamsDebounce() {
      return _.pick(this.params, [
        'number',
        'time_start',
        'time_end',
      ]);
    },
    l2_only_doc_call() {
      return this.$store.getters.modules.l2_only_doc_call;
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
    async load(page_to_load) {
      if (page_to_load !== null) {
        this.params.page = page_to_load;
      } else {
        this.params.page = 1;
      }
      await this.$store.dispatch(actions.INC_LOADING);
      const data = await api('doctor-call/search', this.params);
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
