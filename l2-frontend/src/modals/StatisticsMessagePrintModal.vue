<template>
  <modal ref="modal" @close="hide_message" show-footer="true" white-bg="true" max-width="800px" width="100%"
         marginLeftRight="auto" margin-top="60px" style="z-index: 100;">
    <span slot="header">Отчет по заявкам</span>
    <div slot="body" style="min-height: 100px" class="registry-body">
      <div class="row">
        <div class="col-xs-6 text-left">
          <div class="input-group">
            <input type="date" v-model="date1" class="form-control">
            <span class="input-group-addon addon-splitter"
                  style="background-color: #fff; color: #000; height: 34px">&mdash;</span>
            <input type="date" v-model="date2" :max="maxdate" class="form-control">
          </div>
        </div>
        <div class="col-xs-6">
          <treeselect :multiple="false" :disable-branch-nodes="true" :options="hospitals"
                      placeholder="МО не выбрана" v-model="current_hospital" :append-to-body="true"
          />
        </div>
      </div>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-3"></div>
        <div class="col-xs-6">
          <button type="button" @click="make_report"
                  :disabled="current_hospital === '-2' || date1 === '' || date2 === ''"
                  class="btn btn-primary-nb btn-blue-nb2">
            Создать отчёт в XLSX
          </button>
        </div>
        <div class="col-xs-3" style="padding-left: 0">
          <button @click="hide_message" class="btn btn-primary-nb btn-blue-nb" type="button">
            Отмена
          </button>
        </div>
      </div>
    </div>
  </modal>
</template>

<script>
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import moment from 'moment';
import Modal from '../ui-cards/Modal.vue';

export default {
  name: 'statistics-message-print-modal',
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
  watch: {
    date1: {
      handler() {
        this.date2 = this.date1;
      },
    },
  },
  computed: {
    maxdate() {
      return moment(this.date1).add(59, 'days').format('YYYY-MM-DD');
    },
  },
  mounted() {
    console.log(this.date1);
    console.log(this.date2);
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
