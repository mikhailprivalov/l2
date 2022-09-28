<template>
  <Modal
    ref="modal"
    show-footer="true"
    white-bg="true"
    max-width="800px"
    width="100%"
    margin-left-right="auto"
    margin-top="60px"
    style="z-index: 100;"
    @close="hide_message"
  >
    <span slot="header">Отчет по заявкам</span>
    <div
      slot="body"
      style="min-height: 100px"
      class="registry-body"
    >
      <div class="row">
        <div class="col-xs-6 text-left">
          <div class="input-group">
            <input
              v-model="date1"
              type="date"
              class="form-control"
            >
            <span
              class="input-group-addon addon-splitter"
              style="background-color: #fff; color: #000; height: 34px"
            >&mdash;</span>
            <input
              v-model="date2"
              type="date"
              :max="maxdate"
              class="form-control"
            >
          </div>
        </div>
        <div class="col-xs-6">
          <Treeselect
            v-model="current_hospital"
            :multiple="false"
            :disable-branch-nodes="true"
            :options="hospitals"
            placeholder="МО не выбрана"
            :append-to-body="true"
          />
        </div>
      </div>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-3" />
        <div class="col-xs-6">
          <button
            type="button"
            :disabled="current_hospital === '-2' || date1 === '' || date2 === ''"
            class="btn btn-primary-nb btn-blue-nb2"
            @click="make_report"
          >
            Создать отчёт в XLSX
          </button>
        </div>
        <div
          class="col-xs-3"
          style="padding-left: 0"
        >
          <button
            class="btn btn-primary-nb btn-blue-nb"
            type="button"
            @click="hide_message"
          >
            Отмена
          </button>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script lang="ts">
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import moment from 'moment';

import Modal from '@/ui-cards/Modal.vue';

export default {
  name: 'StatisticsMessagePrintModal',
  components: { Treeselect, Modal },
  props: {
    hospitals: {
      type: Array,
      required: false,
      default() {
        return [];
      },
    },
  },
  data() {
    return {
      current_hospital: '-1',
      date1: moment().format('YYYY-MM-DD'),
      date2: moment().format('YYYY-MM-DD'),
      card_pk: '',
    };
  },
  computed: {
    maxdate() {
      return moment(this.date1).add(59, 'days').format('YYYY-MM-DD');
    },
  },
  watch: {
    date1: {
      handler() {
        this.date2 = this.date1;
      },
    },
  },
  mounted() {
    this.$root.$on('hide_message_tickets', () => {
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
    });
  },
  methods: {
    make_report() {
      // eslint-disable-next-line max-len
      window.open(`/statistic/xls?type=message-ticket&hospital=${this.current_hospital}&date-start=${this.date1}&date-end=${this.date2}`, '_blank');
    },
    hide_message() {
      this.$root.$emit('hide_message_tickets');
    },
  },
};
</script>
