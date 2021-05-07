<template>
  <div>
    <div class="form-row">
      <div class="row-t">
        Пациент (карта)
        <a @click.prevent="open_patient_picker" :class="{unvisible: patient_fio}" href="#"
           style="float: right; padding-right: 5px; color: #ffffff;">Найти</a>
      </div>
      <div class="row-v">
        <input class="form-control" v-model="patient_data" readonly>
      </div>
    </div>
    <div class="form-row">
      <div class="row-t">№ Истории</div>
      <input class="form-control" v-model="current_direction" readonly>
    </div>
    <div class="form-row">
      <div class="row-t">Дата операции</div>
      <input class="form-control" type="date" :min="timeValue" v-model="current_time">
    </div>
    <div class="form-row">
      <div class="row-t">Врач-хирург</div>
      <div class="row-v">
        <treeselect class="treeselect-noborder" :multiple="false" :disable-branch-nodes="true" :options="hirurgs"
                    placeholder="Хирург не выбран" v-model="current_hirurg"
        />
      </div>
    </div>
    <div class="form-row">
      <div class="row-t">Вид операции</div>
      <div class="row-v">
        <input class="form-control" v-model="type_operation">
      </div>
    </div>

    <div class="buttons">
      <div class="cancel-message" v-if="cancel_operation">Операция отменена</div>

      <button class="btn btn-blue-nb btn-sm" @click="save_to_plan"
              :class="[{btndisable: !current_hirurg || !current_direction || !card_pk || !current_time}]">
        {{pk_plan && pk_plan > -1 ? 'Сохранить изменения' : 'Добавить новую запись в план' }}
      </button>

      <button class="btn btn-blue-nb btn-sm" @click="cancel_from_plan" v-if="pk_plan && pk_plan > -1">
        {{cancel_operation ? 'Убрать отмену' : 'Отменить операцию' }}
      </button>
    </div>
    <modal v-if="patient_to_edit" ref="modalPatientEdit" @close="hide_modal_patient_edit" show-footer="true"
           white-bg="true"
           max-width="710px" width="100%" marginLeftRight="auto" margin-top>
      <span slot="header">Поиск пациента</span>
      <div slot="body" style="min-height: 140px" class="registry-body">
        <div style="height: 110px">
          <patient-small-picker v-model="card_pk" :base_pk="base_pk"/>
        </div>
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-4">
            <button @click="hide_modal_patient_edit" class="btn btn-primary-nb btn-blue-nb" type="button">
              Подтвердить
            </button>
          </div>
        </div>
      </div>
    </modal>
  </div>
</template>

<script>
import moment from 'moment';
import Treeselect from '@riophae/vue-treeselect';
import Modal from '../ui-cards/Modal.vue';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import * as actions from '../store/action-types';
import usersPoint from '../api/user-point';
import PatientSmallPicker from '../ui-cards/PatientSmallPicker.vue';
import patientsPoint from '../api/patients-point';
import plansPoint from '../api/plans-point';

export default {
  name: 'PlanOperationsData',
  components: { Treeselect, PatientSmallPicker, Modal },
  props: {
    card_pk_initial: {
      type: Number,
      required: false,
    },
    patient_fio: {
      type: String,
      required: false,
    },
    direction: {
      type: String,
      required: false,
    },
    pk_plan: {
      type: Number,
      required: false,
    },
    pk_hirurg: {
      type: Number,
      required: false,
    },
    date: {
      type: String,
      required: false,
    },
    operation: {
      type: String,
      required: false,
    },
    cancel_operation: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      cart_pk: this.card_pk_initial,
      hirurgs: [],
      patient_to_edit: false,
      patient_data: '',
      current_direction: '',
      timeValue: moment().format('YYYY-MM-DD'),
      current_hirurg: this.pk_hirurg,
      current_time: this.date,
      type_operation: this.operation,
      base_pk: -1,
    };
  },
  watch: {
    card_pk_initial: {
      handler() {
        this.card_pk = this.card_pk_initial;
        if (this.patient_fio && this.card_pk) {
          this.patient_data = this.patient_fio;
        }
      },
      immediate: true,
    },
  },
  created() {
    this.$store.watch((state) => state.bases, () => {
      this.check_base();
    });
    this.check_base();
    this.load_hirurgs();
    if (this.patient_fio && this.card_pk) {
      this.patient_data = this.patient_fio;
    }
    this.current_direction = this.direction;
  },
  computed: {
    bases() {
      return this.$store.getters.bases.filter((b) => !b.hide);
    },
  },
  methods: {
    check_base() {
      if (this.base_pk === -1 && this.bases.length > 0) {
        for (const row of this.bases) {
          if (row.internal_type) {
            this.base_pk = row.pk;
            break;
          }
        }
      }
    },
    async load_hirurgs() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { users } = await usersPoint.loadUsersByGroup({ group: ['Оперирует'] });
      this.hirurgs = users;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    open_patient_picker() {
      this.patient_to_edit = true;
    },
    hide_modal_patient_edit() {
      if (this.$refs.modalPatientEdit) {
        this.load_patient();
        this.$refs.modalPatientEdit.$el.style.display = 'none';
        this.patient_to_edit = false;
      }
    },
    async load_patient() {
      if (!this.card_pk) {
        this.patient_data = '';
      } else {
        const l2Card = await patientsPoint.searchL2Card({ card_pk: this.card_pk });
        this.patient_data = [
          l2Card.results[0].family,
          l2Card.results[0].name,
          l2Card.results[0].twoname,
          `(${l2Card.results[0].num})`,
        ].join(' ');
      }
    },
    async save_to_plan() {
      await this.$store.dispatch(actions.INC_LOADING);
      await plansPoint.planOperationsSave({
        pk_plan: this.pk_plan,
        card_pk: this.card_pk,
        direction: this.current_direction,
        hirurg: this.current_hirurg,
        date: this.current_time,
        type_operation: this.type_operation,
      });
      await this.$store.dispatch(actions.DEC_LOADING);
      window.okmessage('Сохранено');
      this.$root.$emit('hide_plan_operations');
      this.$root.$emit('reload-plans');
    },
    async cancel_from_plan() {
      await this.$store.dispatch(actions.INC_LOADING);

      const data = await plansPoint.planOperationsCancel({
        pk_plan: this.pk_plan,
      });

      await this.$store.dispatch(actions.DEC_LOADING);

      if (data.result) {
        window.okmessage('Операция отменена');
      } else {
        window.okmessage('Отмена убрана');
      }

      this.$root.$emit('reload-plans');
    },
  },
};
</script>

<style scoped lang="scss">
  .btndisable {
    cursor: not-allowed;
    pointer-events: none;

    color: #c0c0c0;
    background-color: #ffffff;
  }

  .unvisible {
    visibility: hidden;
  }

  .color-bottom {
    border-bottom: 1px solid #434a54;
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
      width: 60%;
      flex: 0 65%;
      height: 36px;
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
      padding: 0 0 0 0;
    }

    ::v-deep .input-group {
      border-radius: 0;
    }
  }

  .buttons {
    padding: 10px;
    text-align: center;
  }

  .cancel-message {
    font-size: 16px;
    font-weight: bold;
    color: #f00;
    margin: 10px;
  }
</style>
