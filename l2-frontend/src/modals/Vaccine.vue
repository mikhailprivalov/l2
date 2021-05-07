<template>
  <modal ref="modal" @close="hide_modal" show-footer="true" white-bg="true" max-width="680px" width="100%"
         marginLeftRight="auto" margin-top>
    <span slot="header">Вакцинация пациента
      <span v-if="!card_data.fio_age">{{card_data.family}} {{card_data.name}} {{card_data.twoname}},
      {{card_data.age}}, карта {{card_data.num}}</span>
      <span v-else>{{card_data.fio_age}}</span>
    </span>
    <div slot="body" style="min-height: 200px" class="registry-body">
      <table class="table table-bordered table-condensed table-sm-pd"
             style="table-layout: fixed; font-size: 12px">
        <colgroup>
          <col width="70" />
          <col/>
          <col/>
          <col/>
          <col/>
          <col/>
          <col/>
          <col width="45" />
        </colgroup>
        <thead>
        <tr>
          <th>Дата</th>
          <th>Название</th>
          <th>Серия</th>
          <th>Доза</th>
          <th>Способ</th>
          <th>Этап</th>
          <th>Отвод</th>
          <th></th>
        </tr>
        </thead>
        <tbody>
          <tr v-for="r in rows" :key="r.pk">
            <td>{{r.date}}</td>
            <td>{{r.title}}</td>
            <td>{{r.series}}</td>
            <td>{{r.amount}}</td>
            <td>{{r.method}}</td>
            <td>{{r.step}}</td>
            <td>{{r.tap}}</td>
            <td>
                <button class="btn last btn-blue-nb nbr" type="button"
                        v-tippy="{ placement : 'bottom', arrow: true }"
                        title="Редактирование" style="margin-left: -1px" @click="edit(r.pk)">
                  <i class="glyphicon glyphicon-pencil"></i>
                </button>
            </td>
        </tr>
        </tbody>
      </table>
      <div style="margin: 0 auto; width: 200px">
        <button class="btn btn-primary-nb btn-blue-nb"
                @click="edit(-1)"
                type="button"><i class="fa fa-plus"></i> Создать запись</button>
      </div>
      <modal v-if="edit_pk > -2" ref="modalEdit" @close="hide_edit" show-footer="true" white-bg="true" max-width="710px"
             width="100%" marginLeftRight="auto" margin-top>
        <span slot="header" v-if="edit_pk > -1">Редактор вакцинации</span>
        <span slot="header" v-else>Создание записи вакцинации</span>
        <div slot="body" style="min-height: 200px;padding: 10px" class="registry-body">
          <div class="form-group">
            <label for="de-f3">Дата:</label>
            <input class="form-control" type="date" id="de-f3" v-model="edit_data.date" :max="td" required>
          </div>
          <div class="form-group" v-if="edit_data.direction !== ''">
            <label for="de-f5">Направление:</label>
            <input class="form-control" id="de-f5" v-model="edit_data.direction" readonly>
          </div>
          <div class="form-group">
            <label for="de-f6">Название:</label>
            <input class="form-control" id="de-f6" v-model="edit_data.title">
          </div>
          <div class="form-group">
            <label for="de-f7">Серия:</label>
            <input class="form-control" id="de-f7" v-model="edit_data.series">
          </div>
          <div class="form-group">
            <label for="de-f8">Доза:</label>
            <input class="form-control" id="de-f8" v-model="edit_data.amount">
          </div>
          <div class="form-group">
            <label for="de-f81">Способ:</label>
            <input class="form-control" id="de-f81" v-model="edit_data.method">
          </div>
          <div class="form-group">
            <label for="de-f9">Этап:</label>
            <select v-model="edit_data.step" id="de-f9" class="form-control">
              <option v-for="s in steps" :value="s" :key="s">{{s}}</option>
            </select>
          </div>
          <div class="form-group">
            <label for="de-f10">Отвод:</label>
            <input class="form-control" id="de-f10" v-model="edit_data.tap">
          </div>
          <div class="form-group">
            <label for="de-f11">Примечание:</label>
            <textarea class="form-control" id="de-f11" v-model="edit_data.comment"/>
          </div>
        </div>
        <div slot="footer">
          <div class="row">
            <div class="col-xs-4">
              <button @click="hide_edit" class="btn btn-primary-nb btn-blue-nb" type="button">
                Отмена
              </button>
            </div>
            <div class="col-xs-4">
              <button :disabled="!valid" @click="save()" class="btn btn-primary-nb btn-blue-nb" type="button">
                Сохранить
              </button>
            </div>
          </div>
        </div>
      </modal>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-10">
        </div>
        <div class="col-xs-2">
          <button @click="hide_modal" class="btn btn-primary-nb btn-blue-nb" type="button">
            Закрыть
          </button>
        </div>
      </div>
    </div>
  </modal>
</template>

<script>
import moment from 'moment';
import Modal from '../ui-cards/Modal.vue';
import patientsPoint from '../api/patients-point';
import * as actions from '../store/action-types';

