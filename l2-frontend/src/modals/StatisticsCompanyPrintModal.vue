<template>
  <div class="modal fade" tabindex="-1">
    <div class="modal-dialog" style="max-width: 800px;width: 100%">
      <div class="modal-content">
        <div class="modal-header">
          <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span></button>
          <h4 class="modal-title">Акт по контрагенту</h4>
        </div>
        <div class="modal-body">
          <div class="row" style="margin-top: 10px; margin-bottom: 10px">
            <div class="col-xs-6 text-left" style="display: inline">
              <input type="date" style="height: 35px" v-model="date1">
               &mdash;
              <input type="date" style="height: 35px" v-model="date2">
            </div>
            <div class="col-xs-6">
               <treeselect :multiple="false" :disable-branch-nodes="true" :options="companies"
                    placeholder="Хирург не выбран" v-model="current_company"
               />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <div class="row">
            <div class="col-xs-3"></div>
            <div class="col-xs-6">
              <button type="button" @click="make_report"
                      :disabled="current_company === '-1' || date1 === '' || date2 === ''"
                      class="btn btn-primary-nb btn-blue-nb2">
                Печать
              </button>
            </div>
            <div class="col-xs-3" style="padding-left: 0">
              <button type="button" class="btn btn-primary-nb btn-blue-nb" data-dismiss="modal">Закрыть</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

export default {
  name: 'statistics-company-print-modal',
  components: { Treeselect },
  props: {
    companies: {
      type: Array,
      required: false,
      default() {
        return [];
      },
    },
  },
  data() {
    return {
      current_company: '-1',
      date1: '',
      date2: '',
    };
  },
  methods: {
    make_report() {
      window.open(`forms/pdf?type=200.01&company=${this.current_company}&date1=${this.date1}&date2=${this.date2}`, '_blank');
    },
  },
};
</script>
