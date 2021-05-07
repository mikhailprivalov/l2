<template>
  <div>
    <div class="sidebar-anesthesia-overlay" :class="{showOverlay: this.$store.state.showMenuAnesthesiaStatus}"
         @click="show_anesthesia_sidebar"/>
    <div class="sidebar-anesthesia" :class="{show: this.$store.state.showMenuAnesthesiaStatus}">
      <div class="sidebar-anesthesia-inner">
        <div class="title-anesthesia">
          <div>Течение анестезии<template v-if="isEdit"> (редактирование)</template></div>
          <button class="btn btn-blue-nb sidebar-btn close-btn"
                  @click="show_anesthesia_sidebar">
            <i class="glyphicon glyphicon-remove" v-tippy="{ placement : 'bottom'}" title="Закрыть"></i>
          </button>
        </div>
        <div class="time-control">
          <input type="datetime-local" class="form-control nbr" v-model="timeValue" :max="maxTimeValue"
                  :readonly="isEdit" />
          <button class="btn btn-blue-nb nbr"
                  :disabled="isEdit"
                  @click="setCurrentTime" title="Текущие дата и время" v-tippy>
            <i class="fa fa-clock-o"/>
          </button>
        </div>

        <div class="scroll-wrapper">
          <div class="title-anesthesia">Показатели человека</div>
          <table class="table table-condensed tb-background">
            <colgroup>
              <col/>
              <col width='80'/>
            </colgroup>
            <!-- eslint-disable-next-line vue/no-use-v-if-with-v-for -->
            <tr v-for="(v, k) in patient_params_used" :key="k" v-if="k !== 'temperature'">
              <td class="cl-td" @click="focus_next">{{k}}</td>
              <td class="cl-td">
                <input class="no-outline anastesia" type="text" v-model="patient_params_used[k]" :key="k"
                       :readonly="actionDelete"
                       @focus="focus_input"
                       @blur="blur_input"
                       @keyup.enter.exact="move_focus_next"
                       @keyup.enter.shift="move_focus_prev"
                       placeholder="значение"/>
              </td>
            </tr>
          </table>
          <div class="number">
            <button class="btn btn-blue-nb nbr" @click="minus_temperature_once" :disabled="actionDelete" tabindex="-1">
              -1
            </button>
            <button class="btn btn-blue-nb nbr" @mousedown="minus_temperature_start"
                    @mouseleave="temperature_stop" @mouseup="temperature_stop" :disabled="actionDelete" tabindex="-1">
              -0.1
            </button>
            <input type="text" v-model.number="temperature" class="anastesia"
                   @keyup.enter.exact="move_focus_next"
                   @keyup.enter.shift="move_focus_prev"
                   :readonly="actionDelete"
                   placeholder="Температура"/>
            <button class="btn btn-blue-nb nbr" @mousedown="plus_temperature_start"
                    @mouseleave="temperature_stop" @mouseup="temperature_stop" :disabled="actionDelete" tabindex="-1">
              +0.1
            </button>
            <button class="btn btn-blue-nb nbr" @click="plus_temperature_once" :disabled="actionDelete" tabindex="-1">
              +1
            </button>
          </div>
          <div class="title-anesthesia">Сильнодействующие</div>
          <table class="table table-condensed tb-background">
            <colgroup>
              <col/>
              <col width='80'/>
            </colgroup>
            <tr v-for="(v, k) in potent_drugs_used" :key="k">
              <td class="cl-td" @click="focus_next">{{k}}</td>
              <td class="cl-td">
                <input class="no-outline anastesia" type="text" v-model="potent_drugs_used[k]"
                       :readonly="actionDelete"
                       @focus="focus_input"
                       @blur="blur_input"
                       @keyup.enter.exact="move_focus_next"
                       @keyup.enter.shift="move_focus_prev"
                       :key="k" placeholder="значение"/>
              </td>
            </tr>
          </table>
          <div class="title-anesthesia">Наркотические</div>
          <table class="table table-condensed tb-background col-xs-12">
            <colgroup>
              <col/>
              <col width='80'/>
            </colgroup>
            <tr v-for="(v, k) in narcotic_drugs_used" :key="k">
              <td class="cl-td" @click="focus_next">{{k}}</td>
              <td class="cl-td">
                <input class="no-outline anastesia" type="text" v-model="narcotic_drugs_used[k]" :key="k"
                       :readonly="actionDelete"
                       @focus="focus_input"
                       @blur="blur_input"
                       @keyup.enter.exact="move_focus_next"
                       @keyup.enter.shift="move_focus_prev"
                       placeholder="значение"/>
              </td>
            </tr>
          </table>

          <div v-if="isEdit">
            <label style="margin: 5px 5px 5px 10px;">
              <input type="checkbox" v-model="actionDelete" />
              удалить запись
            </label>
            <br/>
          </div>
        </div>

        <div class="side-bottom">
          <button class="btn btn-blue-nb nbr" @click="save_data" v-if="!isEdit">
            Добавить
          </button>
          <button class="btn btn-blue-nb nbr" @click="save_data" v-else-if="!actionDelete">
            Сохранить изменения
          </button>
          <button class="btn btn-blue-nb nbr" @click="delete_data" v-else>
            Удалить запись
          </button>
        </div>
      </div>
    </div>
    <button class="btn btn-blue-nb tb-add-btn" title="Добавить значения в наркозную карту" v-tippy
            v-if="!disabled"
            @click="show_anesthesia_sidebar">
      <i class="fa fa-heartbeat fa-lg"></i>
      Добавить
    </button>
    <div class="GRID-HACK table-root">
      <table v-if="tb_data.length > 0" ref="firstTable">
        <tr v-for="(row, i) in tb_data" :key="i" :class="`row-${row_category[i] || 'default'}`">
          <td>
            <div>
              {{row[0]}}
            </div>
          </td>
        </tr>
      </table>
      <div class="tb-data" ref="tbData">
        <table :class="!disabled && 'all-hover'">
          <colgroup v-for="(_, i) in tb_data[0] || []" :key="i" />
          <tbody>
            <tr v-for="(row, i) in tb_data" :key="i" :class="`row-${row_category[i] || 'default'}`">
              <!-- eslint-disable-next-line vue/no-use-v-if-with-v-for -->
              <td v-for="(item, j) in row" v-if="j > 0"
                  :key="j"
                  :class="j + 1 === row.length && 'no-hover'"
                  @click="editColumn(j)"
              >
                <div :style="{height: `${tb_heights[i]}px`}">
                  <template v-if="i === 0 && j > 0 && item !== 'Сумма'">
                    <DisplayDateTime :value="item"/><i class="display-only-hover fa fa-pencil"></i>
                  </template>
                  <template v-else>
                    {{ item }}
                  </template>
                </div>
              </td>
            </tr>
          </tbody>
          <tr v-if="tb_data.length === 0">
            <td>нет данных</td>
          </tr>
        </table>
      </div>
    </div>
  </div>

