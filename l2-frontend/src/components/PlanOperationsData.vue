<template>
    <div>
      <div class="form-row">
        <div class="row-t">Пациент (карта)
          <a @click.prevent="open_patient_picker" :class="{unvisible: patient_fio}" href="#" style="float: right; padding-right: 5px; color: #ffffff;">Найти</a>
        </div>
        <div class="row-v">
          <input class="form-control" v-model="patient_data" readonly>
        </div>
      </div>
      <div class="form-row">
        <div class="row-t">№ Истории</div>
        <input class="form-control" v-model="current_direction">
      </div>
      <div class="form-row">
        <div class="row-t">Дата операции</div>
          <input class="form-control" type="date" :min="timeValue" v-model="current_time">
      </div>
      <div class="form-row">
        <div class="row-t">Врач-хирург</div>
        <div class="row-v">
          <treeselect class="vue-treeselect__control_my" :multiple="false" :options="hirurgs" placeholder="Select"
                      v-model="current_hirurg"
          />
        </div>
      </div>
      <div class="form-row">
        <div class="row-t">Вид операции</div>
        <div class="row-v">
          <input class="form-control" v-model="type_operation">
        </div>
      </div>
      <div class="row color-bottom">
        <div style="float: right; margin-right: 10px; padding-right: 10px" >
          <button class="btn btn-blue-nb btn-sm" style="border-radius: 0px" @click="save_to_plan"
                  :class="[{btndisable: !current_hirurg || !current_direction || !card_pk || !current_time}]">
            Сохранить в план
          </button>
          <button class="btn btn-blue-nb btn-sm" style="border-radius: 0px">
            Отменить операцию
          </button>
          </div>
      </div>
      <modal v-if="patient_to_edit" ref="modalPatientEdit" @close="hide_modal_patient_edit" show-footer="true" white-bg="true"
             max-width="710px" width="100%" marginLeftRight="auto" margin-top>
        <span slot="header">Поиск пациента</span>
        <div slot="body" style="min-height: 140px" class="registry-body">
          <div style="height: 110px">
            <patient-small-picker v-model="card_pk" :base_pk="5"/>
          </div>
        </div>
        <div slot="footer">
          <div class="row">
            <div class="col-xs-4">
              <button @click="hide_modal_patient_edit" class="btn btn-primary-nb btn-blue-nb" type="button">
                ОК
              </button>
            </div>
          </div>
        </div>
      </modal>

    </div>

</template>

<script>
  import Modal from '../ui-cards/Modal'
  import Treeselect from '@riophae/vue-treeselect'
  import '@riophae/vue-treeselect/dist/vue-treeselect.css'
  import * as action_types from "../store/action-types";
  import users_point from '../api/user-point'
  import PatientSmallPicker from '../ui-cards/PatientSmallPicker'
  import patients_point from "../api/patients-point";
  import directions_point from '../api/directions-point'
  import moment from "moment";
  import plans_point from "../api/plans-point";

  export default {
    name: "PlanOperationsData",
    components: {Treeselect, PatientSmallPicker, Modal},
     props: {
      card_pk: {
        type: Number,
        required: false
      },
      base_pk: {
        type: Number,
        required: false
      },
      patient_fio: {
        type: String,
        required: false
      },
      direction: {
        type: String,
        required: false
      },
       pk_plan: {
         type: Number,
         required: false
       },
    },
    data() {
      return {
        hirurgs: [],
        patient_to_edit: false,
        patient_data: '',
        current_direction: '',
        timeValue: moment().format('YYYY-MM-DD'),
        current_hirurg: null,
        current_time: '',
        type_operation: '',
      }
    },
    created() {
      this.load_hirurgs();
      if (this.patient_fio && this.card_pk) {
        this.patient_data = this.patient_fio
      }
      this.current_direction = this.direction;
    },
    methods: {
      async load_hirurgs() {
        await this.$store.dispatch(action_types.INC_LOADING)
        const {hirurgs} = await users_point.loadHirurgs()
        this.hirurgs = hirurgs
        await this.$store.dispatch(action_types.DEC_LOADING)
      },
      open_patient_picker() {
        this.patient_to_edit = true
      },
      hide_modal_patient_edit() {
        if (this.$refs.modalPatientEdit) {
          this.card_pk =
          this.load_patient()
          this.$refs.modalPatientEdit.$el.style.display = 'none';
          this.patient_to_edit = false
        }
      },
      async load_patient() {
          if (!this.card_pk) {
            this.patient_data = ''
          }
          else {
            const l2Card = await patients_point.searchL2Card({'card_pk': this.card_pk})
            this.patient_data = l2Card.results[0].family + ' ' + l2Card.results[0].name + ' ' + l2Card.results[0].twoname + ' (' + l2Card.results[0].num + ')'
          }
      },
      async save_to_plan(){
        await this.$store.dispatch(action_types.INC_LOADING)
        await plans_point.planOperationsSave({
          'pk_plan': this.pk_plan,
          'card_pk': this.card_pk,
          'direction': this.current_direction,
          'hirurg': this.current_hirurg,
          'date': this.current_time,
          'type_operation': this.type_operation,
        })
        this.current_hirurg = null;
        this.current_time = '';
        this.type_operation = '';
        await this.$store.dispatch(action_types.DEC_LOADING)
        okmessage('Сохранено');
      },
    }
  }
</script>

<style scoped lang="scss">
   .btndisable {
     cursor: not-allowed;
     pointer-events: none;

     /*Button disabled - CSS color class*/
     color: #c0c0c0;
     background-color: #ffffff;
   }

  .unvisible{
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

    input, .row-v, /deep/ input {
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

      input, .row-v, /deep/ input {
        height: 26px;
      }
    }

    /deep/ input {
      width: 100% !important;
    }

    .row-v {
      padding: 0px 0 0 0px;
    }

    /deep/ .input-group {
      border-radius: 0;
    }
  }

  .vue-treeselect__control_my /deep/ .vue-treeselect__control{
    border: 0px solid #ddd;
    border-radius: 0px;
  }
</style>

