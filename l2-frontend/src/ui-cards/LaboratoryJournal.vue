<template>
  <div v-frag>
    <a href="#" @click.prevent="doOpen">
      Журнал
    </a>
    <MountingPortal mountTo="#portal-place" name="LaboratoryJournal" append v-if="open">
      <modal v-if="open" @close="open = false" show-footer="true" white-bg="true"
             max-width="710px" width="100%" marginLeftRight="auto" overflow-unset="true">
        <span slot="header">Журнал по активной лаборатории</span>
        <div slot="body">
          <div class="filters">
            <div class="input-group">
              <span class="input-group-addon">Дата подтверждения</span>
              <input class="form-control" type="date" v-model="date">
            </div>
            <hr/>
            <div class="input-group treeselect-noborder-left">
              <span class="input-group-addon">Источник финансирования</span>
              <treeselect :multiple="true" :disable-branch-nodes="true"
                          :options="fin_sources_options" :clearable="true"
                          placeholder="Источники финансирования не выбраны" v-model="fin_sources"/>
            </div>
            <hr/>
            <div class="input-group treeselect-noborder-left">
              <span class="input-group-addon">Группа исследований для журнала-списка</span>
              <treeselect :multiple="false" :disable-branch-nodes="true"
                          :options="groups" :clearable="false"
                          placeholder="Группа не выбрана" v-model="group"/>
            </div>
          </div>
          <hr/>
          <div class="row" style="text-align: center">
            <div class="col-xs-2"></div>
            <div class="col-xs-8" style="margin: 0 auto">
              <button type="button" class="btn btn-primary-nb" style="margin-bottom: 10px"
                      @click="createjournal()">Создать журнал-список
              </button>
            </div>
            <div class="col-xs-2"></div>
          </div>
          <div class="row" style="text-align: center">
            <div class="col-xs-2"></div>
            <div class="col-xs-8" style="margin: 0 auto">
              <button type="button" class="btn btn-primary-nb" style="margin-bottom: 10px"
                      @click="createjournaltable()">
                Создать журнал-таблицу
              </button>
            </div>
            <div class="col-xs-2"></div>
          </div>
          <div class="row" style="text-align: center">
            <div class="col-xs-2"></div>
            <div class="col-xs-8" style="margin: 0 auto">
              <button type="button" class="btn btn-primary-nb"
                      @click="createjournalcodes()">
                Создать журнал-список с кодами
              </button>
            </div>
            <div class="col-xs-2"></div>
          </div>
        </div>
        <div slot="footer">
          <div class="row">
            <div class="col-xs-4">
              <button @click="open = false" class="btn btn-primary-nb btn-blue-nb" type="button">
                Закрыть
              </button>
            </div>
          </div>
        </div>
      </modal>
    </MountingPortal>
  </div>
</template>

<script>
import moment from 'moment';

import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import Modal from '@/ui-cards/Modal.vue';
import * as actions from '@/store/action-types';
import api from '@/api';

export default {
  components: { Modal, Treeselect },
  name: 'LaboratoryJournal',
  data() {
    return {
      open: false,
      date: moment().format('YYYY-MM-DD'),
      fin_sources_options: [],
      fin_sources: [],
      groups: [],
      group: -2,
      lab_pk: -1,
    };
  },
  created() {
    this.$root.$on('change-laboratory', (pk) => {
      this.lab_pk = pk;
    });
  },
  methods: {
    async doOpen() {
      this.open = true;
      this.date = moment().format('YYYY-MM-DD');
      await this.$store.dispatch(actions.INC_LOADING);
      const data = await api('laboratory-journal-params');
      this.fin_sources_options = data.fin;
      this.fin_sources = [];
      this.groups = data.groups;
      this.group = -2;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    createjournal() {
      const { date } = this;
      const v = this.fin_sources;
      const { lab_pk } = this;
      const { group } = this;
      if (v.length === 0) {
        // @ts-ignore
        // eslint-disable-next-line no-undef
        window.$.amaran({
          theme: 'awesome no',
          content: {
            title: 'Не выбран источник финансирования',
            message: '',
            info: '',
            icon: 'fa fa-exclamation',
          },
          position: 'bottom right',
          delay: 5000,
        });
        return;
      }
      const arr = JSON.parse(`[${v}]`);
      window.open(`/results/journal?date=${date}&ist_f=${JSON.stringify(arr)}&group=${group}&lab_pk=${lab_pk}`, '_blank');
    },
    createjournaltable() {
      const { date } = this;
      const v = this.fin_sources;
      const { lab_pk } = this;
      if (v.length === 0) {
        // @ts-ignore
        // eslint-disable-next-line no-undef
        window.$.amaran({
          theme: 'awesome no',
          content: {
            title: 'Не выбран источник финансирования',
            message: '',
            info: '',
            icon: 'fa fa-exclamation',
          },
          position: 'bottom right',
          delay: 5000,
        });
        return;
      }
      const arr = JSON.parse(`[${v}]`);
      window.open(`/results/journal_table?date=${date}&ist_f=${JSON.stringify(arr)}&lab_pk=${lab_pk}`, '_blank');
    },
    createjournalcodes() {
      const { date } = this;
      const v = this.fin_sources;
      const { lab_pk } = this;
      const { group } = this;
      if (v.length === 0) {
        // @ts-ignore
        // eslint-disable-next-line no-undef
        window.$.amaran({
          theme: 'awesome no',
          content: {
            title: 'Не выбран источник финансирования',
            message: '',
            info: '',
            icon: 'fa fa-exclamation',
          },
          position: 'bottom right',
          delay: 5000,
        });
        return;
      }
      const arr = JSON.parse(`[${v}]`);
      window.open(`/results/journal?date=${date}&ist_f=${JSON.stringify(arr)}&group=${group}&codes=1&lab_pk=${lab_pk}`, '_blank');
    },
  },
};
</script>

<style lang="scss" scoped>
</style>
