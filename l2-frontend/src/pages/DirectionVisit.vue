<template>
  <div>
    <div class="row">
      <div class="col-xs-12 col-sm-12 col-md-6">
        <div>
          <div class="panel panel-flt nbl" style="margin-bottom: 10px">
            <div class="panel-heading" style="padding-top: 0;padding-bottom: 0;height: 34px">
              <span style="margin-top: 7px;display: inline-block;">Направление</span>
            </div>

            <ul class="list-group">
              <li class="list-group-item">
                <div class="input-group">
                  <input type="text" class="form-control" v-model="direction" data-container="body"
                         data-toggle="popover" data-placement="bottom" data-content="" spellcheck="false" autofocus
                         placeholder="Введите номер направления" @keyup.enter="load" ref="field">
                  <span class="input-group-btn">
                        <button class="btn btn-blue-nb" @click="load" type="button">Загрузить</button>
                  </span>
                </div>
              </li>

              <li class="list-group-item" v-if="loaded_pk > 0">
                <table class="table table-bordered table-condensed dirtb"
                       style="margin-bottom: 0;background-color: #fff">
                  <tr>
                    <td>Номер</td>
                    <td>
                      <h3 style="margin: 2px;padding: 0;">{{loaded_pk}}
                        <small><a class="a-under" href="#" @click.prevent="print_direction">печать</a></small>
                      </h3>
                    </td>
                  </tr>
                  <tr>
                    <td>Дата назначения</td>
                    <td>{{direction_data.date}}</td>
                  </tr>
                  <tr>
                    <td>Пациент</td>
                    <td>{{direction_data.client}}</td>
                  </tr>
                  <tr>
                    <td>Карта</td>
                    <td>{{direction_data.card}}</td>
                  </tr>
                  <tr v-if="!direction_data.imported_from_rmis">
                    <td>Л/врач</td>
                    <td>{{direction_data.doc}}</td>
                  </tr>
                  <tr v-if="!direction_data.imported_from_rmis">
                    <td>Источник финансирования</td>
                    <td>{{direction_data.fin_source}}</td>
                  </tr>
                  <tr v-if="!direction_data.imported_from_rmis">
                    <td>Диагноз</td>
                    <td>{{direction_data.diagnos}}</td>
                  </tr>
                  <tr v-else>
                    <td>Огранизация</td>
                    <td>{{direction_data.imported_org}}</td>
                  </tr>
                </table>
              </li>
              <li class="list-group-item" v-if="loaded_pk > 0">
                <div v-for="r in researches" :key="r.pk" class="research-card card card-1 card-no-hover">
                  <div>
                    <span v-if="r.tube" class="tube-pk">{{r.tube.pk}}</span>&nbsp;
                    {{r.title}} <span class="comment" v-if="r.comment"> [{{r.comment}}]</span>
                  </div>
                  <div v-if="r.tube" style="margin-top: 5px">
                    <a style="float: right" class="a-under" href="#" @click.prevent="print_tube_iss(r.tube.pk)">печать ш/к</a>
                    <!-- eslint-disable-next-line max-len -->
                    <span :style="`background-color: ${r.tube.color};display: inline-block;width: 10px;height: 10px;border: 1px solid #aab2bd;`"></span>
                    <span>{{r.tube.title}}</span>
                  </div>
                </div>
              </li>
              <li class="list-group-item" v-if="loaded_pk > 0">
                <div class="row">
                  <div class="col-xs-5 col-sm-5 col-md-5 col-lg-6">
                    <button class="btn btn-blue-nb" @click="cancel">Отмена</button>
                  </div>
                  <div class="col-xs-7 col-sm-7 col-md-7 col-lg-6 text-right">
                    <div>
                      <template v-if="direction_data.has_microbiology">
                        <button @click="make_visit()" class="btn btn-blue-nb" v-if="!visit_status && can_get">
                          Регистрация забора биоматерала
                        </button>
                      </template>
                      <button @click="make_visit()" class="btn btn-blue-nb" v-else-if="!visit_status && can_visit">
                        Зарегистрировать посещение
                      </button>
                    </div>
                    <div class="float-right" v-if="visit_status">
                      Посещение {{visit_date}}<br/>
                      {{direction_data.visit_who_mark}}
                      <div v-if="allow_reset_confirm">
                        <a @click.prevent="cancel_visit" class="a-under" href="#"
                           v-if="direction_data.has_microbiology && can_get">
                          отменить забор материала
                        </a>
                        <a @click.prevent="cancel_visit" class="a-under" href="#"
                           v-else-if="!direction_data.has_microbiology && can_visit">отменить посещение</a>
                      </div>
                    </div>
                    <div class="float-right" style="margin-top: 10px"
                         v-if="direction_data.has_microbiology && can_receive">
                      <div v-if="receive_status">
                        Материал принят<br/>{{receive_datetime}}<br/>
                        <a @click.prevent="cancel_receive" class="a-under" href="#">отменить приём материала</a>
                      </div>
                      <div v-else>
                        <button @click="make_receive()" class="btn btn-blue-nb">
                          Принять материал
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </li>
              <li v-else class="list-group-item text-center">
                направление не загружено
              </li>
            </ul>
          </div>
        </div>
      </div>
      <div class="col-xs-12 col-sm-12 col-md-6">
        <div class="panel panel-flt" v-if="can_visit || can_get">
          <div class="panel-heading" style="padding-top: 0;padding-bottom: 0;padding-right: 0;height: 34px">
            <date-field-nav class="btr" :brn="false" w="190px" style="float: right"
                            :val.sync="journal_date" :def="journal_date"/>
            <span style="margin-top: 7px;display: inline-block;">Журнал посещений</span></div>
          <div class="panel-body" style="padding-top: 5px">
            <div class="text-right" style="margin-bottom: 5px">
              <a href="#" class="fli a-under" @click.prevent="show_modal">создание отчёта</a></div>
            <div v-if="journal_data.length === 0" class="text-center">
              нет данных
            </div>
            <table class="table table-bordered table-condensed dirtb visits"
                   style="margin-bottom: 0;background-color: #fff"
                   v-else>
              <thead>
              <tr>
                <th>Направление</th>
                <th>Дата и время</th>
                <th>Пациент</th>
              </tr>
              </thead>
              <tbody>
              <tr v-for="r in journal_data" :key="r.pk">
                <td>{{r.pk}}</td>
                <td>{{r.datetime}}</td>
                <td>{{r.client}}</td>
              </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="panel panel-flt" v-if="can_receive">
          <div class="panel-heading" style="padding-top: 0;padding-bottom: 0;padding-right: 0;height: 34px">
            <date-field-nav :brn="false" :def="journal_recv_date" :val.sync="journal_recv_date" class="btr"
                            style="float: right" w="190px"/>
            <span style="margin-top: 7px;display: inline-block;">Журнал приёма материала</span></div>
          <div class="panel-body" style="padding-top: 5px">
            <div class="text-center" v-if="journal_recv_data.length === 0">
              <br/>
              нет данных
            </div>
            <table class="table table-bordered table-condensed dirtb visits"
                   style="margin-bottom: 0;background-color: #fff"
                   v-else>
              <thead>
              <tr>
                <th>Направление</th>
                <th>Дата и время</th>
                <th>Пациент</th>
                <th>Ёмкость</th>
              </tr>
              </thead>
              <tbody>
              <tr v-for="r in journal_recv_data" :key="r.pk">
                <td>{{r.pk}}</td>
                <td>{{r.datetime}}</td>
                <td>{{r.client}}</td>
                <td>
                  <div v-for="t in r.tubes" :key="`${t.title}_${t.color}`">
                    <!-- eslint-disable-next-line max-len -->
                    <span :style="`background-color: ${t.color};display: inline-block;width: 10px;height: 10px;border: 1px solid #aab2bd;`"></span>
                    {{t.title}}
                  </div>
                </td>
              </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
    <modal ref="modal" v-show="showModal" @close="hide_modal" show-footer="true">
      <span slot="header">Настройка отчёта</span>
      <div slot="body">
        <span>Период: </span>
        <div style="width: 186px;display: inline-block;vertical-align: middle">
          <date-range v-model="date_range"/>
        </div>
      </div>
      <div slot="footer" class="text-center">
        <div class="row">
          <div class="col-xs-6">
            <button type="button" @click="report('sum')" class="btn btn-primary-nb btn-blue-nb btn-ell">
              Суммарный отчёт
            </button>
          </div>
        </div>
      </div>
    </modal>
  </div>
