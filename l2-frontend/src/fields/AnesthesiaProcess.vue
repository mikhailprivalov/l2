<template>
  <div>
    <div class="sidebar-anesthesia"
         :class="[{show_anesthesia: this.$store.state.showMenuAnesthesiaStatus}, {hide_anesthesia: !this.$store.state.showMenuAnesthesiaStatus}]">
      <div class="title-anesthesia">
        <div class="col-xs-10">Течение анестезии</div>
        <div class="col-xs-2">
          <button class="btn btn-blue-nb sidebar-btn" style="font-size: 12px" @click="show_anesthesia_sidebar">
            <i class="glyphicon glyphicon-remove" v-tippy="{ placement : 'bottom'}" title="Закрыть"></i>
          </button>
        </div>
      </div>
      <div class="time-control">
        <vue-timepicker style="margin-left: 3px" v-model="timeValue" format="H:mm" input-width="127px"
                        input-class="timepicker_attr"
                        hide-clear-button close-on-complete></vue-timepicker>
        <button class="btn btn-blue-nb" @click="">
          Очистить
        </button>
      </div>
      <input type="text" class="no-outline" placeholder="SpO2"/>
      <input type="text" class="no-outline" placeholder="CO2"/>
      <input type="text" class="no-outline" placeholder="Систолическое давление"/>
      <input type="text" class="no-outline" placeholder="Диастолическое давление"/>
      <div class="number">
        <button class="btn btn-blue-nb sidebar-btn sidebar-btn" @mousedown="minus_temperature_start"
                @mouseleave="temperature_stop" @mouseup="temperature_stop">
          <i class="fa fa-minus"/>
        </button>
        <input type="text" v-model.number="temperature" class="no-outline" style="width: 190px" value="36.6"
               placeholder="Температура"/>
        <button class="btn btn-blue-nb sidebar-btn" style="" @mousedown="plus_temperature_start"
                @mouseleave="temperature_stop" @mouseup="temperature_stop">
          <i class="fa fa-plus"/>
        </button>
      </div>

      <div class="col-xs-10 title-anesthesia">Сильнодействующие</div>
      <div>
        <table class="table table-bordered tb-background">
          <tr v-for="(v, k) in potent_drugs_used">
<!--          <input type="text" class="no-outline" :value="v" @input="update(potent_drugs_used, k, $event)" v-for="(v, k) in potent_drugs_used" :key="k" :placeholder="`${k}`"/>-->
          <td class="cl-td first-column">{{k}}</td>
          <td class="cl-td second-column"><input style="width: 100%" class="no-outline" type="text" :value="v" @input="update(potent_drugs_used, k, $event)"  :key="k" :placeholder="'количество'"/></td>
          </tr>
        </table>
      </div>


      <div class="col-xs-10 title-anesthesia">Наркотические</div>
      <input type="text" class="no-outline" :value="v" @input="update(narcotic_drugs_used, k, $event)" v-for="(v, k) in narcotic_drugs_used" :key="k" :placeholder="`${k}`"/>
      <div class="control-row side-bottom">
        <button class="btn btn-blue-nb" @click="">
          Добавить
        </button>
      </div>
    </div>
    <button
      style=" border-radius: 3px; padding: 4px; width: 10%; align-content: center; height: 30px; margin-bottom: 5px;"
      class="btn btn-blue-nb" title="Добавить значения в наркозную карту" v-tippy @click="show_anesthesia_sidebar">
      <i class="fa fa-heartbeat fa-lg" aria-hidden="true"></i>
      Добавить
    </button>
    <table width="100%" cellspacing="0" border="1">
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
        interval: false,
        potent_drugs_other: {},
        potent_drugs_used: {},
        potent_data: {},
        narcotic_drugs_other: {},
        narcotic_drugs_used: {},
        narcotic_data: {},

      }
    },
    mounted() {
      for (let f of this.fields) {
        if (f.type === 'Сильнодействующие' && f.default=== true) {
          this.potent_drugs_used[f.title] = ''
        }
        else if (f.type === 'Наркотические' && f.default=== true) {
          this.narcotic_drugs_used[f.title] = ''
        }
      }
      console.log(this.narcotic_drugs_all, this.narcotic_drugs_used, this.potent_drugs_all, this.potent_drugs_used)
      console.log(this.iss, this.field_pk)
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
    	  console.log(obj)
    	  console.log(this.potent_drugs_used)
    	  console.log(this.narcotic_drugs_used)
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
        this.interval = false
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
        console.log('test')
      },
      show_anesthesia_sidebar() {
        this.$store.dispatch(action_types.CHANGE_STATUS_MENU_ANESTHESIA);
        this.getCurrentTime();
      }
    }
  }