</template>

<script>
import moment from 'moment';
import * as actions from '../store/action-types';
import directionsPoint from '../api/directions-point';
import DisplayDateTime from '../ui-cards/DisplayDateTime.vue';

export default {
  name: 'AnesthesiaProcess',
  components: { DisplayDateTime },
  props: {
    fields: {
      type: Array,
      required: true,
    },
    iss: {
      type: Number,
      required: false,
    },
    field_pk: {
      type: Number,
      required: true,
    },
    disabled: {
      type: Boolean,
      required: false,
      default: false,
    },
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
      actionDelete: false,
      isEdit: false,
      tb_data: [],
      tb_heights: [],
      row_category: {},
    };
  },
  mounted() {
    for (const f of this.fields) {
      if (f.type === 'Сильнодействующие' && f.default === true) {
        this.potent_drugs_used[f.title] = '';
      } else if (f.type === 'Наркотические' && f.default === true) {
        this.narcotic_drugs_used[f.title] = '';
      } else if (f.type === 'Показатели человека' && f.default === true) {
        this.patient_params_used[f.title] = '';
      }
    }
    this.intervalTime = setInterval(() => {
      this.setMaxTime();
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
      this.temperature = Number(this.temperature) || 36.6;
      if (this.temperature < 34) {
        this.temperature = 34;
      } else if (this.temperature > 41) {
        this.temperature = 41;
      }
      this.temperature = Number(this.temperature.toFixed(1));
    },
  },
  methods: {
    editColumn(j) {
      if (this.disabled || j + 1 === this.tb_data[0].length) {
        return;
      }
      this.show_anesthesia_sidebar();
      this.isEdit = true;
      const data = {
        patient_params: { ...this.patient_params_used },
        potent_drugs: { ...this.potent_drugs_used },
        narcotic_drugs: { ...this.narcotic_drugs_used },
      };
      for (let i = 0; i < this.tb_data.length; i++) {
        const cat = this.row_category[i];
        const paramName = this.tb_data[i][0];
        const val = this.tb_data[i][j];
        if (paramName && val) {
          if (paramName === 'temperature') {
            this.temperature = Number(val) || 36.6;
          } else if (data[cat]) {
            data[cat][paramName] = val;
          } else if (paramName === 'Параметр') {
            this.timeValue = val;
          }
        }
      }
      this.patient_params_used = data.patient_params;
      this.potent_drugs_used = data.potent_drugs;
      this.narcotic_drugs_used = data.narcotic_drugs;
    },
    sync_heights() {
      const tb_heights = [];
      if (this.$refs.firstTable) {
        window.$(this.$refs.firstTable).find('tr td div').each(function () {
          tb_heights.push(window.$(this).height());
        });
      }
      this.tb_heights = tb_heights;
    },
    focus_next(e) {
      window.$('input', window.$(e.target).next()).focus();
    },
    focus_input(e) {
      window.$(e.target).parent().parent().addClass('active');
    },
    blur_input(e) {
      window.$(e.target).parent().parent().removeClass('active');
    },
    move_focus_next(e) {
      this.move_focus(e);
    },
    move_focus_prev(e) {
      this.move_focus(e, -1);
    },
    move_focus(e, n = 1) {
      const s = 'input.anastesia';
      const nextI = window.$(s).index(e.target) + n;
      const next = window.$(s).eq(nextI);
      if (next.length) {
        next.focus();
      }
    },
    async save_data() {
      await this.$store.dispatch(actions.INC_LOADING);
      this.patient_params_used.temperature = this.temperature;
      const temp_result = {
        time: this.timeValue,
        potent_drugs: this.potent_drugs_used,
        narcotic_drugs: this.narcotic_drugs_used,
        patient_params: this.patient_params_used,
      };
      const research_data = { iss_pk: this.iss, field_pk: this.field_pk };
      this.tb_data.push(temp_result);
      await directionsPoint.anesthesiaResultSave({
        temp_result,
        research_data,
      });
      setTimeout(() => this.sync_heights(), 10);
      await this.load_data();
      await this.$store.dispatch(actions.DEC_LOADING);
      window.okmessage('Сохранено');
      this.show_anesthesia_sidebar();
    },
    async delete_data() {
      try {
        await this.$dialog.confirm('Подтвердите удаление');
      } catch (_) {
        return;
      }
      await this.$store.dispatch(actions.INC_LOADING);
      const research_data = { iss_pk: this.iss, field_pk: this.field_pk };
      const temp_result = {
        time: this.timeValue,
        potent_drugs: this.potent_drugs_used,
        narcotic_drugs: this.narcotic_drugs_used,
        patient_params: this.patient_params_used,
      };
      await directionsPoint.anesthesiaResultSave({
        temp_result,
        research_data,
        action: 'del',
      });
      setTimeout(() => this.sync_heights(), 10);
      await this.load_data();
      await this.$store.dispatch(actions.DEC_LOADING);
      window.okmessage('Запись удалена');
      this.show_anesthesia_sidebar();
    },
    async load_data() {
      await this.$store.dispatch(actions.INC_LOADING);
      const research_data = { iss_pk: this.iss, field_pk: this.field_pk };
      const data = await directionsPoint.anesthesiaLoadData({
        research_data,
      });
      this.tb_data = [...data.data];
      this.row_category = data.row_category;
      setTimeout(() => this.sync_heights(), 10);
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    plus_temperature_start() {
      if (typeof this.temperature !== 'number') {
        this.temperature = 36.6;
      } else {
        this.temperature += 0.1;
      }

      clearInterval(this.interval);

      this.interval = setTimeout(() => {
        clearInterval(this.interval);
        this.interval = setInterval(() => {
          this.temperature += 0.1;
        }, 200);
      }, 400);
    },
    temperature_stop() {
      clearInterval(this.interval);
      this.interval = null;
    },
    minus_temperature_start() {
      if (typeof this.temperature !== 'number') {
        this.temperature = 36.6;
      } else {
        this.temperature -= 0.1;
      }

      clearInterval(this.interval);

      this.interval = setTimeout(() => {
        clearInterval(this.interval);
        this.interval = setInterval(() => {
          this.temperature -= 0.1;
        }, 200);
      }, 400);
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
      Object.entries(obj).forEach(([key]) => {
        // eslint-disable-next-line no-param-reassign
        obj[key] = '';
      });
    },
    clearAll() {
      this.clear_data(this.potent_drugs_used);
      this.clear_data(this.narcotic_drugs_used);
      this.clear_data(this.patient_params_used);
      this.isEdit = false;
      this.actionDelete = false;
      this.setCurrentTime();
    },
    show_anesthesia_sidebar() {
      this.$store.dispatch(actions.CHANGE_STATUS_MENU_ANESTHESIA);
      this.clearAll();
    },
  },
};
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
      top: 63px;
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
      position: relative;

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

      &::before {
        content: "t ______ Cº";
        position: absolute;
        color: #7a7878;
        top: 0;
        line-height: 34.5px;
        left: 119px;
      }
    }

    .scroll-wrapper {
      th {
        padding-left: 5px;
        background: #ccc;
        text-align: left;
      }

      td {
        padding-left: 3px !important;
        border-bottom: 1px solid #0f0f0f;
      }

      td, th {
        padding: 4px;
      }

      tr.active {
        &, & input {
          background-color: #55566b;
          color: #fff;
        }
      }

      tr:hover:not(.active) {
        &, & input {
          background-color: #d7d8ee;
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
        width: 100%;
        height: 34px;
      }
    }
  }

  input:not([type=checkbox]) {
    border: none;
    background-color: #eee;
    width: 100%;
    padding: 5px 1px;
  }

  input[type=checkbox] {
    vertical-align: sub;
  }

  ::placeholder {
    color: #89909b;
  }

  :focus {
    outline: none;
  }

  .time-control {
    width: 100%;
    display: flex;
    flex-direction: row;

    input {
      text-align: center;
      flex: 0 calc(100% - 38px);
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

  .tb-background {
    background-color: #eee;
    margin-bottom: 0;
  }

  .tb-data {
    overflow-x: auto;
    display: flex;
  }

  .table-root {
    margin-top: 5px;

    tr {
      white-space: normal;
      word-break: break-word;
    }

    table {
      border: 1px solid #4b6075;
      table-layout: fixed;
      white-space: nowrap;

      td, th {
        border: 1px solid #4b6075;
        padding: 2px;
      }
    }

    & > table:first-child {
      div {
        width: 110px;
      }

      td {
        font-weight: bold;
      }
    }

    .tb-data {
      table {
        border-left: 0 !important;

        tr:first-of-type, tr td:last-of-type {
          font-weight: bold;
        }

        div {
          width: 88px;

          i {
            font-size: 80%;

            margin-left: -1px;
          }
        }

        tr:first-of-type div {
          white-space: nowrap;
        }

        tr td:first-of-type {
          border-left: 0 !important;
        }
      }
    }
  }

  .GRID-HACK.table-root {
    grid-template-columns: 116px 1fr;
  }

  .row {
    &-patient_params {
      background-color: #e7e7e7;
    }

    &-potent_drugs {
      background-color: #e7d3bd;
    }

    &-narcotic_drugs {
      background-color: #bdd1e7;
    }
  }

</style>
