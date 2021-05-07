<template>
  <modal ref="modal" @close="hide_modal" show-footer="true" white-bg="true" max-width="680px" width="100%"
         marginLeftRight="auto" margin-top>
    <span slot="header">Сведения из амбулаторной карты
      <span v-if="!card_data.fio_age">{{card_data.family}} {{card_data.name}} {{card_data.twoname}},
      {{card_data.age}}, карта {{card_data.num}}</span>
      <span v-else>{{card_data.fio_age}}</span>
    </span>
    <div slot="body" style="min-height: 200px" class="registry-body">
      <table class="table table-bordered table-condensed table-sm-pd layout">
        <colgroup>
          <col width="100"/>
          <col width="100"/>
          <col width="430"/>
        </colgroup>
        <thead>
        <tr>
          <th>Год</th>
          <th>Месяц</th>
          <th>Сведения</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="r in rows" :key="r.date">
          <td>{{r.date.slice(6)}}</td>
          <td>{{r.date.slice(3,5)}}</td>
          <td><span v-html="r.data.replace(/\n/g, '<br/>')"></span></td>
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
                type="button"><i class="fa fa-plus"></i> Создать запись
        </button>
      </div>
      <modal v-if="edit_pk > -2" ref="modalEdit" @close="hide_edit" show-footer="true" white-bg="true" max-width="710px"
             width="100%" marginLeftRight="auto" margin-top>
        <span slot="header" v-if="edit_pk > -1">Редактор сведений</span>
        <span slot="header" v-else>Создание записи</span>
        <div slot="body" style="min-height: 200px;padding: 10px" class="registry-body">
          <div class="form-group">
            <label for="de-f1">Дата:</label>
            <input class="form-control date" type="month" id="de-f1" v-model="edit_data.date" :max="td" required>
          </div>
          <div class="form-group">
            <label for="de-f2">Данные:</label>
            <textarea class="form-control" id="de-f2" rows="10" v-model="edit_data.data"/>
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
      <modal v-if="show_history_ambulatory" ref="modalEdit" @close="hide_edit" show-footer="true" white-bg="true"
             max-width="710px"
             width="100%" marginLeftRight="auto" margin-top>
        <span slot="header">История изменений</span>
        <div slot="body" style="min-height: 200px;padding: 10px" class="registry-body">
          <table class="table table-bordered table-condensed table-sm-pd layout">
            <colgroup>
              <col width="100"/>
              <col width="530"/>
            </colgroup>
            <thead>
            <tr>
              <th>Дата</th>
              <th>Сводные данные</th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="r in rows_history" :key="r.date">
              <td>{{r.date}}</td>
              <td>{{r.data}}</td>
            </tr>
            </tbody>
          </table>
        </div>
        <div slot="footer">
          <div class="row">
            <div class="col-xs-4">
              <button @click="hide_edit" class="btn btn-primary-nb btn-blue-nb" type="button">
                Отмена
              </button>
            </div>
          </div>
        </div>
      </modal>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-12">
          <div class="col-xs-4">
            <button @click="show_history_ambulatory_data" class="btn btn-primary-nb btn-blue-nb" type="button">
              История изменений
            </button>
          </div>
          <div class="col-xs-4">
            <button @click="hide_modal" class="btn btn-primary-nb btn-blue-nb" type="button">
              Закрыть
            </button>
          </div>
          <div class="col-xs-4">
            <button @click="open_form_112" class="btn btn-primary-nb btn-blue-nb" type="button">
              Печать
            </button>
          </div>
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
import { form112 } from '../forms';

export default {
  name: 'AmbulatoryData',
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
      td: moment().format('YYYY-MM'),
      edit_data: {
        date: '',
        data: '',
      },
      show_history_ambulatory: false,
      rows_history: [],
    };
  },
  created() {
    this.load_data();
  },
  computed: {
    forms() {
      return form112.map((f) => ({
        ...f,
        url: f.url.kwf({
          card: this.card_pk,
        }),
      }));
    },
    valid() {
      return this.edit_data.date !== '' && this.edit_data.data !== '';
    },
  },
  methods: {
    open_form_112() {
      window.open(this.forms[0].url);
    },
    show_history_ambulatory_data() {
      this.show_history_ambulatory = true;
      this.$store.dispatch(actions.INC_LOADING);
      patientsPoint.loadAmbulatoryHistory(this, 'card_pk').then(({ rows }) => {
        this.rows_history = rows;
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
      });
    },
    async edit(pk) {
      this.td = moment().format('YYYY-MM');
      if (pk === -1) {
        this.edit_data = {
          date: this.td,
          data: '',
        };
      } else {
        const d = await patientsPoint.loadAmbulatoryDataDetail({ pk });
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
      this.$root.$emit('hide_ambulatory_data');
    },
    hide_edit() {
      if (this.$refs.modalEdit) {
        this.$refs.modalEdit.$el.style.display = 'none';
      }
      this.edit_pk = -2;
      this.show_history_ambulatory = false;
    },
    load_data() {
      this.$store.dispatch(actions.INC_LOADING);
      patientsPoint.loadAmbulatoryData(this, 'card_pk').then(({ rows }) => {
        this.rows = rows;
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
      });
    },
    async save() {
      await this.$store.dispatch(actions.INC_LOADING);
      await patientsPoint.saveAmbulatoryData({ card_pk: this.card_pk, pk: this.edit_pk, data: this.edit_data });
      await this.$store.dispatch(actions.DEC_LOADING);
      window.okmessage('Сохранено');
      this.hide_edit();
      this.load_data();
    },
  },
};
</script>

<style scoped lang="scss">
  .align-button {
    float: right;
  }

  .layout {
    table-layout: fixed;
    font-size: 12px
  }

  .date {
    width: 200px;
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

</style>
