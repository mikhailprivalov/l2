<template>
  <modal ref="modal" @close="hide_modal" show-footer="true" white-bg="true" max-width="680px" width="100%" marginLeftRight="auto" margin-top>
    <span slot="header">Диспансерный учёт пациента
      <span v-if="!card_data.fio_age">{{card_data.family}} {{card_data.name}} {{card_data.twoname}},
      {{card_data.age}}, карта {{card_data.num}}</span>
      <span v-else>{{card_data.fio_age}}</span>
    </span>
    <div slot="body" style="min-height: 200px" class="registry-body">
      <table class="table table-bordered table-condensed table-sm-pd"
             style="table-layout: fixed; font-size: 12px">
        <colgroup>
          <col width="70" />
          <col width="98" />
          <col />
          <col width="70" />
          <col />
          <col width="45" />
        </colgroup>
        <thead>
          <tr>
            <th>Дата начала</th>
            <th>Дата прекращения</th>
            <th>Диагноз</th>
            <th>Код по МКБ-10</th>
            <th>Врач</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rows" :class="{stop: !!r.date_end}">
            <td>{{r.date_start}}</td>
            <td>{{r.date_end}}</td>
            <td>{{r.illnes}}</td>
            <td>{{r.diagnos}}</td>
            <td>{{r.spec_reg}} {{r.doc_start_reg}}</td>
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
      <modal v-if="edit_pk > -2" ref="modalEdit" @close="hide_edit" show-footer="true" white-bg="true" max-width="710px" width="100%" marginLeftRight="auto" margin-top>
        <span slot="header" v-if="edit_pk > -1">Редактор диспансерного учёта</span>
        <span slot="header" v-else>Создание записи диспансерного учёта</span>
        <div slot="body" style="min-height: 200px;padding: 10px" class="registry-body">
          <div class="form-group">
            <label for="de-f3">Дата начала:</label>
            <input class="form-control" type="date" id="de-f3" v-model="edit_data.date_start" :max="td"
                   :readonly="edit_data.close">
          </div>
          <div class="form-group mkb10" style="width: 100%">
            <label>Диагноз в полной форме (код по МКБ и название):</label>
            <m-k-bfield v-model="edit_data.diagnos" v-if="!edit_data.close" :short="false" />
            <input class="form-control" v-model="edit_data.diagnos" v-else readonly>
          </div>
          <div class="checkbox" style="padding-left: 15px;">
            <label>
              <input type="checkbox" v-model="edit_data.close"> прекращён
            </label>
          </div>
          <div class="form-group" v-if="edit_data.close">
            <label for="de-f5">Дата прекращения:</label>
            <input class="form-control" type="date" id="de-f5" v-model="edit_data.date_end" :min="td">
          </div>
          <div class="form-group" v-if="edit_data.close">
            <label for="de-f6">Причина прекращения:</label>
            <input class="form-control" id="de-f6" v-model="edit_data.why_stop">
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
              <button :disabled="!valid_reg" @click="save()" class="btn btn-primary-nb btn-blue-nb" type="button">
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
  import Modal from './ui-cards/Modal'
  import patients_point from './api/patients-point'
  import * as action_types from './store/action-types'
  import MKBfield from './MKBField'
  import moment from 'moment';

  export default {
    name: 'd-reg',
    components: {Modal, MKBfield},
    props: {
      card_pk: {
        type: Number,
        required: true
      },
      card_data: {
        type: Object,
        required: true,
      },
    },
    data() {
      return {
        td: moment().format('YYYY-MM-DD'),
        rows: [],
        edit_data: {
          date_start: '',
          date_end: '',
          why_stop: '',
          close: false,
          diagnos: '',
          illnes: '',
        },
        edit_pk: -2,
      }
    },
    created() {
      this.load_data()
    },
    computed: {
      valid_reg() {
        return this.edit_pk > -2 &&
          this.edit_data.diagnos.match(/^[A-Z]\d{1,2}(\.\d{1,2})?.*/gm) &&
          this.edit_data.date_start !== '' &&
          (!this.edit_data.close || this.edit_data.date_end !== '');
      }
    },
    methods: {
      async edit(pk) {
        if (pk === -1) {
          this.edit_data = {
            date_start: this.td,
            date_end: this.td,
            why_stop: '',
            close: false,
            diagnos: '',
            illnes: '',
          };
        } else {
          const d = await patients_point.loadDregDetail(pk);
          this.edit_data = {
            ...this.edit_data,
            ...d,
            date_end: d.date_end || this.td,
          };
        }
        this.edit_pk = pk;
      },
      hide_edit() {
        this.$refs.modalEdit.$el.style.display = 'none';
        this.edit_pk = -2;
      },
      hide_modal() {
        this.$refs.modal.$el.style.display = 'none'
        this.$root.$emit('hide_dreg')
      },
      async save() {
        await this.$store.dispatch(action_types.INC_LOADING)
        const data = await patients_point.saveDreg(this.card_pk, this.edit_pk, this.edit_data)
        this.$store.dispatch(action_types.DEC_LOADING).then()
        okmessage('Сохранено');
        this.hide_edit()
        this.load_data()
      },
      load_data() {
        let vm = this
        vm.$store.dispatch(action_types.INC_LOADING).then()
        patients_point.loadDreg(vm.card_pk).then(({rows}) => {
          vm.rows = rows
        }).finally(() => {
          vm.$store.dispatch(action_types.DEC_LOADING).then()
        })
      },
    }
  }
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

  /deep/ .panel-flt {
    margin: 41px;
    align-self: stretch !important;
    width: 100%;
    display: flex;
    flex-direction: column;
  }

  /deep/ .panel-body {
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

    input, .row-v, /deep/ input {
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
      input, .row-v, /deep/ input {
        height: 26px;
      }
    }

    /deep/ input {
      width: 100% !important;
    }
    .row-v {
      padding: 7px 0 0 10px;
    }

    /deep/ .input-group {
      border-radius: 0;
    }

    /deep/ ul {
      width: auto;
      font-size: 13px;
    }

    /deep/ ul li {
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
      padding-right: 0!important;

      .row-t, input, .row-v, /deep/ input {
        border-right: 1px solid #434a54 !important;
      }
    }
    &:not(.left):not(.mid) {
      padding-left: 0!important;
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
  .str /deep/ .input-group {
    width: 100%;
  }

  .lst {
    margin: 0;
    line-height: 1;
  }

  .mkb10 {
    z-index: 0;
  }

  .mkb10 /deep/ .input-group {
    width: 100%;
  }

  .mkb10 /deep/ ul {
    font-size: 13px;
    z-index: 1000;
  }

  .mkb10 /deep/ ul li {
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
