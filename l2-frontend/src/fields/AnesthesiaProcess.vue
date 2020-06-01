<template>
  <div>
    <div class="sidebar-anesthesia"
         :class="[{show_anesthesia: this.$store.state.showMenuAnesthesiaStatus}, {hide_anesthesia: !this.$store.state.showMenuAnesthesiaStatus}]">
      <div class="title-anesthesia">
        <div class="col-xs-10">Течение анестезии</div>
        <div class="col-xs-2">
          <button class="btn btn-blue-nb sidebar-btn close-btn" style="font-size: 14px" @click="show_anesthesia_sidebar">
            <i class="glyphicon glyphicon-remove" v-tippy="{ placement : 'bottom'}" title="Закрыть"></i>
          </button>
        </div>
      </div>
      <div class="time-control row">
        <vue-timepicker class="col-xs-6" v-model="timeValue" format="H:mm" hide-clear-button close-on-complete/>
        <button class="btn btn-blue-nb col-xs-6" @click="getCurrentTime">
          <i class="fa fa-clock-o"/> Текущее время
        </button>
      </div>
      <div class="content">
        <div class="col-xs-12 title-anesthesia">Показатели человека</div>
        <table class="table table-condensed tb-background">
          <colgroup>
            <col width='190'/>
            <col width='70'/>
          </colgroup>
          <tr v-for="(v, k) in patient_params_used">
            <td class="cl-td">{{k}}</td>
            <td class="cl-td"><input style="width: 100%" class="no-outline" type="text" :value="v"
                                                   @input="update(patient_params_used, k, $event)" :key="k"
                                                   :placeholder="'значение'"/></td>
          </tr>
        </table>
        <div class="number">
          <button class="btn btn-blue-nb sidebar-btn" @mousedown="minus_temperature_start"
                  @mouseleave="temperature_stop" @mouseup="temperature_stop">
            <i class="fa fa-minus"/>
          </button>
          <input type="text" v-model.number="temperature"
                 placeholder="Температура"/>
          <button class="btn btn-blue-nb sidebar-btn" style="" @mousedown="plus_temperature_start"
                  @mouseleave="temperature_stop" @mouseup="temperature_stop">
            <i class="fa fa-plus"/>
          </button>
        </div>
        <div class="col-xs-12 title-anesthesia">Сильнодействующие</div>
        <table class="table table-condensed tb-background">
          <colgroup>
            <col width='190'/>
            <col width='70'/>
          </colgroup>
          <tr v-for="(v, k) in potent_drugs_used">
            <td class="cl-td">{{k}}</td>
            <td class="cl-td"><input style="width: 100%" class="no-outline" type="text" :value="v"
                                                   @input="update(potent_drugs_used, k, $event)" :key="k"
                                                   :placeholder="'значение'"/></td>
          </tr>
        </table>
        <div class="col-xs-12 title-anesthesia">Наркотические</div>
        <table class="table table-condensed tb-background col-xs-12">
          <colgroup>
            <col width='190'/>
            <col width='70'/>
          </colgroup>
          <tr v-for="(v, k) in narcotic_drugs_used">
            <td class="cl-td ">{{k}}</td>
            <td class="cl-td "><input style="width: 100%" class="no-outline" type="text" :value="v"
                                                   @input="update(narcotic_drugs_used, k, $event)" :key="k"
                                                   :placeholder="'значение'"/></td>
          </tr>
        </table>
      </div>
      <div class="side-bottom row">
        <button class="btn btn-blue-nb col-xs-6" @click="save_data">
          Добавить
        </button>
        <button class="btn btn-blue-nb col-xs-6" @click="save_data">
          Обновить
        </button>
      </div>
    </div>
    <button
      style=" border-radius: 3px; padding: 4px; width: 10%; height: 30px; margin-bottom: 5px;"
      class="btn btn-blue-nb" title="Добавить значения в наркозную карту" v-tippy @click="show_anesthesia_sidebar">
      <i class="fa fa-heartbeat fa-lg"></i>
      Добавить
    </button>
    <table class="table table-bordered">
      <tr>
        <th>SpO2</th>
        <th>10:05</th>
        <th>10:15</th>
        <th>10:25</th>
        <th>10:35</th>
        <th>10:45</th>
        <th>10:55</th>
        <th>11:05</th>
        <th>11:15</th>
        <th>11:25</th>
        <th>11:35</th>
        <th>11:45</th>
        <th>11:55</th>
        <th>12:05</th>
        <th>12:15</th>
        <th>12:25</th>
        <th>12:35</th>
        <th>12:45</th>
        <th>12:55</th>
        <th>13:05</th>
        <th>13:15</th>
      </tr>
      <tr>
        <th>CО2</th>
        <td>5.5</td>
        <td>6.0</td>
        <td>7.0</td>
        <td>7.0</td>
        <td>8.0</td>
        <td>9.0</td>
        <td>1.0</td>
        <td>2.0</td>
      </tr>
      <tr>
        <th>Температура</th>
        <td>Да</td>
        <td>Да</td>
        <td>Да</td>
        <td>Да</td>
        <td>Да</td>
        <td>Да</td>
        <td>Да</td>
        <td>Да</td>
      </tr>
      <tr>
        <th>САД</th>
        <td>Да</td>
        <td>Да</td>
        <td>Да</td>
        <td>Да</td>
        <td>Да</td>
        <td>Да</td>
        <td>Да</td>
        <td>Да</td>
      </tr>
      <tr>
        <th>ДАД</th>
        <td>Да</td>
        <td>Да</td>
        <td>Да</td>
        <td>Да</td>
        <td>Да</td>
        <td>Да</td>
        <td>Да</td>
        <td>Да</td>
      </tr>
    </table>
  </div>

