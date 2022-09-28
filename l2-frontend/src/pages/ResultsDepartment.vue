<template>
  <div>
    <div
      class="row"
      style="margin-top: 60px"
    >
      <div class="col-xs-2" />
      <div class="col-xs-4">
        <div class="panel panel-default panel-flt">
          <div class="panel-heading">
            <h3 class="panel-title">
              Быстрая печать результатов по отделению или врачу
            </h3>
          </div>
          <div class="panel-body">
            <div class="row">
              <div
                class="col-xs-6 text-param"
              >
                <label>
                  Дата результатов:
                </label>
              </div>
              <div class="col-xs-6">
                <input
                  v-model="date"
                  type="date"
                  class="date-display"
                >
              </div>
            </div>
            <div
              class="row margin"
            >
              <div
                class="col-xs-4 text-param"
              >
                <div class="checkbox">
                  <label>
                    <input
                      v-model="is_lab"
                      type="checkbox"
                    > Лабораторные
                  </label>
                </div>
              </div>
              <div
                class="col-xs-4 text-param"
              >
                <div class="checkbox">
                  <label>
                    <input
                      v-model="is_paraclinic"
                      type="checkbox"
                    > Параклинические
                  </label>
                </div>
              </div>
              <div
                class="col-xs-4 text-param"
              >
                <div class="checkbox">
                  <label>
                    <input
                      v-model="is_doc_refferal"
                      type="checkbox"
                    > Консультации
                  </label>
                </div>
              </div>
            </div>
            <div class="row">
              <div class="col-xs-5" />
              <div class="col-xs-7">
                <div
                  class="btn btn-blue-nb margin-param"
                  @click="print(false)"
                >
                  По отделению
                </div>
                <div
                  class="btn btn-blue-nb margin-param margin-left-param"
                  @click="print(true)"
                >
                  По врачу
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="col-xs-1" />
      <div class="col-xs-4">
        <div class="panel panel-default panel-flt">
          <div class="panel-heading">
            <h3 class="panel-title">
              Быстрая печать направлений по отделению или врачу
            </h3>
          </div>
          <div class="panel-body">
            <div class="row">
              <div
                class="col-xs-6 text-param"
              >
                <label>
                  Дата направлений:
                </label>
              </div>
              <div class="col-xs-6">
                <input
                  v-model="date"
                  type="date"
                  class="date-display"
                >
              </div>
            </div>
            <br>
            <div class="input-group">
              <span class="input-group-addon">Пользователь:</span>
              <treeselect
                v-model="user"
                class="treeselect-noborder treeselect-wide"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="users"
                :clearable="true"
                placeholder="Пользователь не выбан"
                :disabled="dep"
              />
            </div>
            <br>
            <div class="input-group">
              <span class="input-group-addon">Подразделение:</span>
              <treeselect
                v-model="dep"
                class="treeselect-noborder treeselect-wide"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="deps"
                :clearable="true"
                placeholder="Подразделение не выбано"
                :disabled="user"
              />
            </div>
            <div class="row">
              <div class="col-xs-5" />
              <div class="col-xs-7">
                <div
                  class="btn btn-blue-nb margin-param margin-left-param"
                  @click="printDirection"
                >
                  Печать направлений
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import moment from 'moment';
import Treeselect from '@riophae/vue-treeselect';

import * as actions from '@/store/action-types';
import directionsPoint from '@/api/directions-point';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import usersPoint from '@/api/user-point';

@Component({
  components: {
    Treeselect,
  },
  data() {
    return {
      date: moment().format('YYYY-MM-DD'),
      is_lab: true,
      is_paraclinic: true,
      is_doc_refferal: false,
      by_doc: false,
      users: [],
      user: null,
      dep: null,
    };
  },
  mounted() {
    this.loadUsers();
  },
})
export default class ResultsDepartment extends Vue {
  date: string;

  is_lab: boolean;

  is_paraclinic: boolean;

  is_doc_refferal: boolean;

  by_doc: boolean;

  users: any[];

  async print(byDoc) {
    await this.$store.dispatch(actions.INC_LOADING);
    // eslint-disable-next-line max-len
    const { results } = await directionsPoint.getDirectionsTypeDate(this, ['is_lab', 'is_paraclinic', 'is_doc_refferal', 'date'], { by_doc: byDoc });
    if (!results || results.length === 0) {
      this.$root.$emit('msg', 'error', 'Результатов не найдено');
    }
    this.$root.$emit('print:results', results);
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  async printDirection() {
    await this.$store.dispatch(actions.INC_LOADING);
    const { results } = await directionsPoint.getCreatedDirectionsbyDate(this, ['user', 'dep', 'date']);
    if (!results || results.length === 0) {
      this.$root.$emit('msg', 'error', 'Результатов не найдено');
    }
    this.$root.$emit('print:directions', results);
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  async loadUsers() {
    await this.$store.dispatch(actions.INC_LOADING);
    const { users } = await usersPoint.loadUsersByGroup({ group: '*' });
    this.users = users;
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  get deps() {
    return this.users.map(d => ({ id: d.id, label: d.label }));
  }
}
</script>

<style lang="scss" scoped>
.text-param {
  text-align: right;
  line-height: 1.26;
}

.date-display {
  display: inline-block
}

.margin-param {
  margin-bottom: 5px;
  margin-top: 15px;
}

.margin-left-param {
  margin-left: 20px;
}
</style>
