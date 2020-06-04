<template>
  <div>
    <div class="sidebar-anesthesia-overlay" :class="{showOverlay: this.$store.state.showMenuAnesthesiaStatus}"/>
    <div class="sidebar-anesthesia" :class="{show: this.$store.state.showMenuAnesthesiaStatus}">
      <div class="sidebar-anesthesia-inner">
        <div class="scroll-wrapper">
          <div class="title-anesthesia">
            <div>Течение анестезии</div>
            <button class="btn btn-blue-nb sidebar-btn close-btn"
                    @click="show_anesthesia_sidebar">
              <i class="glyphicon glyphicon-remove" v-tippy="{ placement : 'bottom'}" title="Закрыть"></i>
            </button>
          </div>
          <div class="time-control">
            <input type="datetime-local" class="form-control nbr" v-model="timeValue" :max="maxTimeValue"/>
            <button class="btn btn-blue-nb nbr" @click="setCurrentTime" title="Текущие дата и время" v-tippy>
              <i class="fa fa-circle"/>
            </button>
          </div>

          <div class="time-control">
            <input type="datetime-local" class="form-control nbr" v-model="timeValue" :max="maxTimeValue"/>
            <button class="btn btn-blue-nb nbr" @click="setCurrentTime" title="Текущие дата и время" v-tippy>
              <i class="fa fa-circle"/>
            </button>
          </div>

          <div class="sidebar-content">
            <div class="title-anesthesia">Показатели человека</div>
            <table class="table table-condensed tb-background">
              <colgroup>
                <col/>
                <col width='80'/>
              </colgroup>
              <tr v-for="(v, k) in patient_params_used" v-if="k !== 'temperature'">
                <td class="cl-td">{{k}}</td>
                <td class="cl-td"><input style="width: 100%" class="no-outline" type="text" :value="v"
                                         @input="update(patient_params_used, k, $event)" :key="k"
                                         :placeholder="'значение'"/></td>
              </tr>
            </table>
            <div class="number">
              <button class="btn btn-blue-nb sidebar-btn" @click="minus_temperature_once">
                -1
              </button>
              <button class="btn btn-blue-nb sidebar-btn" @mousedown="minus_temperature_start"
                      @mouseleave="temperature_stop" @mouseup="temperature_stop">
                -0.1
              </button>
              <input type="text" v-model.number="temperature"
                     placeholder="Температура"/>
              <button class="btn btn-blue-nb sidebar-btn" @mousedown="plus_temperature_start"
                      @mouseleave="temperature_stop" @mouseup="temperature_stop">
                +0.1
              </button>
              <button class="btn btn-blue-nb sidebar-btn"  @click="plus_temperature_once">
                +1
              </button>
            </div>
            <div class="title-anesthesia">Сильнодействующие</div>
            <table class="table table-condensed tb-background">
              <colgroup>
                <col/>
                <col width='80'/>
              </colgroup>
              <tr v-for="(v, k) in potent_drugs_used">
                <td class="cl-td">{{k}}</td>
                <td class="cl-td"><input style="width: 100%" class="no-outline" type="text" :value="v"
                                         @input="update(potent_drugs_used, k, $event)" :key="k"
                                         :placeholder="'значение'"/></td>
              </tr>
            </table>
            <div class="title-anesthesia">Наркотические</div>
            <table class="table table-condensed tb-background col-xs-12">
              <colgroup>
                <col/>
                <col width='80'/>
              </colgroup>
              <tr v-for="(v, k) in narcotic_drugs_used">
                <td class="cl-td ">{{k}}</td>
                <td class="cl-td "><input style="width: 100%" class="no-outline" type="text" :value="v"
                                          @input="update(narcotic_drugs_used, k, $event)" :key="k"
                                          :placeholder="'значение'"/></td>
              </tr>
            </table>
          </div>
        </div>

        <div class="side-bottom">
          <button class="btn btn-blue-nb nbr" @click="save_data">
            Добавить
          </button>
          <button class="btn btn-blue-nb nbr" @click="load_data">
            Обновить
          </button>
        </div>
      </div>
    </div>
    <button
      style=" border-radius: 3px; padding: 4px; width: 10%; height: 30px; margin-bottom: 5px;"
      class="btn btn-blue-nb" title="Добавить значения в наркозную карту" v-tippy @click="show_anesthesia_sidebar">
      <i class="fa fa-heartbeat fa-lg"></i>
      Добавить
    </button>
    <table class="table table-bordered">
      <colgroup>
            <col width='190'/>
            <col width='70'/>
      </colgroup>
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
  import moment from 'moment'
  import * as action_types from '../store/action-types'
  import directions_point from "../api/directions-point";

  export default {
    name: "AnesthesiaProcess",
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
        timeValue: moment().format('YYYY-MM-DDTHH:mm'),
        maxTimeValue: moment().add(1, 'days').format('YYYY-MM-DDTHH:mm'),
        temperature: 36.6,
        interval: null,
        intervalTime: null,
        potent_drugs_other: {},
        potent_drugs_used: {},
        potent_data: {},
        narcotic_drugs_other: {},
        narcotic_drugs_used: {},
        narcotic_data: {},
        patient_params_used: {},
        patient_params_other: {},
        tb_data: [],
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
      this.intervalTime = setInterval(() => {
        this.setMaxTime()
      }, 1000);
      this.setCurrentTime();
      this.setMaxTime();
      this.load_data();
    },
    destroyed() {
      clearInterval(this.interval);
      clearInterval(this.intervalTime);
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
        this.patient_params_used['temperature'] = this.temperature
        let temp_result = {
          'time': this.timeValue.H + this.timeValue.mm,
          'potent_drugs': this.potent_drugs_used,
          'narcotic_drugs': this.narcotic_drugs_used,
          'patient_params': this.patient_params_used
        }
        let research_data = {'iss_pk': this.iss, 'field_pk': this.field_pk}
        this.tb_data.push(temp_result)
        await directions_point.anesthesiaResultSave({
          'temp_result': this.tb_data,
          'research_data': research_data
        });
        await this.$store.dispatch(action_types.DEC_LOADING)
      },
      async load_data() {
        await this.$store.dispatch(action_types.INC_LOADING);
        let research_data = {'iss_pk': this.iss, 'field_pk': this.field_pk};
        const data = await directions_point.anesthesiaLoadData({
          'research_data': research_data
        });
        this.tb_data = [...data.data];

        await this.$store.dispatch(action_types.DEC_LOADING)
      },
      plus_temperature_start() {
        if (typeof this.temperature !== 'number') {
          this.temperature = 36.6
        } else {
          this.temperature += 0.1
        }

        clearInterval(this.interval);

        this.interval = setTimeout(() => {
          clearInterval(this.interval);
          this.interval = setInterval(() => {
            this.temperature += 0.1
          }, 200)
        }, 400)
      },
      temperature_stop() {
        clearInterval(this.interval);
        this.interval = null
      },
      minus_temperature_start() {
        if (typeof this.temperature !== 'number') {
          this.temperature = 36.6
        } else {
          this.temperature -= 0.1
        }

        clearInterval(this.interval);

        this.interval = setTimeout(() => {
          clearInterval(this.interval);
          this.interval = setInterval(() => {
            this.temperature -= 0.1
          }, 200)
        }, 400)
      },
      minus_temperature_once() {
        this.temperature -= 1;
      },
      plus_temperature_once() {
        this.temperature += 1;
      },
      setCurrentTime() {
        this.timeValue = moment().format('YYYY-MM-DDTHH:mm');
      },
      setMaxTime() {
        this.maxTimeValue = moment().add(2, 'days').format('YYYY-MM-DDTHH:mm');
      },
      clear_data(obj) {
        Object.entries(obj).forEach(([key]) => obj[key] = '');
      },
      show_anesthesia_sidebar() {
        this.$store.dispatch(action_types.CHANGE_STATUS_MENU_ANESTHESIA);
        this.clear_data(this.potent_drugs_used)
        this.clear_data(this.narcotic_drugs_used)
        this.clear_data(this.patient_params_used)
        this.setCurrentTime();
      }
    }
  }
