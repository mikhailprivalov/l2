<template>
  <div v-frag>
    <button class="btn btn-blue-nb btn-block btn-sm" type="button" tabindex="-1" @click="openSchedule = true">
      Записать
    </button>
    <MountingPortal mountTo="#portal-place-modal" :name="`PlanSchedule_${data.pk_plan}`" append>
      <transition name="fade">
        <Modal
          @close="openSchedule = false"
          white-bg="true"
          max-width="710px"
          width="100%"
          marginLeftRight="auto"
          :zIndex="5001"
          v-if="openSchedule"
          show-footer="true"
        >
          <span slot="header">{{ data.date }} {{ data.fio_patient }} — запись на время</span>
          <div slot="body" class="popup-body">
            Заявка: {{ data.date }} {{ data.fio_patient }}<br />
            Телефон: {{ data.phone }}<br />
            Диагноз: {{ data.diagnos }}<br />
            Примечания: {{ data.comment }}
            <hr />
            <ServiceSchedule
              v-model="selectedSlot"
              :service-pk="data.research_id"
              :service-title="data.research_title"
              :initial-date="data.date"
              :slot-date.sync="slotDate"
              :slot-resource.sync="slotResource"
            />
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-6">
                <button type="button" @click="openSchedule = false" class="btn btn-primary-nb btn-blue-nb">Закрыть</button>
              </div>
              <div class="col-xs-6 text-right">
                <button type="button" @click="linkPlanSlot" class="btn btn-primary-nb btn-blue-nb" :disabled="!selectedSlot">
                  Записать на время
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
import ServiceSchedule from '@/ui-cards/ServiceSchedule.vue';
import * as actions from '@/store/action-types';

export default {
  name: 'HospPlanScheduleButton',
  components: { Modal, ServiceSchedule },
  props: {
    data: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      openSchedule: false,
      selectedSlot: null,
      slotDate: null,
      slotResource: null,
    };
  },
  methods: {
    async linkPlanSlot() {
      await this.$store.dispatch(actions.INC_LOADING);
      await this.$api('schedule/save', {
        id: this.selectedSlot,
        planId: this.data.pk_plan,
        serviceId: this.data.research_id,
        cardId: this.data.patient_card,
        date: this.slotDate,
        resource: this.slotResource,
      });
      this.openSchedule = false;
      this.selectedSlot = null;
      this.$root.$emit('reload-hospplans');
      this.$root.$emit('reload-list-wait-data');
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
};
</script>

<style scoped lang="scss">
.btn-block {
  white-space: normal;
}
</style>