export default {
  name: 'vaccine',
  components: { Modal },
  props: {
    card_pk: {
      type: Number,
      required: true,
    },
    card_data: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      rows: [],
      edit_pk: -2,
      td: moment().format('YYYY-MM-DD'),
      edit_data: {
        date: '',
        direction: '',
        title: '',
        series: '',
        amount: '',
        method: '',
        step: 'V',
        tap: '',
        comment: '',
      },
      steps: ['V', 'V1', 'V2', 'V3', 'V4', 'R', 'R1', 'R2', 'R3'],
    };
  },
  created() {
    this.load_data();
  },
  computed: {
    valid() {
      return this.edit_data.date !== '' && this.edit_data.title !== '';
    },
  },
  methods: {
    async edit(pk) {
      this.td = moment().format('YYYY-MM-DD');
      if (pk === -1) {
        this.edit_data = {
          date: moment().format('YYYY-MM-DD'),
          direction: '',
          title: '',
          series: '',
          amount: '',
          method: '',
          step: 'V',
          tap: '',
          comment: '',
        };
      } else {
        const d = await patientsPoint.loadVaccineDetail({ pk });
        this.edit_data = {
          ...this.edit_data,
          ...d,
        };
      }
      this.edit_pk = pk;
    },
    hide_modal() {
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
      this.$root.$emit('hide_vaccine');
    },
    hide_edit() {
      if (this.$refs.modalEdit) {
        this.$refs.modalEdit.$el.style.display = 'none';
      }
      this.edit_pk = -2;
    },
    load_data() {
      this.$store.dispatch(actions.INC_LOADING);
      patientsPoint.loadVaccine(this, 'card_pk').then(({ rows }) => {
        this.rows = rows;
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
      });
    },
    async save() {
      await this.$store.dispatch(actions.INC_LOADING);
      await patientsPoint.saveVaccine({ card_pk: this.card_pk, pk: this.edit_pk, data: this.edit_data });
      await this.$store.dispatch(actions.DEC_LOADING);
      window.okmessage('Сохранено');
      this.hide_edit();
      this.load_data();
    },
  },
};
</script>

<style scoped lang="scss">
  select.form-control {
    padding: 0;
    overflow: visible;
  }

  .nonPrior {
    opacity: .7;

    &:hover {
      opacity: 1;
    }
  }

  .prior {
    background-color: rgba(#000, .05);
  }

  .modal-mask {
    align-items: stretch !important;
    justify-content: stretch !important;
  }

  ::v-deep .panel-flt {
    margin: 41px;
    align-self: stretch !important;
    width: 100%;
    display: flex;
    flex-direction: column;
  }

  ::v-deep .panel-body {
    flex: 1;
    padding: 0;
    height: calc(100% - 91px);
    min-height: 200px;
  }

  .form-row {
    width: 100%;
    display: flex;
    border-bottom: 1px solid #434a54;

    &:first-child:not(.nbt-i) {
      border-top: 1px solid #434a54;
    }

    justify-content: stretch;

    .row-t {
      background-color: #AAB2BD;
      padding: 7px 0 0 10px;
      width: 35%;
      flex: 0 35%;
      color: #fff;
    }

    .input-group {
      flex: 0 65%;
    }

    input, .row-v, ::v-deep input {
      background: #fff;
      border: none;
      border-radius: 0 !important;
      width: 65%;
      flex: 0 65%;
      height: 34px;
    }

    &.sm-f {
      .row-t {
        padding: 2px 0 0 10px;
      }

      input, .row-v, ::v-deep input {
        height: 26px;
      }
    }

    ::v-deep input {
      width: 100% !important;
    }

    .row-v {
      padding: 7px 0 0 10px;
    }

    ::v-deep .input-group {
      border-radius: 0;
    }

    ::v-deep ul {
      width: auto;
      font-size: 13px;
    }

    ::v-deep ul li {
      overflow: hidden;
      text-overflow: ellipsis;
      padding: 2px .25rem;
      margin: 0 .2rem;

      a {
        padding: 2px 10px;
      }
    }
  }

  .col-form {
    &.left {
      padding-right: 0 !important;

      .row-t, input, .row-v, ::v-deep input {
        border-right: 1px solid #434a54 !important;
      }
    }

    &:not(.left):not(.mid) {
      padding-left: 0 !important;

      .row-t {
        border-right: 1px solid #434a54;
      }
    }
  }

  .info-row {
    padding: 7px;
  }

  .individual {
    cursor: pointer;

    &:hover {
      background-color: rgba(0, 0, 0, .15);
    }
  }

  .str ::v-deep .input-group {
    width: 100%;
  }

  .lst {
    margin: 0;
    line-height: 1;
  }

  .mkb10 {
    z-index: 0;
  }

  .mkb10 ::v-deep .input-group {
    width: 100%;
  }

  .mkb10 ::v-deep ul {
    font-size: 13px;
    z-index: 1000;
  }

  .mkb10 ::v-deep ul li {
    overflow: hidden;
    text-overflow: ellipsis;
    padding: 2px .25rem;
    margin: 0 .2rem;

    a {
      padding: 2px 10px;
    }
  }

  tr.stop {
    opacity: .7;
    text-decoration: line-through;

    &:hover {
      opacity: 1;
      text-decoration: none;
    }
  }
</style>
