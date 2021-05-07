<template>
  <modal @close="hide_modal" margin-top marginLeftRight="auto" max-width="680px" ref="modal" show-footer="true"
         white-bg="true" width="100%">
    <span slot="header">Льготы пациента
      <span v-if="!card_data.fio_age">{{card_data.family}} {{card_data.name}} {{card_data.twoname}},
      {{card_data.age}}, карта {{card_data.num}}</span>
      <span v-else>{{card_data.fio_age}}</span>
    </span>
    <div class="registry-body" slot="body" style="min-height: 200px">
      <table class="table table-bordered table-condensed table-sm-pd"
             style="table-layout: fixed; font-size: 12px">
        <colgroup>
          <col width="130"/>
          <col/>
          <col/>
          <col/>
          <col width="45" v-if="!readonly"/>
        </colgroup>
        <thead>
        <tr>
          <th>Вид льготы</th>
          <th>Основание</th>
          <th>Постановка на льготу</th>
          <th>Снятие со льготы</th>
          <th v-if="!readonly"></th>
        </tr>
        </thead>
        <tbody>
        <tr :class="{stop: !!r.date_end}" v-for="r in rows" :key="r.pk">
          <td>{{r.benefit}}</td>
          <td>{{r.registration_basis}}</td>
          <td>{{r.doc_start_reg}}<br/>{{r.date_start}}</td>
          <td>{{r.doc_end_reg}}<br v-if="!!r.date_end"/>{{r.date_end}}</td>
          <td v-if="!readonly">
            <button @click="edit(r.pk)" class="btn last btn-blue-nb nbr"
                    style="margin-left: -1px"
                    title="Редактирование" type="button" v-tippy="{ placement : 'bottom', arrow: true }">
              <i class="glyphicon glyphicon-pencil"></i>
            </button>
          </td>
        </tr>
        </tbody>
      </table>
      <div style="margin: 0 auto; width: 200px" v-if="!readonly">
        <button @click="edit(-1)"
                class="btn btn-primary-nb btn-blue-nb"
                type="button"><i class="fa fa-plus"></i> Создать запись
        </button>
      </div>
      <modal @close="hide_edit" margin-top marginLeftRight="auto" max-width="710px" ref="modalEdit" show-footer="true"
             v-if="edit_pk > -2" white-bg="true" width="100%">
        <span slot="header" v-if="edit_pk > -1">Редактор льготы</span>
        <span slot="header" v-else>Создание льготы</span>
        <div class="registry-body" slot="body" style="min-height: 200px;padding: 10px">
          <div class="form-group">
            <label>Вид льготы:</label>
            <select :readonly="edit_data.close" class="form-control" v-model="edit_data.benefit_id">
              <option :value="x.pk" v-for="x in edit_data.types" :key="x.pk">{{x.title}}</option>
            </select>
          </div>
          <div class="form-group">
            <label for="de-f3">Дата постановки на льготу:</label>
            <input :max="td" :readonly="edit_data.close" class="form-control" id="de-f3" type="date"
                   v-model="edit_data.date_start">
          </div>
          <div class="form-group">
            <label for="de-f6">Основание:</label>
            <textarea class="form-control" id="de-f6" :readonly="edit_data.close"
                      v-model="edit_data.registration_basis"></textarea>
          </div>
          <div class="checkbox" style="padding-left: 15px;">
            <label>
              <input type="checkbox" v-model="edit_data.close"> снят с льготы
            </label>
          </div>
          <div class="form-group" v-if="edit_data.close">
            <label for="de-f5">Дата снятия:</label>
            <input :min="td" class="form-control" id="de-f5" type="date" v-model="edit_data.date_end">
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
import moment from 'moment';
import Modal from '../ui-cards/Modal.vue';
import patientsPoint from '../api/patients-point';
import * as actions from '../store/action-types';

export default {
  name: 'benefit',
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
    readonly: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      td: moment().format('YYYY-MM-DD'),
      rows: [],
      edit_data: {},
      edit_pk: -2,
    };
  },
  created() {
    this.load_data();
  },
  computed: {
    valid_reg() {
      return this.edit_pk > -2
          && this.edit_data.date_start !== ''
          && this.edit_data.registration_basis !== ''
          && (!this.edit_data.close || this.edit_data.date_end !== '');
    },
  },
  methods: {
    async edit(pk) {
      const d = await patientsPoint.loadBenefitDetail({ pk });
      this.edit_data = {
        ...this.edit_data,
        ...d,
        date_start: d.date_start || this.td,
        date_end: d.date_end || this.td,
      };
      this.edit_pk = pk;
    },
    hide_edit() {
      if (this.$refs.modalEdit) {
        this.$refs.modalEdit.$el.style.display = 'none';
      }
      this.edit_pk = -2;
    },
    hide_modal() {
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
      this.$root.$emit('hide_benefit');
    },
    async save() {
      await this.$store.dispatch(actions.INC_LOADING);
      await patientsPoint.saveBenefit({ card_pk: this.card_pk, pk: this.edit_pk, data: this.edit_data });
      await this.$store.dispatch(actions.DEC_LOADING);
      window.okmessage('Сохранено');
      this.hide_edit();
      this.load_data();
    },
    load_data() {
      this.$store.dispatch(actions.INC_LOADING);
      patientsPoint.loadBenefit(this, 'card_pk').then(({ rows }) => {
        this.rows = rows;
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
      });
    },
  },
};
</script>

<style lang="scss" scoped>
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
