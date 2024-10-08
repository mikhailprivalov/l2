<template>
  <Modal
    ref="modal"
    show-footer="true"
    white-bg="true"
    max-width="780px"
    width="100%"
    margin-left-right="auto"
    margin-top
    @close="hide_modal"
  >
    <span
      slot="header"
    >Ведомость для передачи
    </span>
    <div
      slot="body"
      style="min-height: 200px"
      class="registry-body"
    >
      <div
        v-tippy="{ placement: 'right', arrow: true }"
        class="direct-date"
        title="Дата направления"
      >
        <DateRange
          v-model="date_range"
          small
        />
      </div>
      <table class="table table-bordered table-condensed table-sm-pd layout">
        <colgroup>
          <col width="260">
          <col width="200">
          <col width="270">
          <col width="30">
        </colgroup>
        <thead>
          <tr>
            <th>ФИО</th>
            <th>Направление</th>
            <th>Емкость</th>
            <th class="nopd noel">
              <input
                v-model="all_checked"
                type="checkbox"
              >
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="r in tubes"
            :key="r.tubeNumber"
          >
            <td>{{ r.fio }}</td>
            <td>{{ r.direction }}</td>
            <td>{{ r.tubeNumber }}</td>
            <td class="nopd">
              <input
                v-model="r.checked"
                type="checkbox"
              >
            </td>
          </tr>
        </tbody>
      </table>
      <Modal
        v-if="show_history_statement"
        ref="modalEdit"
        show-footer="true"
        white-bg="true"
        max-width="710px"
        width="100%"
        margin-left-right="auto"
        margin-top
        @close="hide_edit"
      >
        <span slot="header">История</span>
        <div
          slot="body"
          style="min-height: 200px; padding: 10px"
          class="registry-body"
        >
          <table class="table table-bordered table-condensed table-sm-pd layout">
            <colgroup>
              <col width="150">
              <col width="430">
              <col width="50">
            </colgroup>
            <thead>
              <tr>
                <th>Дата ведомости</th>
                <th>Сведения</th>
                <th>Печать</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="r in rowsHistory"
                :key="r.pk"
              >
                <td>{{ r.date }}</td>
                <td>{{ r.tubes }}</td>
                <td>
                  <button
                    v-tippy="{ placement: 'bottom', arrow: true }"
                    class="btn last btn-blue-nb nbr ml-1"
                    type="button"
                    title="Печать ведомости"
                    @click="printStatement(r.tubes)"
                  >
                    <i class="fa fa-print" />
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div slot="footer">
          <div class="row">
            <div class="col-xs-4">
              <button
                class="btn btn-primary-nb btn-blue-nb"
                type="button"
                @click="hide_edit"
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      </Modal>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-12">
          <div class="col-xs-4">
            <button
              class="btn btn-primary-nb btn-blue-nb"
              type="button"
              @click="show_history_statement_data"
            >
              История
            </button>
          </div>
          <div class="col-xs-4">
            <button
              class="btn btn-primary-nb btn-blue-nb"
              type="button"
              @click="hide_modal"
            >
              Закрыть
            </button>
          </div>
          <div class="col-xs-4">
            <button
              class="btn btn-primary-nb btn-blue-nb"
              type="button"
              @click="save"
            >
              Сохранить и печать
            </button>
          </div>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script lang="ts">
import moment from 'moment';
import _ from 'lodash';

import { valuesToString } from '@/utils';
import Modal from '@/ui-cards/Modal.vue';
import patientsPoint from '@/api/patients-point';
import * as actions from '@/store/action-types';

import DateRange from '../DateRange.vue';

export default {
  name: 'Statement',
  components: { Modal, DateRange },
  data() {
    return {
      rows: [],
      edit_pk: -2,
      td: moment().format('YYYY-MM'),
      edit_data: {
        date: '',
        data: '',
      },
      show_history_statement: false,
      rowsHistory: [],
      date_range: [
        moment()
          .subtract(this.daysSubtract, 'day')
          .format('DD.MM.YY'),
        moment().format('DD.MM.YY'),
      ],
      all_checked: false,
      tubes: [],
      checked: [],
    };
  },
  created() {
    this.load_data();
  },
  methods: {
    async show_history_statement_data() {
      this.show_history_statement = true;
      const data = await this.$api('statement/show-history');
      this.rowsHistory = data.rows || [];
    },
    hide_modal() {
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
      this.$root.$emit('hide_statement_data');
    },
    hide_edit() {
      if (this.$refs.modalEdit) {
        this.$refs.modalEdit.$el.style.display = 'none';
      }
      this.edit_pk = -2;
      this.show_history_statement = false;
      this.rowsHistory = [];
    },
    async load_data() {
      // eslint-disable-next-line max-len
      const data = await this.$api(
        'statement/select-tubes',
        {
          date_from: moment(this.date_range[0], 'DD.MM.YY').format('DD.MM.YYYY'),
          date_to: moment(this.date_range[1], 'DD.MM.YY').format('DD.MM.YYYY'),
        },
      );
      this.all_checked = false;
      this.tubes = data.rows || [];
      this.checked = [];
    },
    async printStatement(tubes) {
      window.open(`/forms/pdf?type=114.01&&filter=[${tubes}]`, '_blank');
    },
    async save() {
      await this.$store.dispatch(actions.INC_LOADING);
      const data = await this.$api('statement/save-tubes-statement', this.checked);
      await this.$store.dispatch(actions.DEC_LOADING);
      if (data.ok) {
        this.$root.$emit('msg', 'ok', 'Сохранено');
        this.printStatement(data.tubes);
      } else {
        this.$root.$emit('msg', 'error', data.message);
      }
      this.checked = [];
      this.rowsHistory = [];
      this.hide_edit();
      this.load_data();
    },

  },
  // eslint-disable-next-line vue/order-in-components
  watch: {
    date_range() {
      this.load_data();
    },
    all_checked() {
      for (const row of this.tubes) {
        row.checked = this.all_checked;
      }
    },
    tubes: {
      handler() {
        this.checked = [];
        for (const row of this.tubes) {
          if (row.checked) {
            this.checked.push({ tubeNumber: row.tubeNumber, direction: row.direction });
          }
        }
      },
      deep: true,
    },
  },
};
</script>

<style scoped lang="scss">
.align-button {
  float: right;
}

.layout {
  table-layout: fixed;
  font-size: 12px;
}

.modal-mask {
  align-items: stretch !important;
  justify-content: stretch !important;
}

::v-deep .panel-flt {
  margin: 41px;
  align-self: stretch !important;
  width: 100%;
  display: flex;
  flex-direction: column;
}

::v-deep .panel-body {
  flex: 1;
  padding: 0;
  height: calc(100% - 91px);
  min-height: 200px;
}

.direct-date {
  width: 126px;
}

</style>