</script>

<style scoped lang="scss">
  $sidebar-anesthesia-width: 300px;

  .sidebar-anesthesia {
    border-top-right-radius: 5px;
    position: fixed;
    top: 105px;
    z-index: 1000;
    bottom: 0;
    left: 0;
    width: 0;
    overflow-x: hidden;
    overflow-y: hidden;
    transition: 0.4s width ease-in-out, 0.4s box-shadow ease-in-out;
    background-color: #fff;
    border-right: 1px solid #56616c;

    &.show {
      width: $sidebar-anesthesia-width;
      box-shadow: 1px 0 8px 2px rgba(0, 0, 0, .3);
    }
  }

  .sidebar-anesthesia-overlay {
    z-index: 998;
    position: fixed;
    top: -999px;
    left: -999px;
    opacity: 0;
    background: rgba(#000, .3);
    transition: 0.4s opacity ease-in-out;

    &.showOverlay {
      top: 0;
      right: 0;
      bottom: 0;
      left: 0;
      opacity: 1;
    }
  }

  .zIndex999 {
    z-index: 998;
    position: relative;
  }

  .sidebar-anesthesia-inner {
    position: relative;
    height: 100%;
    width: $sidebar-anesthesia-width;
    overflow-x: hidden;

    .scroll-wrapper {
      overflow-x: hidden;
      overflow-y: auto;
      position: absolute;
      top: 0;
      right: 0;
      left: 0;
      bottom: 34px;
    }

    .title-anesthesia {
      position: relative;
      height: 30px;
      background-color: #56616c;
      display: flex;
      flex-direction: row;
      color: #f5f5f5;
      padding-top: 5px;
      padding-left: 5px;
      padding-right: 30px;

      .sidebar-btn {
        color: #fff;
        position: absolute;
        right: 0;
        top: 0;
        height: 30px;
        width: 30px;
        padding: 0;
      }
    }

    .number {
      display: flex;
      flex-direction: row;

      .sidebar-btn {
        margin-top: 0;
        height: 31px;
        width: 40px;
        font-weight: bold;
        padding: 0;

        &:nth-of-type(1), &:nth-of-type(2) {
          border-right: 1px solid #000 !important;
        }
        &:nth-of-type(3), &:nth-of-type(4) {
          border-left: 1px solid #000 !important;
        }
      }

      input {
        margin-left: 0;
        margin-right: 0;
        text-align: center;
        width: calc(100% - 160px);
      }
    }

    .sidebar-content {
      th {
        padding-left: 5px;
      }

      td {
        padding-left: 3px !important;
        border-left: 1px solid #000;
      }

      tr:hover {
        &, & input {
          background-color: #55566b;
          color: #f5f5f5;
        }
      }
    }

    .side-bottom {
      display: flex;
      flex-direction: row;
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      height: 34px;

      .btn {
        display: inline-block;
        width: 50%;
        height: 34px;
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

    input {
      text-align: center;
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
