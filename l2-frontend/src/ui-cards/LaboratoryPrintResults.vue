<template>
  <div v-frag>
    <a
      href="#"
      @click.prevent="doOpen"
    >
      Печать результатов
    </a>
    <MountingPortal
      v-if="open"
      mount-to="#portal-place"
      name="LaboratoryPrintResults"
      append
    >
      <Modal
        v-if="open"
        show-footer="true"
        white-bg="true"
        max-width="710px"
        width="100%"
        margin-left-right="auto"
        @close="open = false"
      >
        <span slot="header">Печать результатов за день</span>
        <div slot="body">
          <div class="input-group">
            <span class="input-group-addon">Дата подтверждения</span>
            <input
              v-model="date"
              class="form-control"
              type="date"
            >
          </div>
          <div style="margin-top: 10px">
            <ResearchesPicker
              v-model="selected_researches"
              autoselect="none"
              :just_search="true"
              :hidetemplates="true"
              style="border-top: 1px solid #eaeaea;border-bottom: 1px solid #eaeaea;height: 350px;"
              :types-only="[2]"
            />
          </div>
          <div style="margin-top: 10px">
            <Treeselect
              v-model="otd"
              :multiple="false"
              :disable-branch-nodes="true"
              :options="otds"
              :clearable="false"
              placeholder="Отделение не выбрано"
            />
            <hr>
            <button
              type="button"
              class="btn btn-primary-nb"
              @click="dayprint_do"
            >
              Печать результатов за выбранную дату
            </button>
          </div>
        </div>
        <div slot="footer">
          <div class="row">
            <div class="col-xs-4">
              <button
                class="btn btn-primary-nb btn-blue-nb"
                type="button"
                @click="open = false"
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      </Modal>
    </MountingPortal>
  </div>
</template>

<script lang="ts">
import moment from 'moment';
import _ from 'lodash';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import Modal from '@/ui-cards/Modal.vue';
import ResearchesPicker from '@/ui-cards/ResearchesPicker.vue';
import * as actions from '@/store/action-types';

export default {
  name: 'LaboratoryPrintResults',
  components: { Modal, ResearchesPicker, Treeselect },
  data() {
    return {
      open: false,
      date: moment().format('YYYY-MM-DD'),
      selected_researches: [],
      otds: [],
      otd: -1,
    };
  },
  methods: {
    async doOpen() {
      this.open = true;
      this.selected_researches = [];
      this.date = moment().format('YYYY-MM-DD');
      this.otd = -1;
      await this.$store.dispatch(actions.INC_LOADING);
      this.otds = (await this.$api('otds')).rows;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async dayprint_do() {
      const researches = this.selected_researches;

      if (researches.length === 0) {
        // @ts-ignore
        // eslint-disable-next-line no-undef
        window.$.amaran({
          theme: 'awesome wrn',
          content: {
            title: 'Печать невозможна',
            message: 'Ничего не выбрано',
            info: '',
            icon: 'fa fa-exclamation',
          },
          position: 'bottom right',
          delay: 6000,
        });
        return;
      }

      await this.$store.dispatch(actions.INC_LOADING);

      await new Promise(r => {
        window.$.ajax({
          url: '/results/day',
          data: {
            date: this.date,
            researches: JSON.stringify(researches),
            otd: this.otd,
          },
        })
          .done(function (data) {
            if (Object.keys(data.directions).length > 0) {
              let strs = [];
              for (let l = 0; l < Object.keys(data.directions).length; l++) {
                strs = _.union(strs, data.directions[Object.keys(data.directions)[l]]);
              }
              window.printResults(strs);
              this.open = false;
            } else {
              // @ts-ignore
              // eslint-disable-next-line no-undef
              window.$.amaran({
                theme: 'awesome wrn',
                content: {
                  title: 'Печать невозможна',
                  message: 'Ничего не найдено',
                  info: '',
                  icon: 'fa fa-exclamation',
                },
                position: 'bottom right',
                delay: 6000,
              });
            }
          })
          .always(() => {
            r(0);
          });
      });

      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
};
</script>

<style lang="scss" scoped></style>
