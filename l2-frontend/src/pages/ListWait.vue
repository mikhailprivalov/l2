<template>
  <div>
    <div class="row" style="margin-top: 100px;min-height: 400px;">
      <div class="col-xs-4">
      </div>
      <div class="col-xs-4">
        <div class="panel panel-default panel-flt">
          <div class="panel-heading">
            <h3 class="panel-title">Лист ожидания</h3>
          </div>
          <div class="panel-body">
            <div class="row">
              <div class="col-xs-3" style="text-align: right; line-height: 1.4;">
                <label style="margin-top: 5px">
                  Дата:
                </label>
              </div>
              <div class="col-xs-5">
                <date-range v-model="date"/>
              </div>
              <div class="col-xs-4"/>
            </div>
            <div class="row" style="margin-top: 10px">
              <div class="col-xs-3" style="text-align: right; line-height: 1.26; margin-top: 10px;">
                <label>
                  Услуги:
                </label>
              </div>
              <div class="col-xs-9">
                <treeselect :multiple="false" :disable-branch-nodes="true" :options="researches"
                    placeholder="Все услуги" v-model="research"
                    :append-to-body="true"
                />
              </div>
            </div>
            <div class="row">
              <div class="col-xs-9"></div>
              <div class="col-xs-3">
                <div class="btn btn-blue-nb" style="margin-bottom: 5px;margin-top: 15px; margin-left: 20px;"
                     @click="print(true)">
                  Печать
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  import Treeselect from "@riophae/vue-treeselect";
  import '@riophae/vue-treeselect/dist/vue-treeselect.css'
  import moment from "moment";
  import DateRange from "../ui-cards/DateRange"

  export default {
    name: "ListWait",
    components: {Treeselect, DateRange},
      data() {
        return {
          date: [moment().format('DD.MM.YYYY'), moment().format('DD.MM.YYYY')],
          research: -1,
          researches: [{id: -1, label: 'Все услуги'}, {id: 1, label: 'one'}, {id: 2, label: '2'}, {id: 3, label: 'three'}, {id: 4, label: '4'}],
      }
    },
    methods: {
      print() {
        console.log(this.date)
        window.open(`/forms/pdf?type=109.03&date=${this.date}&research_pk=${this.research}`);
      },
    }
  }

</script>
