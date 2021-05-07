<template>
  <modal ref="modal" @close="hide_plan_operations" show-footer="true" white-bg="true" max-width="680px" width="100%"
         marginLeftRight="auto" margin-top>
    <span slot="header">Планирование операции</span>
    <div slot="body" style="min-height: 200px" class="registry-body">
      <plan-operations-data :card_pk_initial="card_pk" :patient_fio="patient_fio" :direction="direction" :pk_plan="pk_plan"
                            :pk_hirurg="pk_hirurg" :date="date" :operation="operation" :cancel_operation="cancel_operation"/>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-5" style="float: right">
          <button @click="hide_plan_operations" class="btn btn-primary-nb btn-blue-nb" type="button">
            Отмена
          </button>
        </div>
      </div>
    </div>
  </modal>
</template>

<script>
import Modal from '../ui-cards/Modal.vue';
import PlanOperationsData from '../components/PlanOperationsData.vue';

export default {
  name: 'plan-operation-edit',
  components: { Modal, PlanOperationsData },
  props: {
    card_pk: {
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
      required: false,
    },
  },
  data() {
    return {
      cards: [],
    };
  },
  mounted() {
    this.$root.$on('hide_plan_operations', () => {
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
    });
  },
  methods: {
    hide_plan_operations() {
      this.$root.$emit('hide_plan_operations');
    },
  },
};
</script>

<style scoped lang="scss">
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
