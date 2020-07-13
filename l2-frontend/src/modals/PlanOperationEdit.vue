<template>
  <modal ref="modal" @close="hide_plan_operations" show-footer="true" white-bg="true" max-width="680px" width="100%"
         marginLeftRight="auto" margin-top>
    <span slot="header">Планирование операции</span>
    <div slot="body" style="min-height: 200px" class="registry-body">
      <plan-operations-data :card_pk="card_pk" :patient_fio="patient_fio"  :direction="direction"/>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-5" style="float: right">
          <button @click="hide_plan_operations" class="btn btn-primary-nb btn-blue-nb" type="button">
            Выйти
          </button>
        </div>
      </div>
    </div>
  </modal>
</template>

<script>
  import Modal from '../ui-cards/Modal'
  import * as action_types from '../store/action-types'
  import moment from 'moment'
  import PlanOperationsData from '../components/PlanOperationsData'
  import SelectHospitalDirections from '../components/SelectHospitalDirections'

  export default {
    name: 'plan-operation-edit',
    components: {SelectHospitalDirections, Modal, PlanOperationsData},
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
        cards: [],
      }
    },
    mounted() {
      console.log('modal', this.patient_fio)
      console.log('modal-1',this.card_pk)
      console.log('modal-1',this.direction)
    },
    methods: {
      hide_plan_operations() {
        this.$root.$emit('hide_plan_operations')
        if (this.$refs.modal) {
          this.$refs.modal.$el.style.display = 'none'
        }
      }
    },
    load_stationar_research() {
      return ''
    }
  }
</script>

<style scoped lang="scss">
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

</style>