</template>

<script>
  import VueTimepicker from 'vue2-timepicker/src/vue-timepicker.vue'
  import moment from 'moment'
  import * as action_types from '../store/action-types'
  import directions_point from "../api/directions-point";

  export default {
    name: "AnesthesiaProcess",
    components: {
      VueTimepicker
    },
    props: {
      fields: {
        type: Array,
        required: true
      },
      iss: {
        type: Number,
        required: false,
      },
      field_pk: {
        type: Number,
        required: true,
      }
    },
    data() {
      return {
        show_anesthesia_menu: false,
        timeValue: {
          H: '',
          mm: '',
        },
        temperature: 36.6,
        interval: null,
        potent_drugs_other: {},
        potent_drugs_used: {},
        potent_data: {},
        narcotic_drugs_other: {},
        narcotic_drugs_used: {},
        narcotic_data: {},
        patient_params_used: {},
        patient_params_other: {}

      }
    },
    mounted() {
      for (let f of this.fields) {
        if (f.type === 'Сильнодействующие' && f.default === true) {
          this.potent_drugs_used[f.title] = ''
        } else if (f.type === 'Наркотические' && f.default === true) {
          this.narcotic_drugs_used[f.title] = ''
        } else if (f.type === 'Показатели человека' && f.default === true) {
          this.patient_params_used[f.title] = ''
        }
      }
      this.getCurrentTime();
    },
    watch: {
      temperature() {
        this.temperature = Number(this.temperature) || 36.6
        if (this.temperature < 34) {
          this.temperature = 34
        } else if (this.temperature > 41) {
          this.temperature = 41
        }
        this.temperature = Number(this.temperature.toFixed(1))
      }
    },
    methods: {
      update(obj, prop, event) {
        this.$set(obj, prop, event.target.value);
      },
      async save_data() {
        await this.$store.dispatch(action_types.INC_LOADING);
        let temp_result = {
          'time': '10-00',
          'potent_drugs': this.potent_drugs_used,
          'narcotic_drugs': this.narcotic_drugs_used
        }
        let research_data = {'iss': this.iss, 'field_pk': this.field_pk}
        await directions_point.anesthesiaResultSave({
          'temp_result': temp_result,
          'research_data': research_data
        });
        await this.$store.dispatch(action_types.DEC_LOADING)
      },
      plus_temperature_start() {
        if (typeof this.temperature !== 'number') {
          this.temperature = 36.6
        }
        if (!this.interval) {
          this.interval = setInterval(() => ((this.temperature += 0.1).toFixed(1)), 100)
        }
      },
      temperature_stop() {
        clearInterval(this.interval);
        this.interval = null
      },
      minus_temperature_start() {
        if (typeof this.temperature !== 'number') {
          this.temperature = 36.6
        }
        if (!this.interval) {
          this.interval = setInterval(() => (
            (this.temperature -= 0.1).toFixed(1)), 100)
        }
      },
      getCurrentTime() {
        this.timeValue.mm = moment().format('mm');
        this.timeValue.H = moment().format('H');
      },
      clear_data(obj) {
        Object.entries(obj).forEach(([key, value]) => obj[key] = '');
      },
      show_anesthesia_sidebar() {
        this.$store.dispatch(action_types.CHANGE_STATUS_MENU_ANESTHESIA);
        this.clear_data(this.potent_drugs_used)
        this.clear_data(this.narcotic_drugs_used)
        this.clear_data(this.patient_params_used)
        this.getCurrentTime();
      }
    }
  }
</script>

<style scoped lang="scss">
  .show_anesthesia {
    width: 260px;
  }

  .hide_anesthesia {
    width: 0;
  }

  .sidebar-anesthesia {
    height: 600px;
    position: fixed;
    top: 100px;
    left: 0;
    background-color: #eee;
    overflow-x: hidden;
    overflow-y: hidden;
    transition: 0.6s;
    border-right: 1px solid #56616c;
    border-bottom: 1px solid #56616c;

    .side-bottom {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      border-radius: 0;
      height: 30px;
      .btn {
        border-radius: 0;
      }
    }

    .title-anesthesia {
      height: 30px;
      background-color: #56616c;
      display: flex;
      flex-direction: row;
      color: #f5f5f5;
      padding-top: 5px;
      .sidebar-btn {
        height: 27px;
        width: 27px;
        padding: 0 8px;

      }
    }

    .number {
      display: flex;
      flex-direction: row;
      width: 259px;

      .sidebar-btn {
        margin-top: 0;
        height: 31px;
        width: 40px;
      }

      input {
        margin-left: 0;
        margin-right: 0;
        text-align: center;
      }
    }

    .content {
      overflow-y: auto;
      overflow-x: hidden;
      height: 510px;

      tr:hover {
        &, & input {
          background-color: #55566b;
          color: #f5f5f5;
        }
      }
    }
  }

  input {
    border: none;
    background-color: #eee;
    width: 100%;
    padding: 5px 1px;
  }

  ::placeholder {
    color: #89909b;
  }

  :focus {
    outline: none;
  }

  .time-control {
    display: flex;
    flex-direction: row;
    .btn {
      border-radius: 0;
      padding: 5px 4px;
      width: 50%;
      height: 31px;
      border: none !important;
    }
  }

  .sidebar-btn {
    border-radius: 0;
    border: none !important;
    padding: 0 12px;
    height: 26px;

    &:not(:hover) {
      background-color: rgba(#000, .02) !important;
      color: #000;
    }
  }

  th {
    background: #ccc;
    text-align: left;
  }

  td, th {
    border-bottom: 1px solid #0f0f0f;
    padding: 4px;
  }


  .tb-background {
    background-color: #eee;
    margin-bottom: 0;
  }

</style>