</script>

<style scoped lang="scss">
  .tb-background{
    background-color: #eee;
  }
  .first-column{
    width: 160px;
  }
  .second-column{
    width: 100px;
  }

  .show_anesthesia {
    width: 260px;
  }

  .hide_anesthesia {
    width: 0;
  }

  .sidebar-anesthesia {
    display: flex;
    align-items: stretch;
    flex-direction: column;
    align-content: stretch;
    height: 85%;
    position: fixed; /* Stay in place */
    z-index: 1;
    top: 100px;
    left: 0;
    background-color: #eee;
    overflow-x: hidden;
    transition: 0.6s;
    border-right: 1px solid #56616c;
    border-bottom: 1px solid #56616c;

    .side-bottom {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      border-radius: 0;
      display: flex;
      flex-direction: row;
      height: 30px;

      .btn {
        border-radius: 0;
        padding: 5px 4px;
        width: 100%;
      }
    }

    .title-anesthesia {
      height: 30px;
      width: 260px;
      background-color: #56616c;
      display: flex;
      flex-direction: row;
      color: whitesmoke;
      padding-top: 5px;

      .sidebar-btn {
        border-bottom: none !important;
      }
    }

    .number {
      display: flex;
      flex-direction: row;

      .sidebar-btn {
        margin-top: 0px;
        height: 31px;
        width: 35px;
      }

      input {
        margin-left: 0px;
        margin-right: 0px;
        text-align: center;
      }

      .minus, .plus {
        width: 20px;
        height: 20px;
        background: #7f8c9a;
        border-radius: 4px;
        padding: 8px 5px 8px 5px;
        border: 1px solid #ddd;
        display: inline-block;
        vertical-align: middle;
        text-align: center;
      }
    }

    input {
      border-top-style: hidden;
      border-right-style: hidden;
      border-left-style: hidden;
      border-bottom-style: hidden;
      background-color: #eee;
      width: 100%;
      padding: 5px 1px;
    }

    input:focus,
    input:active {
      /*background-color: #aab2bd;*/
      /*background-color: #ec7063;*/
      background-color: #dc322f;
      /*color: white;*/
    }

    .no-outline:focus {
      outline: none;
    }
  }

  .time-control {
    display: flex;
    flex-direction: row;

    .btn {
      border-radius: 0;
      padding: 5px 4px;
      width: 50%;
      height: 31px;
    }
  }

  .sidebar-btn {
    border-radius: 0;

    &:not(.text-center) {
      text-align: left;
    }

    border-top: none !important;
    border-right: none !important;
    border-left: none !important;
    padding: 0 12px;
    height: 24px;

    &:not(:hover), &.active-btn:hover {
      cursor: default;
      background-color: rgba(#000, .02) !important;
      color: #000;
      border-bottom: 1px solid #b1b1b1 !important;
    }
  }

  table {
    border-collapse: collapse;
  }

  th {
    background: #ccc;
    text-align: left;
  }

  td, th {
    border: 1px solid #0f0f0f;
    padding: 4px;
  }

</style>
