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
              <input id="date1" type="date" value="2017-06-01" style="height: 35px">
               &mdash;
              <input id="date2" type="date" value="2017-06-01" style="height: 35px">
            </div>
            <div class="col-xs-6">
               <treeselect class="treeselect" :multiple="false" :disable-branch-nodes="true" :options="hirurgs"
                    placeholder="Хирург не выбран" v-model="current_hirurg"
               />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <div class="row">
            <div class="col-xs-3"></div>
            <div class="col-xs-6">
              <button type="button" @click="make_report"
                      :disabled="(user === '-1' || user === '') && research === '-1'"
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
  import DateSelector from '../fields/DateSelector.vue'
  import SelectPicker from '../fields/SelectPicker'
  import Treeselect from '@riophae/vue-treeselect'
  import '@riophae/vue-treeselect/dist/vue-treeselect.css'

  export default {
    name: 'statistics-company-print-modal',
    components: {DateSelector, SelectPicker, Treeselect,},
    props: {
      researches: {
        type: Array,
        required: false,
        default() {
          return [];
        },
      },
    },
    data() {
      return {
        research: '-1',
        hirurgs: [{"id": "-1", "label": "not found"}, {"id": "1", "label": "Большая компания"},
          {"id": "2", "label": "Не большая компания"},
          {"id": "3", "label": "Очень Большая компания"},
          {"id": "4", "label": "маленькая  компания"}],
        current_hirurg:  '',
      }
    },
    methods: {
      make_report() {
        window.open(`forms/docx?type=200.04&card_pk=199555`, '_blank')
      }
    },
  }
</script>
