<template>
  <div>
    <div class="row">
      <div class="col-xs-12 col-sm-12 col-md-6">
        <div>
          <div
            class="panel panel-flt nbl"
            style="margin-bottom: 10px"
          >
            <div
              class="panel-heading"
              style="padding-top: 0;padding-bottom: 0;height: 34px"
            >
              <span style="margin-top: 7px;display: inline-block;">Направление</span>
            </div>

            <ul class="list-group">
              <li class="list-group-item">
                <div class="input-group">
                  <input
                    ref="field"
                    v-model="direction"
                    type="text"
                    class="form-control"
                    data-container="body"
                    data-toggle="popover"
                    data-placement="bottom"
                    data-content=""
                    spellcheck="false"
                    autofocus
                    placeholder="Введите номер направления"
                    @keyup.enter="load"
                  >
                  <span class="input-group-btn">
                    <button
                      class="btn btn-blue-nb"
                      type="button"
                      @click="load"
                    >Загрузить</button>
                  </span>
                </div>
              </li>

              <li
                v-if="loaded_pk > 0"
                class="list-group-item"
              >
                <table
                  class="table table-bordered table-condensed dirtb"
                  style="margin-bottom: 0;background-color: #fff"
                >
                  <tr>
                    <td>Номер</td>
                    <td>
                      <h3 style="margin: 2px;padding: 0;">
                        {{ loaded_pk }}
                        <small><a
                          class="a-under"
                          href="#"
                          @click.prevent="print_direction"
                        >печать</a></small>
                      </h3>
                    </td>
                  </tr>
                  <tr>
                    <td>Дата назначения</td>
                    <td>{{ direction_data.date }}</td>
                  </tr>
                  <tr>
                    <td>Пациент</td>
                    <td>{{ direction_data.client }}</td>
                  </tr>
                  <tr>
                    <td>Карта</td>
                    <td>{{ direction_data.card }}</td>
                  </tr>
                  <tr v-if="!direction_data.imported_from_rmis">
                    <td>Л/врач</td>
                    <td>{{ direction_data.doc }}</td>
                  </tr>
                  <tr v-if="!direction_data.imported_from_rmis">
                    <td>Источник финансирования</td>
                    <td>{{ direction_data.fin_source }}</td>
                  </tr>
                  <tr v-if="!direction_data.imported_from_rmis && direction_data.priceCategory">
                    <td>Платная категория</td>
                    <td>{{ direction_data.priceCategory }}</td>
                  </tr>
                  <tr v-if="!direction_data.imported_from_rmis">
                    <td>Диагноз</td>
                    <td>{{ direction_data.diagnos }}</td>
                  </tr>
                  <tr v-else>
                    <td>Организация</td>
                    <td>{{ direction_data.imported_org }}</td>
                  </tr>
                  <tr v-if="l2_decriptive_coexecutor">
                    <td :class="{ 'status-none': !direction_data.coExecutor }">
                      Лаборант
                    </td>
                    <td class="cl-td">
                      <Treeselect
                        v-model="direction_data.coExecutor"
                        class="reeselect-noborder-left treeselect-wide treeselect-34px"
                        :multiple="false"
                        :disable-branch-nodes="true"
                        :options="laborantUsers"
                        placeholder="Исполнитель не выбран"
                        :disabled="visit_status"
                        :align="left"
                      />
                    </td>
                  </tr>
                  <tr v-if="l2_decriptive_additional_number">
                    <td :class="{ 'status-none': !direction_data.additionalNumber }">
                      Рег. номер
                    </td>
                    <td class="cl-td">
                      <div class="input-group additional-number-group input-group-flex">
                        <input
                          v-model.trim="direction_data.additionalNumber"
                          class="form-control"
                          :disabled="visit_status"
                        >
                        <input
                          :value="direction_data.additionalNumberYear || currentYear"
                          class="form-control"
                          readonly
                        >
                        <span class="input-group-btn">
                          <button
                            v-tippy="{ placement : 'bottom'}"
                            class="btn btn-default btn-primary-nb"
                            title="Освободить номер"
                            :disabled="visit_status"
                            @click="clearAdditionalNumber"
                          >
                            <i class="fa fa-times" />
                          </button>
                        </span>
                      </div>
                    </td>
                  </tr>
                  <tr v-if="direction_data.has_gistology">
                    <td :class="{ 'status-none': !direction_data.gistology_receive_time }">
                      Материал принят
                    </td>
                    <td class="cl-td">
                      <input
                        v-model="direction_data.gistology_receive_time"
                        type="datetime-local"
                        :readonly="visit_status"
                        step="1"
                        class="form-control"
                      >
                    </td>
                  </tr>
                  <tr v-if="direction_data.has_gistology && !visit_status && can_visit">
                    <td>
                      Дата регистрации
                      <input
                        v-model="manualDateVisit"
                        type="checkbox"
                        class="ml-5"
                      >
                    </td>
                    <td
                      v-if="manualDateVisit"
                      class="cl-td"
                    >
                      <input
                        v-model="visit_date"
                        type="datetime-local"
                        :readonly="visit_status"
                        step="1"
                        class="form-control"
                      >
                    </td>
                  </tr>
                  <tr v-if="direction_data.has_gistology">
                    <td :class="{ 'status-none': !direction_data.planedDoctorExecutor }">
                      Врач
                    </td>
                    <td class="cl-td">
                      <Treeselect
                        v-model="direction_data.planedDoctorExecutor"
                        class="reeselect-noborder-left treeselect-wide treeselect-34px"
                        :multiple="false"
                        :disable-branch-nodes="true"
                        :options="users"
                        placeholder="Исполнитель не выбран"
                        :disabled="visit_status"
                        :align="left"
                      />
                    </td>
                  </tr>
                </table>
              </li>
              <li
                v-if="loaded_pk > 0"
                class="list-group-item"
              >
                <div
                  v-for="r in researches"
                  :key="r.pk"
                  class="research-card card card-1 card-no-hover"
                >
                  <div>
                    <span
                      v-if="r.tube"
                      class="tube-pk"
                    >{{ r.tube.pk }}</span>&nbsp;
                    {{ r.title }} <span
                      v-if="r.comment"
                      class="comment"
                    > [{{ r.comment }}]</span>
                  </div>
                  <div
                    v-if="r.tube"
                    style="margin-top: 5px"
                  >
                    <a
                      style="float: right"
                      class="a-under"
                      href="#"
                      @click.prevent="print_tube_iss(r.tube.pk)"
                    >печать ш/к</a>
                    <!-- eslint-disable-next-line max-len -->
                    <span :style="`background-color: ${r.tube.color};display: inline-block;width: 10px;height: 10px;border: 1px solid #aab2bd;`" />
                    <span>{{ r.tube.title }}</span>
                  </div>
                </div>
              </li>
              <li
                v-if="loaded_pk > 0"
                class="list-group-item"
              >
                <div class="row">
                  <div class="col-xs-5 col-sm-5 col-md-5 col-lg-6">
                    <button
                      class="btn btn-blue-nb"
                      @click="cancel"
                    >
                      Отмена
                    </button>
                    <button
                      v-if="direction_data.has_gistology"
                      class="btn btn-blue-nb"
                      @click="show_modal_protocol(loaded_pk)"
                    >
                      Протокол
                    </button>
                  </div>
                  <div class="col-xs-7 col-sm-7 col-md-7 col-lg-6 text-right">
                    <div>
                      <template v-if="direction_data.has_microbiology">
                        <button
                          v-if="!visit_status && can_get"
                          class="btn btn-blue-nb"
                          @click="make_visit()"
                        >
                          Регистрация забора биоматериала
                        </button>
                      </template>
                      <button
                        v-else-if="!visit_status && can_visit && fillRequiredField"
                        class="btn btn-blue-nb"
                        @click="make_visit()"
                      >
                        Зарегистрировать направление
                      </button>
                    </div>
                    <div
                      v-if="visit_status"
                      class="float-right"
                    >
                      Посещение {{ visit_date }}<br>
                      {{ direction_data.visit_who_mark }}
                      <div v-if="allow_reset_confirm">
                        <a
                          v-if="direction_data.has_microbiology && can_get"
                          class="a-under"
                          href="#"
                          @click.prevent="cancel_visit"
                        >
                          отменить забор материала
                        </a>
                        <a
                          v-else-if="!direction_data.has_microbiology && can_visit"
                          class="a-under"
                          href="#"
                          @click.prevent="cancel_visit"
                        >отменить регистрацию</a>
                      </div>
                    </div>
                    <div
                      v-if="!fillRequiredField && direction_data.has_gistology "
                      class="status-none"
                    >
                      Введите полные данные
                    </div>
                    <div
                      v-if="direction_data.has_microbiology && can_receive"
                      class="float-right"
                      style="margin-top: 10px"
                    >
                      <div v-if="receive_status">
                        Материал принят<br>{{ receive_datetime }}<br>
                        <a
                          class="a-under"
                          href="#"
                          @click.prevent="cancel_receive"
                        >отменить приём материала</a>
                      </div>
                      <div v-else>
                        <button
                          class="btn btn-blue-nb"
                          @click="make_receive()"
                        >
                          Принять материал
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </li>
              <li
                v-else
                class="list-group-item text-center"
              >
                направление не загружено
              </li>
            </ul>
          </div>
        </div>
      </div>
      <div class="col-xs-12 col-sm-12 col-md-6">
        <div
          v-if="can_visit || can_get"
          class="panel panel-flt"
        >
          <div
            class="panel-heading"
            style="padding-top: 0;padding-bottom: 0;padding-right: 0;height: 34px"
          >
            <DateFieldNav
              class="btr"
              :brn="false"
              w="190px"
              style="float: right"
              :val.sync="journal_date"
              :def="journal_date"
            />
            <span style="margin-top: 7px;display: inline-block;">Журнал регистраций</span>
          </div>
          <div
            class="panel-body"
            style="padding-top: 5px"
          >
            <div
              class="text-right"
              style="margin-bottom: 5px"
            >
              <a
                href="#"
                class="fli a-under"
                @click.prevent="show_modal"
              >создание отчёта</a>
            </div>
            <div
              v-if="journal_data.length === 0"
              class="text-center"
            >
              нет данных
            </div>
            <table
              v-else
              class="table table-bordered table-condensed dirtb visits"
              style="margin-bottom: 0;background-color: #fff"
            >
              <thead>
                <tr>
                  <th>Направление</th>
                  <th>Дата и время</th>
                  <th>Пациент</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="r in journal_data"
                  :key="r.pk"
                >
                  <td>
                    {{ r.pk }}
                    <div v-if="r.additionalNumber">
                      {{ r.additionalNumber }}
                    </div>
                  </td>
                  <td>{{ r.datetime }}</td>
                  <td>{{ r.client }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div
          v-if="can_receive"
          class="panel panel-flt"
        >
          <div
            class="panel-heading"
            style="padding-top: 0;padding-bottom: 0;padding-right: 0;height: 34px"
          >
            <DateFieldNav
              :brn="false"
              :def="journal_recv_date"
              :val.sync="journal_recv_date"
              class="btr"
              style="float: right"
              w="190px"
            />
            <span style="margin-top: 7px;display: inline-block;">Журнал приёма материала</span>
          </div>
          <div
            class="panel-body"
            style="padding-top: 5px"
          >
            <div
              v-if="journal_recv_data.length === 0"
              class="text-center"
            >
              <br>
              нет данных
            </div>
            <table
              v-else
              class="table table-bordered table-condensed dirtb visits"
              style="margin-bottom: 0;background-color: #fff"
            >
              <thead>
                <tr>
                  <th>Направление</th>
                  <th>Дата и время</th>
                  <th>Пациент</th>
                  <th>Ёмкость</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="r in journal_recv_data"
                  :key="r.pk"
                >
                  <td>{{ r.pk }}</td>
                  <td>{{ r.datetime }}</td>
                  <td>{{ r.client }}</td>
                  <td>
                    <div
                      v-for="t in r.tubes"
                      :key="`${t.title}_${t.color}`"
                    >
                      <!-- eslint-disable-next-line max-len -->
                      <span :style="`background-color: ${t.color};display: inline-block;width: 10px;height: 10px;border: 1px solid #aab2bd;`" />
                      {{ t.title }}
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
    <Modal
      v-show="showModal"
      ref="modal"
      show-footer="true"
      @close="hide_modal"
    >
      <span slot="header">Настройка отчёта</span>
      <div slot="body">
        <span>Период: </span>
        <div style="width: 186px;display: inline-block;vertical-align: middle">
          <DateRange v-model="date_range" />
        </div>
      </div>
      <div
        slot="footer"
        class="text-center"
      >
        <div class="row">
          <div class="col-xs-6">
            <button
              type="button"
              class="btn btn-primary-nb btn-blue-nb btn-ell"
              @click="report('sum')"
            >
              Суммарный отчёт
            </button>
          </div>
        </div>
      </div>
    </Modal>
    <Modal
      v-if="toEnter"
      v-show="showModalProtocol"
      ref="modalProtocol"
      white-bg="true"
      width="100%"
      margin-left-right="34px"
      margin-top="30px"
      show-footer="true"
      @close="hide_modal_protocol"
    >
      <span slot="header">Заполнить данные</span>
      <div
        slot="body"
        class="protocol-body"
      >
        <iframe
          :src="toEnterUrl"
          name="toEnter"
        />
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-12">
            <button
              class="btn btn-primary-nb btn-blue-nb"
              type="button"
              @click="hide_modal_protocol"
            >
              Закрыть
            </button>
          </div>
        </div>
      </div>
    </Modal>
  </div>
</template>

<script lang="ts">
import moment from 'moment';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import DateFieldNav from '@/fields/DateFieldNav.vue';
import DateRange from '@/ui-cards/DateRange.vue';
import directionsPoint from '@/api/directions-point';
import usersPoint from '@/api/user-point';
import * as actions from '@/store/action-types';
import Modal from '@/ui-cards/Modal.vue';

function TryParseInt(str, defaultValue): number {
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
  name: 'DirectionVisit',
  components: {
    DateFieldNav,
    Modal,
    DateRange,
    Treeselect,
  },
  data() {
    return {
      loaded_pk: -1,
      direction: '',
      in_load: false,
      showModal: false,
      showModalProtocol: false,
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
      users: [],
      laborantUsers: [],
      manualDateVisit: false,
      toEnter: null,
      currentDate: moment().format('YYYY-MM-DD'),
      currentDateInterval: null,
    };
  },
  computed: {
    toEnterUrl() {
      return `/ui/results/descriptive?embedded=1#{"pk":${this.toEnter}}`;
    },
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
    fillRequiredField() {
      if (this.direction_data.has_gistology) {
        return this.direction_data.coExecutor && this.direction_data.additionalNumber
          && this.direction_data.gistology_receive_time && this.direction_data.planedDoctorExecutor;
      }
      return true;
    },
    l2_decriptive_coexecutor() {
      return this.$store.getters.modules.l2_decriptive_coexecutor;
    },
    l2_decriptive_additional_number() {
      return this.$store.getters.modules.l2_decriptive_additional_number;
    },
    currentYear() {
      return moment(this.currentDate).format('YYYY');
    },
  },
  watch: {
    journal_date() {
      this.load_journal();
    },
    manualDateVisit() {
      if (!this.manualDateVisit) {
        this.visit_date = '';
      }
    },
    journal_recv_date() {
      this.load_recv_journal();
    },
    l2_decriptive_coexecutor: {
      immediate: true,
      async handler() {
        const [{ users }, rows] = await Promise.all([
          usersPoint.loadUsersByGroup({
            group: ['Врач параклиники', 'Врач консультаций', 'Заполнение мониторингов', 'Свидетельство о смерти-доступ'],
            position: ['лаборант'],
          }),
          usersPoint.loadUsersByGroup({
            group: ['Врач параклиники', 'Врач консультаций', 'Заполнение мониторингов', 'Свидетельство о смерти-доступ'],
            position: ['врач'],
          }),
        ]);
        this.laborantUsers = users;
        this.users = rows.users;
      },
    },
  },
  mounted() {
    this.load_journal();
    this.load_recv_journal();
    this.getCurrentTime();
    this.currentDateInterval = setInterval(() => {
      this.getCurrentTime();
    }, 60000);
  },
  beforeDestroy() {
    clearInterval(this.currentDateInterval);
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
    show_modal_protocol(pk) {
      this.toEnter = pk;
      if (this.$refs.modalProtocol) {
        this.$refs.modalProtocol.$el.style.display = 'flex';
      }
      this.showModalProtocol = true;
    },
    hide_modal_protocol() {
      this.showModalProtocol = false;
      this.toEnter = null;
      if (this.$refs.modalProtocol) {
        this.$refs.modalProtocol.$el.style.display = 'none';
      }
      this.focus();
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
      this.getCurrentTime();
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
          this.$root.$emit('msg', 'error', data.message);
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
    async clearAdditionalNumber() {
      const data = await this.$api('directions/clear-register-number', {
        additionalNumber: this.direction_data.additionalNumber,
        additionalNumberYear: this.direction_data.additionalNumberYear,
        pk: this.loaded_pk,
      });
      this.direction_data.additionalNumber = '';
      this.direction_data.additionalNumberYear = null;
      if (data.ok) {
        this.$root.$emit('msg', 'ok', data.message);
      } else {
        this.$root.$emit('msg', 'error', data.message);
      }
    },
    cancel_visit() {
      // eslint-disable-next-line no-restricted-globals,no-alert
      if (confirm('Вы уверены, что хотите отменить регистрацию?')) {
        this.make_visit(true);
      }
    },
    make_visit(cancel = false) {
      if (this.loaded_pk === -1 || this.in_load) return;
      this.$store.dispatch(actions.INC_LOADING);
      this.in_load = true;
      directionsPoint.getMarkDirectionVisit({
        pk: this.loaded_pk,
        cancel,
        coExecutor: this.direction_data.coExecutor,
        planedDoctorExecutor: this.direction_data.planedDoctorExecutor,
        additionalNumber: this.direction_data.additionalNumber,
        additionalNumberYear: this.direction_data.additionalNumberYear || this.currentYear,
        gistologyReceiveTime: this.direction_data.gistology_receive_time,
        visitDate: this.visit_date,
      }).then((data) => {
        if (data.ok) {
          this.visit_status = data.visit_status;
          this.visit_date = data.visit_date;
          this.allow_reset_confirm = data.allow_reset_confirm;
          this.focus();
        } else {
          this.$root.$emit('msg', 'error', data.message);
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
          this.$root.$emit('msg', 'error', data.message);
        }
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
        this.in_load = false;
        this.load_recv_journal();
      });
    },
    async getCurrentTime() {
      const { date } = await this.$api('current-time');
      if (date) {
        this.currentDate = date;
      }
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

  .dirtb tr td:not(.cl-td):last-child {
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

.protocol-body {
  height: calc(100vh - 179px);
  position: relative;

  iframe {
    display: block;
    width: 100%;
    height: 100%;
    border: none;
  }
}

.status-none {
  color: #cf3a24;
}

.additional-number-group {
  .form-control {
    &:first-child {
      flex: 1;
    }
    &:nth-child(2) {
      width: 58px;
    }
  }

  .input-group-btn {
    width: 42px;
    flex: 0 42px;

    .btn {
      margin-left: 0!important;
    }
  }
}
</style>
