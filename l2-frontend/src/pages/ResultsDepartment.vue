<template>
  <div>
    <br/>
    <br/>
    <br/>
    <div class="row">
      <div class="col-xs-4">
      </div>
      <div class="col-xs-4">
        <div class="panel panel-default panel-flt">
          <div class="panel-heading">
            <h3 class="panel-title">Быстрая печать результатов</h3>
          </div>
          <div class="panel-body">
            <div class="row">
              <div class="col-xs-6" style="text-align: right;line-height: 1.26;">
                <label>
                  Дата результатов:
                </label>
              </div>
              <div class="col-xs-6">
                <input v-model="date" type="date" style="display: inline-block"/>
              </div>
            </div>
            <div class="row" style="margin-bottom: 5px; margin-top: 15px">
              <div class="col-xs-4" style="text-align: right;line-height: 1.26;">
                <div class="checkbox">
                  <label>
                    <input type="checkbox" v-model="is_lab"> Лабораторные
                  </label>
                </div>
              </div>
              <div class="col-xs-4" style="text-align: right;line-height: 1.26;">
                <div class="checkbox">
                  <label>
                    <input type="checkbox" v-model="is_paraclinic"> Параклинические
                  </label>
                </div>
              </div>
              <div class="col-xs-4" style="text-align: right;line-height: 1.26;">
                <div class="checkbox">
                  <label>
                    <input type="checkbox" v-model="is_doc_reffearl"> Консультации
                  </label>
                </div>
              </div>
            </div>
            <div class="row">
              <div class="col-xs-9"></div>
              <div class="col-xs-3">
                <div class="btn btn-blue-nb" style="margin-bottom: 5px;margin-top: 15px;"
                     @click="print()">
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
  import directions_point from '../api/directions-point'
  import moment from "moment";

  export default {
    name: "results-department",
    data() {
      return {
        date: moment().format('YYYY-MM-DD'),
        is_lab: true,
        is_paraclinic: true,
        is_doc_reffearl: false,
      }
    },
    methods: {
      async print(type) {
        await this.$store.dispatch(action_types.INC_LOADING)
        const {results} = await directions_point.getDirectionsTypeDate({
          'is_lab': this.is_lab, 'is_paraclinic': this.is_paraclinic, 'is_doc_reffearl': this.is_doc_reffearl,
          'date': this.date});
        this.print_results(results);
        await this.$store.dispatch(action_types.DEC_LOADING)
      },
      print_results(pk) {
        this.$root.$emit('print:results', pk)
      },
    }
  }

</script>

