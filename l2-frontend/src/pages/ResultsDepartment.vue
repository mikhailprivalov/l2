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
            <div class="row">
              <div class="col-xs-4" style="text-align: right;line-height: 1.26;">
                <div class="btn btn-blue-nb" style="margin-bottom: 5px;margin-top: 15px"
                     @click="print('is_lab')">
                  Лабораторные
                </div>
              </div>
              <div class="col-xs-4" style="text-align: right;line-height: 1.26;">
                <div class="btn btn-blue-nb" style="margin-bottom: 5px;margin-top: 15px"
                     @click="print('is_paraclinic')">
                  Параклинические
                </div>
              </div>
              <div class="col-xs-4" style="text-align: right;line-height: 1.26;">
                <div class="btn btn-blue-nb" style="margin-bottom: 5px;margin-top: 15px"
                     @click="print('is_doc_refferal')">
                  Консультации
                </div>
              </div>

            </div>
          </div>
        </div>
      </div>
      <!--        <div class="col-xs-4">-->
      <!--        </div>-->
    </div>

  </div>
</template>

<script>
  import * as action_types from "../store/action-types";
  import directions_point from '../api/directions-point'
  import departments from "../store/modules/departments";

  export default {
    name: "results-department",
    data() {
      return {
        date: '',
      }
    },
    methods: {
      async print(type) {
        await this.$store.dispatch(action_types.INC_LOADING)
        const data = directions_point.getDirectionsTypeDate({'type': type, 'date': this.date})
        await this.$store.dispatch(action_types.DEC_LOADING)
      }
    }
  }

</script>

