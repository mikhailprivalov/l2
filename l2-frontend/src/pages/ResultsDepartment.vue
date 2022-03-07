<template>
  <div>
    <div
      class="row"
      style="margin-top: 60px"
    >
      <div class="col-xs-4" />
      <div class="col-xs-4">
        <div class="panel panel-default panel-flt">
          <div class="panel-heading">
            <h3 class="panel-title">
              Быстрая печать результатов по отделению или врачу
            </h3>
          </div>
          <div class="panel-body">
            <div class="row">
              <div
                class="col-xs-6"
                style="text-align: right;line-height: 1.26;"
              >
                <label>
                  Дата результатов:
                </label>
              </div>
              <div class="col-xs-6">
                <input
                  v-model="date"
                  type="date"
                  style="display: inline-block"
                >
              </div>
            </div>
            <div
              class="row"
              style="margin-bottom: 5px; margin-top: 15px"
            >
              <div
                class="col-xs-4"
                style="text-align: right;line-height: 1.26;"
              >
                <div class="checkbox">
                  <label>
                    <input
                      v-model="is_lab"
                      type="checkbox"
                    > Лабораторные
                  </label>
                </div>
              </div>
              <div
                class="col-xs-4"
                style="text-align: right;line-height: 1.26;"
              >
                <div class="checkbox">
                  <label>
                    <input
                      v-model="is_paraclinic"
                      type="checkbox"
                    > Параклинические
                  </label>
                </div>
              </div>
              <div
                class="col-xs-4"
                style="text-align: right;line-height: 1.26;"
              >
                <div class="checkbox">
                  <label>
                    <input
                      v-model="is_doc_refferal"
                      type="checkbox"
                    > Консультации
                  </label>
                </div>
              </div>
            </div>
            <div class="row">
              <div class="col-xs-5" />
              <div class="col-xs-7">
                <div
                  class="btn btn-blue-nb"
                  style="margin-bottom: 5px;margin-top: 15px;"
                  @click="print(false)"
                >
                  По отделению
                </div>
                <div
                  class="btn btn-blue-nb"
                  style="margin-bottom: 5px;margin-top: 15px; margin-left: 20px;"
                  @click="print(true)"
                >
                  По врачу
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import moment from 'moment';
import * as actions from '../store/action-types';
import directionsPoint from '../api/directions-point';

@Component({
  data() {
    return {
      date: moment().format('YYYY-MM-DD'),
      is_lab: true,
      is_paraclinic: true,
      is_doc_refferal: false,
      by_doc: false,
    };
  },
})
export default class ResultsDepartment extends Vue {
  date: string;

  is_lab: boolean;

  is_paraclinic: boolean;

  is_doc_refferal: boolean;

  by_doc: boolean;

  async print(by_doc) {
    await this.$store.dispatch(actions.INC_LOADING);
    const { results } = await directionsPoint.getDirectionsTypeDate(
      this, ['is_lab', 'is_paraclinic', 'is_doc_refferal', 'date'], { by_doc },
    );
    if (!results || results.length === 0) {
      this.$root.$emit('msg', 'error', 'Результатов не найдено');
    }
    this.$root.$emit('print:results', results);
    await this.$store.dispatch(actions.DEC_LOADING);
  }
}
</script>
