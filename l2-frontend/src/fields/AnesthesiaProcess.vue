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
      <div class="number">
        <button class="btn btn-blue-nb sidebar-btn sidebar-btn" @mousedown="minus_temperature_start"
                @mouseleave="temperature_stop" @mouseup="temperature_stop">
          <i class="fa fa-minus"/>
        </button>
        <input type="text" v-model="temerature_current" class="no-outline" style="width: 190px" value="36.6"
               placeholder="Температура"/>
        <button class="btn btn-blue-nb sidebar-btn" style="" @mousedown="plus_temperature_start"
                @mouseleave="temperature_stop" @mouseup="temperature_stop">
          <i class="fa fa-plus"/>
        </button>
      </div>

      <input type="text" class="no-outline" placeholder="Систолическое давление"/>
      <input type="text" class="no-outline" placeholder="Диастолическое давление"/>
      <br/>
      <br/>
      <div class="control-row side-bottom">
        <button class="btn btn-blue-nb" @click="show_anesthesia_sidebar">
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
    data() {
      return {
        show_anesthesia_menu: false,
        timeValue: {
          H: '',
          mm: '',
        },
        temerature: 'Температура',
        interval: false,
      }
    },
    computed: {
      temerature_current() {
        if (this.temerature < 34) {
          return this.temerature = 34
        } else if (this.temerature > 41) {
          return this.temerature = 41
        } else if ((this.temerature > 34) && (this.temerature < 42)) {
          return this.temerature.toFixed(1)
        }
      }
    },
    methods: {
      plus_temperature_start() {
        if (typeof this.temerature !== 'number') {
          this.temerature = 36.6
        }
        if (!this.interval) {
          this.interval = setInterval(() => ((this.temerature += 0.1).toFixed(1)), 100)
        }
      },
      temperature_stop() {
        clearInterval(this.interval);
        this.interval = false
      },
      minus_temperature_start() {
        if (typeof this.temerature !== 'number') {
          this.temerature = 36.6
        }
        if (!this.interval) {
          this.interval = setInterval(() => (
            (this.temerature -= 0.1).toFixed(1)), 100)
        }
      },
      getCurrentTime() {
        this.timeValue.mm = moment().format('mm');
        this.timeValue.H = moment().format('H');
      },
      show_anesthesia_sidebar() {
        this.$store.dispatch(action_types.CHANGE_STATUS_MENU_ANESTHESIA);
        this.getCurrentTime();
        if (this.$store.state.showMenuAnesthesiaStatus === true) {
          var renewTime = setInterval(this.getCurrentTime, 1000 * 10);
        }
        if (this.$store.state.showMenuAnesthesiaStatus === false) {
          clearInterval(renewTime);
        }
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

      .btn {
        border-radius: 0;
        padding: 5px 4px;
        width: 100%;
      }
    }

    .title-anesthesia {
      height: 5%;
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
      border-bottom-style: groove;
      background-color: #eee;
      margin-left: 3px;
      margin-right: 3px;
      margin-top: 8px;
    }

    input:focus,
    input:active {
      border-bottom: 2px solid #56616c;
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
