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
                <input v-model="date" type="date" class="form-control"/>
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
              <div class="col-xs-9">
                <div class="checkbox" style="text-align: right; margin-top: 20px;">
                  <label>
                    <input type="checkbox" v-model="is_canceled"> Показать отмененные
                  </label>
                </div>
              </div>
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
  import api from '@/api';

  export default {
    name: "DocCall",
    components: {Treeselect},
      data() {
        return {
          date: moment().format('YYYY-MM-DD'),
          district: -1,
          districts: [],
          is_canceled: false,
      }
    },
    mounted() {
      api('actual-districts').then(rows => this.districts = rows);
    },
    methods: {
      print() {
        window.open(`/forms/pdf?type=109.02&date=${this.date}&district=${this.district}&cancel=${this.is_canceled ? 0 : 1}`);
      },
    }
  }

</script>
