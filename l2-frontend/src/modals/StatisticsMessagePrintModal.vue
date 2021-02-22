<template>
  <modal ref="modal" @close="hide_message" show-footer="true" white-bg="true" max-width="800px" width="100%"
         marginLeftRight="auto" margin-top>
    <span slot="header">Отчет по заявкам</span>
    <div slot="body" style="min-height: 100px" class="registry-body">
      <div class="row">
        <div class="col-xs-6 text-left" style="display: inline">
          <input type="date" style="height: 35px" v-model="date1">
          &mdash;
          <input type="date" style="height: 35px" v-model="date2" :max="maxdate">
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
            Печать
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
  import Treeselect from '@riophae/vue-treeselect'
  import '@riophae/vue-treeselect/dist/vue-treeselect.css'
  import Modal from '../ui-cards/Modal'
  import moment from "moment";

  export default {
    name: 'statistics-message-print-modal',
    components: {Treeselect, Modal,},
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

      }
    },
    watch: {
      date1: {
        handler() {
          this.date2 = this.date1
        },
      }
    },
    computed:{
      maxdate() {
        return moment(this.date1).add(59, 'days').format('YYYY-MM-DD');
      },
    },
    mounted() {
      console.log(this.date1)
      console.log(this.date2)
      this.$root.$on('hide_message_tickets', () => {
        if (this.$refs.modal) {
          this.$refs.modal.$el.style.display = 'none'
        }
      })
    },
    methods: {
      make_report() {
        window.open(`/statistic/xls?type=message-ticket&hospital=${this.current_hospital}&date-start=${this.date1}&date-end=${this.date2}`, '_blank')
      },
      hide_message() {
        this.$root.$emit('hide_message_tickets')
      }
    },
  }
</script>
