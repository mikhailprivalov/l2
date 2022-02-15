<template>
  <div v-frag>
    <button class="btn btn-blue-nb btn-block btn-sm" type="button" tabindex="-1" @click="cancelModal = true">Отмена</button>
    <MountingPortal mountTo="#portal-place-modal" :name="`PlanCancel_${data.pk_plan}`" append>
      <transition name="fade">
        <Modal
          @close="cancelModal = false"
          white-bg="true"
          max-width="710px"
          width="100%"
          marginLeftRight="auto"
          :zIndex="5001"
          v-if="cancelModal"
          show-footer="true"
        >
          <span slot="header">{{ data.date }} {{ data.fio_patient }} — отмена</span>
          <div slot="body" class="popup-body">
            <input class="form-control" placeholder="Причина отмены" autofocus v-model="cancelReason" type="text" />
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-6">
                <button type="button" @click="cancelModal = false" class="btn btn-primary-nb btn-blue-nb">Закрыть</button>
              </div>
              <div class="col-xs-6 text-right">
                <button
                  type="button"
                  @click="cancel_plan_hospitalization"
                  class="btn btn-primary-nb btn-blue-nb"
                  :disabled="!cancelReason"
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
