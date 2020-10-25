<template>
  <div>
    <div class="row" style="margin-top: 60px">
      <div class="col-xs-4">
      </div>
      <div class="col-xs-4">
        <div class="panel panel-default panel-flt">
          <div class="panel-heading">
            <h3 class="panel-title">Вызова врача на дом</h3>
          </div>
          <div class="panel-body">
            <div class="row">
              <div class="col-xs-3" style="text-align: right;line-height: 1.26;">
                <label>
                  Дата:
                </label>
              </div>
              <div class="col-xs-9">
                <input v-model="date" type="date" style="display: inline-block"/>
              </div>
            </div>
            <div class="row" style="margin-top: 10px">
              <div class="col-xs-3" style="text-align: right;line-height: 1.26; margin-top: 10px;">
                <label>
                  Участок:
                </label>
              </div>
              <div class="col-xs-9">
                <treeselect :multiple="false" :disable-branch-nodes="true" :options="districts"
                    placeholder="Участок не выбран" v-model="district"
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
  import * as action_types from "../store/action-types";
  import Treeselect from "@riophae/vue-treeselect";
  import '@riophae/vue-treeselect/dist/vue-treeselect.css'
  import moment from "moment";

  export default {
    name: "DocCall",
    components: {Treeselect},
      data() {
        return {
          date: moment().format('YYYY-MM-DD'),
          district: -1,
          districts: [{id: -1, label: 'Не выбран'}, {id: 1, label: '1'}, {id: 2, label: '2'}, {id: 3, label: '3'}, {id: 4, label: '4'}],
      }
    },
    methods: {
      print() {
        window.open(`/forms/pdf?type=109.02&date=${this.date}&district=${this.district}`);
      },
    }
  }

</script>
