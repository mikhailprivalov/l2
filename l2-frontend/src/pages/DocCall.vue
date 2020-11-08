<template>
  <div>
    <div class="row" style="margin-top: 60px">
      <div class="col-xs-4">
      </div>
      <div class="col-xs-4">
        <div class="panel panel-default panel-flt">
          <div class="panel-heading">
            <h3 class="panel-title">Вызова (обращения)</h3>
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
                  Время:
                </label>
              </div>
              <div class="col-xs-4">
                <input v-model="time_start" type="time" class="form-control"/>
              </div>
              <div class="col-xs-1"></div>
              <div class="col-xs-4">
                <input v-model="time_end" type="time" class="form-control"/>
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
            <div class="row" style="margin-top: 10px">
              <div class="col-xs-3" style="text-align: right;line-height: 1.26; margin-top: 10px;">
                <label>
                  Врач:
                </label>
              </div>
              <div class="col-xs-9">
                <treeselect :multiple="false" :disable-branch-nodes="true" :options="docs_assigned"
                    placeholder="Врач не выбран" v-model="doc_assigned"
                    :append-to-body="true"
                />
              </div>
            </div>
            <div class="row" style="margin-top: 10px">
              <div class="col-xs-3" style="text-align: right;line-height: 1.26; margin-top: 10px;">
                <label>
                  Цель:
                </label>
              </div>
              <div class="col-xs-9">
                <treeselect :multiple="false" :disable-branch-nodes="true" :options="purposes"
                    placeholder="Цель не казана" v-model="purpose"
                    :append-to-body="true"
                />
              </div>
            </div>
            <div class="row" style="margin-top: 10px">
              <div class="col-xs-3" style="text-align: right;line-height: 1.26; margin-top: 10px;">
                <label>
                  Больница:
                </label>
              </div>
              <div class="col-xs-9">
                <treeselect :multiple="false" :disable-branch-nodes="true" :options="hospitals"
                    placeholder="Больницв не выбрана" v-model="hospital"
                    :append-to-body="true"
                />
              </div>
            </div>

            <div class="row">
              <div class="col-xs-9">
                <div class="checkbox" style="text-align: left; margin-top: 20px;">
                  <label>
                    <input type="checkbox" v-model="is_extrnal">Внешние заявки
                  </label>
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
          is_extrnal: false,
          purposes: [],
          purpose: -1,
          docs_assigned: [],
          doc_assigned: -1,
          hospitals: [],
          hospital: -1,
          time_start: "00:00",
          time_end: "23:59",
      }
    },
    mounted() {
      api('actual-districts').then(rows => {
        this.districts = rows.rows;
        this.docs_assigned = rows.docs;
        this.purposes = rows.purposes;
        this.hospitals = rows.hospitals;
      });
    },
    methods: {
      print() {
        window.open(`/forms/pdf?type=109.02&date=${this.date}&time_start=${this.time_start}&time_end=${this.time_end}&district=${this.district}&doc=${this.doc_assigned}&purpose=${this.purpose}&hospital=${this.hospital}&external=${this.is_extrnal ? 0 : 1}&cancel=${this.is_canceled ? 0 : 1}`);
      },
    }
  }

</script>
