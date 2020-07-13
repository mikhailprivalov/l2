<template>
    <div>
      <div class="form-row">
        <div class="row-t">Пациент (карта)
          <a @click.prevent="open_patient_picker" href="#" style="float: right; padding-right: 5px; color: #ffffff">Найти</a>
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
          <input class="form-control" type="date">
      </div>
      <div class="form-row">
        <div class="row-t">Врач-хирург</div>
        <div class="row-v">
          <treeselect class="vue-treeselect__control_my"
            :multiple="false"
            :options="hirurgs"
            placeholder="Select "
          />
        </div>
      </div>
      <div class="form-row">
        <div class="row-t">Вид операции</div>
        <div class="row-v">
          <input class="form-control">
        </div>
      </div>
      <div class="row color-bottom">
        <div style="float: right; margin-right: 10px; padding-right: 10px" >
          <button class="btn btn-blue-nb btn-sm" style="border-radius: 0px">
            Сохранить в план
          </button>
          <button class="btn btn-blue-nb btn-sm" style="border-radius: 0px">
            Отменить
          </button>
          </div>
      </div>
      <modal v-if="patient_to_edit" ref="modalPatientEdit" @close="hide_modal_patient_edit" show-footer="true" white-bg="true"
             max-width="710px" width="100%" marginLeftRight="auto" margin-top>
        <span slot="header">Поиск пациента</span>
        <div slot="body" style="min-height: 140px" class="registry-body">
          <div style="height: 110px">
            <patient-small-picker v-model="patient_card_selected" :base_pk="5"/>
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
        type: Number,
        required: false
      }
    },
    data() {
      return {
        hirurgs: [],
        patient_to_edit: false,
        patient_card_selected: null,
        patient_data: '',
        current_direction:''
      }
    },
    created() {
      this.load_hirurgs();
      this.patient_card_selected = this.card_pk;
      this.load_patient()
      this.current_direction = this.direction
    },
    watch: {

    },
    methods: {
      async load_hirurgs() {
        await this.$store.dispatch(action_types.INC_LOADING)
        const {hirurgs} = await users_point.loadHirurgs()
        this.hirurgs = hirurgs
        await this.$store.dispatch(action_types.DEC_LOADING)
      },
      open_patient_picker() {
        this.patient_card_selected = null
        this.patient_to_edit = true
      },
      hide_modal_patient_edit() {
        if (this.$refs.modalPatientEdit) {
          this.load_patient()
          this.$refs.modalPatientEdit.$el.style.display = 'none';
          this.patient_to_edit = false
        }
      },
      async load_patient() {
          if (!this.patient_card_selected) {
            this.patient_data = ''
          }
          else {
            const l2Card = await patients_point.searchL2Card({'card_pk': this.patient_card_selected})
            console.log(l2Card)
            console.log(l2Card.results[0].name)
            this.patient_data = l2Card.results[0].family + ' ' + l2Card.results[0].name + ' ' + l2Card.results[0].twoname + ' (' + l2Card.results[0].num + ')'
          }
      },
    }
  }
</script>

<style scoped lang="scss">
  .color-bottom {
    border-bottom: 1px solid #434a54;
  }

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


  .str /deep/ .input-group {
    width: 100%;
  }

  .lst {
    margin: 0;
    line-height: 1;
  }

  .c-pointer {
    &, & strong, &:hover {
      cursor: pointer!important;
    }
  }
  .vue-treeselect__control_my /deep/ .vue-treeselect__control{
    border: 0px solid #ddd;
    border-radius: 0px;
  }
</style>

