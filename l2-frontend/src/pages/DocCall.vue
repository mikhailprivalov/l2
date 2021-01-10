<template>
  <div>
    <div class="panel panel-default panel-flt" style="margin: 20px;">
      <div class="panel-body">
        <div class="row">
          <div class="col-xs-6">
            <div class="input-group">
              <span class="input-group-addon">Дата и время</span>
              <input v-model="params.date" type="date" class="form-control"/>
              <span class="input-group-addon" style="background-color: #fff;height: 34px;width: 1px"></span>
              <input v-model="params.time_start" type="time" class="form-control"/>
              <span class="input-group-addon" style="background-color: #fff;color: #000; height: 34px">&mdash;</span>
              <input v-model="params.time_end" type="time" class="form-control"/>
            </div>
          </div>
          <div class="col-xs-6">
            <div class="input-group treeselect-noborder-left">
              <span class="input-group-addon">Цель</span>
              <treeselect :multiple="false" :disable-branch-nodes="true" :options="purposes"
                          placeholder="Цель не казана" v-model="params.purpose"
                          :append-to-body="true"
              />
            </div>
          </div>
        </div>
        <div class="row" style="margin-top:5px;">
          <div class="col-xs-3">
            <div class="input-group treeselect-noborder-left">
              <span class="input-group-addon">Больница</span>
              <treeselect :multiple="false" :disable-branch-nodes="true" :options="hospitals"
                          placeholder="Больница не выбрана" v-model="params.hospital"
                          :append-to-body="true"
              />
            </div>
          </div>
          <div class="col-xs-3">
            <div class="input-group treeselect-noborder-left">
              <span class="input-group-addon">Участок</span>
              <treeselect :multiple="false" :disable-branch-nodes="true" :options="districts"
                          placeholder="Участок не выбран" v-model="params.district"
                          :append-to-body="true"
              />
            </div>
          </div>
          <div class="col-xs-3">
            <div class="input-group treeselect-noborder-left">
              <span class="input-group-addon">Врач</span>
              <treeselect :multiple="false" :disable-branch-nodes="true" :options="docs_assigned"
                          placeholder="Врач не выбран" v-model="params.doc_assigned"
                          :append-to-body="true"
              />
            </div>
          </div>
          <div class="col-xs-3">
            <label>
              <input type="checkbox" v-model="params.is_external"> Внешние заявки
            </label>
            <label>
              <input type="checkbox" v-model="params.is_canceled"> Показать отмененные
            </label>
          </div>
        </div>

        <div class="btn btn-blue-nb" @click="print" style="float: right;">
          Печать
        </div>

        <div class="btn btn-blue-nb" @click="load(null)">
          Загрузить данные
        </div>
      </div>
    </div>
    <div class="not-loaded" v-if="!loaded">
      Данные не загружены<br/>
      <a class="a-under" href="#" @click.prevent="load(null)">загрузить</a>
    </div>
    <div v-else class="data">
      <div class="founded">
        Найдено записей: <strong>{{ params.total }}</strong>
      </div>
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
      <table class="table table-bordered table-condensed">
        <colgroup>
          <col>
          <col style="width: 95px">
          <col style="width: 95px">
          <col>
          <col>
          <col>
          <col>
          <col>
          <col>
        </colgroup>
        <thead>
        <tr>
          <td>Номер</td>
          <td>Создан</td>
          <td>На дату</td>
          <td>Пациент</td>
          <td>Больница, участок</td>
          <td>Телефон</td>
          <td>Цель</td>
          <td>Услуга, врач</td>
          <td>Примечания</td>
        </tr>
        </thead>
        <tbody>
        <tr v-for="r in rows">
          <td>{{ r.pk }}{{ r.externalNum ? ` — ${r.externalNum}` : '' }}</td>
          <td>
            {{ r.createdAt }}<br/>
            {{ r.createdAtTime }}
          </td>
          <td>{{ r.execAt }}</td>
          <td>
            {{ r.card }}
            <br/>
            {{ r.address }}
          </td>
          <td>
            {{ r.hospital }}<br/>
            {{ r.district }}
          </td>
          <td>{{ r.phone }}</td>
          <td>{{ r.purpose }}</td>
          <td>
            {{ r.research }}<br/>
            {{ r.docAssigned }}
          </td>
          <td>{{ r.comment }}</td>
        </tr>
        </tbody>
      </table>
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
  </div>
</template>

<script>
import moment from 'moment';
import _ from 'lodash';

import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import Paginate from 'vuejs-paginate';
import api from '@/api';
import * as action_types from '@/store/action-types';

export default {
  name: 'DocCall',
  components: {Treeselect, Paginate},
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
        district: -1,
        is_canceled: false,
        is_external: false,
        purpose: -1,
        doc_assigned: -1,
        hospital: -1,
        time_start: '00:00',
        time_end: '23:59',
        pages: 0,
        page: 1,
        total: 0,
      },
    };
  },
  computed: {
    watchParams() {
      return _.pick(this.params, [
        'date',
        'district',
        'is_canceled',
        'is_external',
        'purpose',
        'doc_assigned',
        'hospital',
        'time_start',
        'time_end',
      ]);
    },
  },
  watch: {
    watchParams: {
      deep: true,
      handler() {
        this.loaded = false;
      },
    },
  },
  async mounted() {
    await this.$store.dispatch(action_types.INC_LOADING);
    const data = await api('actual-districts');

    this.districts = data.rows;
    this.docs_assigned = data.docs;
    this.purposes = [{id: -1, label: 'Не выбрана'}, ...data.purposes];
    this.hospitals = data.hospitals;
    await this.$store.dispatch(action_types.DEC_LOADING);
  },
  methods: {
    print() {
      const {params} = this;
      window.open(`/forms/pdf?type=109.02&date=${params.date}&time_start=${params.time_start}&time_end=${params.time_end}&district=${params.district || -1}&doc=${params.doc_assigned || -1}&purpose=${params.purpose || -1}&hospital_pk=${params.hospital || -1}&external=${params.is_external ? 0 : 1}&cancel=${params.is_canceled ? 0 : 1}`);
    },
    async load(page_to_load) {
      if (page_to_load !== null) {
        this.params.page = page_to_load;
      } else {
        this.params.page = 1;
      }
      await this.$store.dispatch(action_types.INC_LOADING);
      const data = await api('doctor-call/search', this.params);
      this.params.pages = data.pages;
      this.params.page = data.page;
      this.params.total = data.total;
      this.rows = data.rows;
      await this.$store.dispatch(action_types.DEC_LOADING);
      this.loaded = true;
    },
  },
};

</script>

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
}
</style>
