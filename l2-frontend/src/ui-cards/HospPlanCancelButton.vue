<template>
  <div v-frag>
    <button
      class="btn btn-blue-nb btn-block btn-sm"
      type="button"
      tabindex="-1"
      @click="cancelModal = true"
    >
      Отмена
    </button>
    <MountingPortal
      mount-to="#portal-place-modal"
      :name="`PlanCancel_${data.pk_plan}`"
      append
    >
      <transition name="fade">
        <Modal
          v-if="cancelModal"
          white-bg="true"
          max-width="710px"
          width="100%"
          margin-left-right="auto"
          :z-index="5001"
          show-footer="true"
          @close="cancelModal = false"
        >
          <span slot="header">{{ data.date }} {{ data.fio_patient }} — отмена</span>
          <div
            slot="body"
            class="popup-body"
          >
            <input
              v-model="cancelReason"
              class="form-control"
              placeholder="Причина отмены"
              autofocus
              type="text"
            >
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-6">
                <button
                  type="button"
                  class="btn btn-primary-nb btn-blue-nb"
                  @click="cancelModal = false"
                >
                  Закрыть
                </button>
              </div>
              <div class="col-xs-6 text-right">
                <button
                  type="button"
                  class="btn btn-primary-nb btn-blue-nb"
                  :disabled="!cancelReason"
                  @click="cancel_plan_hospitalization"
                >
                  Подтвердить отмену
                </button>
              </div>
            </div>
          </div>
        </Modal>
      </transition>
    </MountingPortal>
  </div>
</template>

<script lang="ts">
import Modal from '@/ui-cards/Modal.vue';
import * as actions from '@/store/action-types';
import plansPoint from '@/api/plans-point';

export default {
  name: 'HospPlanCancelButton',
  components: { Modal },
  props: {
    data: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      cancelModal: false,
      cancelReason: '',
    };
  },
  methods: {
    async cancel_plan_hospitalization() {
      await this.$store.dispatch(actions.INC_LOADING);
      await plansPoint.cancelPlansHospitalization(this, ['cancelReason'], {
        pk_plan: this.data.pk_plan,
        status: 2,
        action: 'cancel',
      });
      this.cancelModal = false;
      this.$root.$emit('reload-hospplans');
      this.$root.$emit('reload-list-wait-data');
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
};
</script>
