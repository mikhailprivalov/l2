<template>
  <div class="report-root">
    <h3>{{ title }}</h3>
    <div class="filters">
      <div class="row">
        <div class="col-xs-1"></div>
        <div class="col-xs-3">
          <div class="input-group treeselect-noborder-left">
            <span class="input-group-addon">Мониторинг</span>
            <treeselect
              :multiple="false"
              :disable-branch-nodes="true"
              :options="monitorings"
              placeholder="Мониторинг не выбран"
              v-model="research"
            />
          </div>
        </div>
        <div class="col-xs-5">
          <div class="input-group">
            <span class="input-group-addon">Дата или начало периода</span>
            <input class="form-control" type="date" v-model="date" />
            <span class="input-group-addon">Час</span>
            <select class="form-control" v-model="hour">
              <option v-for="h in HOURS" :key="h.id" :value="h.id">{{ h.label }}</option>
            </select>
          </div>
        </div>
        <div class="col-xs-2">
          <button class="btn btn-blue-n btn-block" @click="load_data" :disabled="research === null">
            Загрузить данные
          </button>
        </div>
        <div class="col-xs-1"></div>
      </div>
    </div>
    <table class="table table-bordered table-condensed table-striped" style="table-layout: fixed" v-if="data">
      <colgroup>
        <col style="width: 220px" />
        <col style="width: 150px" />
        <col style="width: 90px" />
        <template v-for="(t, i) in data.titles">
          <col v-for="(f, j) in t.fields" :key="`${i}_${j}`" />
        </template>
      </colgroup>
      <thead>
        <tr>
          <th rowspan="2">Организация</th>
          <th rowspan="2">Подтверждено</th>
          <th rowspan="2">№</th>
          <th v-for="(t, i) in data.titles" :key="i" :colspan="t.fields.length" class="param-title">
            {{ t.groupTitle }}
          </th>
        </tr>
        <tr>
          <template v-for="(t, i) in data.titles">
            <th v-for="(f, j) in t.fields" :key="`${i}_${j}`" class="param-title">
              {{ f }}
            </th>
          </template>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(r, i) in data.rows" :key="i">
          <td>
            {{ r.hospTitle }}
          </td>
          <td>
            {{ r.confirm }}
          </td>
          <td>
            {{ r.direction }}
          </td>
          <template v-for="(v, j) in r.values">
            <td v-for="(rv, k) in v" :key="`${j}_${k}`">
              {{ rv }}
            </td>
          </template>
        </tr>
        <tr v-if="data.total && data.total.length > 0">
          <th colspan="3">Итого</th>
          <template v-for="(v, j) in data.total">
            <td v-for="(rv, k) in v" :key="`${j}_${k}`">
              {{ rv }}
            </td>
          </template>
        </tr>
        <tr v-for="(h, i) in data.empty_hospital" :key="i">
          <th>{{ h }}</th>
          <th :colspan="2 + data.titles.reduce((a, b) => a + b.fields.length, 0)">Мониторинг не заполнен</th>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script lang="ts">
import { mapGetters } from 'vuex';
import moment from 'moment';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import api from '@/api';
import * as actions from '@/store/action-types';

const HOURS = [{ id: '-', label: 'нет' }];

for (let i = 0; i < 24; i++) {
  const id = i < 10 ? `0${i}` : String(i);
  const label = `${id}:00`;
  HOURS.push({ id, label });
}

export default {
  components: {
    Treeselect,
  },
  data() {
    return {
      title: 'Просмотр мониторингов',
      research: null,
      date: moment().format('YYYY-MM-DD'),
      hour: '-',
      HOURS,
      data: null,
    };
  },
  async mounted() {
    await this.$store.dispatch(actions.INC_LOADING);
    await this.$store.dispatch(actions.GET_RESEARCHES);
    await this.$store.dispatch(actions.DEC_LOADING);
  },
  computed: {
    ...mapGetters(['researches']),
    monitorings() {
      return (this.researches['-12'] || []).map(r => ({ id: r.pk, label: r.title }));
    },
  },
  methods: {
    async load_data() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { rows } = await api('/monitorings/search', this, ['research', 'date', 'hour']);
      this.data = rows;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
};
</script>

<style scoped lang="scss">
.report-root {
  padding: 0 10px;
  max-width: 1900px;
  max-width: 0 auto;
}

.filters {
  margin-bottom: 10px;
}

.param-title {
  font-size: 12px;
  word-break: break-word;
}
</style>