</template>

<script>
import moment from 'moment';
import DateFieldNav from '../fields/DateFieldNav.vue';
import DateRange from '../ui-cards/DateRange.vue';
import directionsPoint from '../api/directions-point';
import * as actions from '../store/action-types';
import Modal from '../ui-cards/Modal.vue';

/**
     * @return {number}
     */
function TryParseInt(str, defaultValue) {
  let retValue = defaultValue;
  if (str !== null) {
    if (str.length > 0) {
      if (!Number.isNaN(str)) {
        retValue = parseInt(str, 10);
      }
    }
  }
  return retValue;
}

export default {
  name: 'direction-visit',
  components: {
    DateFieldNav,
    Modal,
    DateRange,
  },
  data() {
    return {
      loaded_pk: -1,
      direction: '',
      in_load: false,
      showModal: false,
      researches: [],
      visit_status: false,
      receive_status: false,
      receive_datetime: null,
      allow_reset_confirm: false,
      visit_date: '',
      direction_data: {},
      journal_date: moment().format('DD.MM.YYYY'),
      journal_data: [],
      journal_recv_date: moment().format('DD.MM.YYYY'),
      journal_recv_data: [],
      date_range: [moment().format('DD.MM.YYYY'), moment().format('DD.MM.YYYY')],
    };
  },
  computed: {
    query_int() {
      return TryParseInt(this.direction, -1);
    },
    can_get() {
      if ('groups' in this.$store.getters.user_data) {
        for (const g of this.$store.getters.user_data.groups) {
          if (g === 'Заборщик биоматериала микробиологии') {
            return true;
          }
        }
      }
      return false;
    },
    can_receive() {
      if ('groups' in this.$store.getters.user_data) {
        for (const g of this.$store.getters.user_data.groups) {
          if (g === 'Получатель биоматериала микробиологии') {
            return true;
          }
        }
      }
      return false;
    },
    can_visit() {
      if ('groups' in this.$store.getters.user_data) {
        for (const g of this.$store.getters.user_data.groups) {
          if (g === 'Посещения по направлениям' || g === 'Врач параклиники' || g === 'Врач консультаций') {
            return true;
          }
        }
      }
      return false;
    },
  },
  watch: {
    journal_date() {
      this.load_journal();
    },
    journal_recv_date() {
      this.load_recv_journal();
    },
  },
  mounted() {
    this.load_journal();
    this.load_recv_journal();
  },
  methods: {
    report(t) {
      // eslint-disable-next-line max-len
      window.open(`/statistic/xls?type=statistics-visits&users=${encodeURIComponent(JSON.stringify([this.$store.getters.user_data.doc_pk]))}&date-start=${this.date_range[0]}&date-end=${this.date_range[1]}&t=${t}`, '_blank');
    },
    hide_modal() {
      this.showModal = false;
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
    },
    show_modal() {
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'flex';
      }
      this.showModal = true;
    },
    cancel() {
      this.loaded_pk = -1;
      this.researches = [];
      this.visit_status = false;
      this.allow_reset_confirm = false;
      this.visit_date = '';
      this.direction_data = {};
    },
    print_direction() {
      if (this.loaded_pk === -1) return;
      this.$root.$emit('print:directions', [this.loaded_pk]);
    },
    load_journal() {
      this.$store.dispatch(actions.INC_LOADING);
      directionsPoint.visitJournal({ date: this.journal_date }).then((data) => {
        this.journal_data = data.data;
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
      });
    },
    load_recv_journal() {
      this.$store.dispatch(actions.INC_LOADING);
      directionsPoint.recvJournal({ date: this.journal_recv_date }).then((data) => {
        this.journal_recv_data = data.data;
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
      });
    },
    load() {
      if (this.query_int === -1) {
        return;
      }
      if (this.in_load) return;
      this.$store.dispatch(actions.INC_LOADING);
      this.in_load = true;
      this.cancel();
      directionsPoint.getDirectionsServices({ pk: this.query_int }).then((data) => {
        if (data.ok) {
          this.loaded_pk = data.loaded_pk;
          this.researches = data.researches;
          this.direction_data = data.direction_data;
          this.visit_status = data.visit_status;
          this.visit_date = data.visit_date;
          this.receive_status = !!data.direction_data.receive_datetime;
          this.receive_datetime = data.direction_data.receive_datetime;
          this.allow_reset_confirm = data.allow_reset_confirm;
          this.blur();
        } else {
          window.errmessage(data.message);
        }
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
        this.in_load = false;
        this.direction = '';
      });
    },
    focus() {
      window.$(this.$refs.field).focus();
    },
    blur() {
      window.$(this.$refs.field).blur();
    },
    cancel_visit() {
      // eslint-disable-next-line no-restricted-globals,no-alert
      if (confirm('Вы уверены, что хотите отменить посещение?')) {
        this.make_visit(true);
      }
    },
    make_visit(cancel = false) {
      if (this.loaded_pk === -1 || this.in_load) return;
      this.$store.dispatch(actions.INC_LOADING);
      this.in_load = true;
      directionsPoint.getMarkDirectionVisit({ pk: this.loaded_pk, cancel }).then((data) => {
        if (data.ok) {
          this.visit_status = data.visit_status;
          this.visit_date = data.visit_date;
          this.allow_reset_confirm = data.allow_reset_confirm;
          this.focus();
        } else {
          window.errmessage(data.message);
        }
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
        this.in_load = false;
        this.load_journal();
      });
    },
    print_tube_iss(pk) {
      this.$root.$emit('print:barcodes:iss', [pk]);
    },
    cancel_receive() {
      // eslint-disable-next-line no-restricted-globals,no-alert
      if (confirm('Вы уверены, что хотите отменить приём биоматериала?')) {
        this.make_receive(true);
      }
    },
    make_receive(cancel = false) {
      if (this.loaded_pk === -1 || this.in_load) return;
      this.$store.dispatch(actions.INC_LOADING);
      this.in_load = true;
      directionsPoint.drectionReceiveMaterial({ pk: this.loaded_pk, cancel }).then((data) => {
        if (data.ok) {
          this.receive_status = !!data.receive_datetime;
          this.receive_datetime = data.receive_datetime;
          this.focus();
        } else {
          window.errmessage(data.message);
        }
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
        this.in_load = false;
        this.load_recv_journal();
      });
    },
  },
};
</script>

<style scoped lang="scss">
  .dirtb td {
    vertical-align: middle;
    padding: 2px;
    border: 1px solid #ddd;
  }

  .dirtb tr td:last-child {
    text-align: left;
  }

  .dirtb:not(.visits) tr td:first-child {
    font-weight: 600;
    width: 170px;
  }

  .dirtb td:first-child {
    padding-left: 10px;
  }

  .fli {
    text-decoration: underline;
    margin-left: 5px;
  }

  .fli:hover {
    text-decoration: none;
  }

  .btr ::v-deep input {
    border-radius: 0 4px 0 0;
  }

  .comment {
    margin-left: 3px;
    color: #049372;
    font-weight: 600;
  }

  .research-card {
    padding: 5px;
    margin-bottom: 15px;
  }
</style>
