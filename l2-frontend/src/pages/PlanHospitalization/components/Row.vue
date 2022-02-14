<template>
  <tr :class="{ 'cancel-row': data.canceled, 'approved-row': data.status === 3 }">
    <td v-tippy="vtp" :title="data.tooltip_data">
      {{ data.date }}
    </td>
    <td v-tippy="vtp" :title="data.tooltip_data">
      {{ data.fio_patient }}<br />
      {{ data.phone }}
    </td>
    <td v-tippy="vtp" :title="data.tooltip_data">
      <div>{{ data.research_title }}</div>
      <div v-if="data.depart_title">— {{ data.depart_title }}</div>
    </td>
    <td v-tippy="vtp" :title="data.tooltip_data">
      {{ data.diagnos }}
    </td>
    <td v-tippy="vtp" :title="data.tooltip_data" class="td-comment">{{ data.comment }}</td>
    <td>
      <template v-if="!data.canceled && data.status !== 3">
        <button class="btn btn-blue-nb btn-block btn-sm" type="button" tabindex="-1" @click="openSchedule = true">
          Записать на время
        </button>
        <button class="btn btn-blue-nb btn-block btn-sm" type="button" tabindex="-1" @click="cancelModal = true">Отмена</button>
      </template>
      <template v-else-if="data.slot"> Запись:<br />{{ data.slot }} </template>
    </td>
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
  </tr>
</template>

<script lang="ts">
import Modal from '@/ui-cards/Modal.vue';
import ServiceSchedule from '@/ui-cards/ServiceSchedule.vue';
import * as actions from '@/store/action-types';
import plansPoint from '@/api/plans-point';

export default {
  name: 'Row',
  components: { Modal, ServiceSchedule },
  props: {
    data: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      vtp: {
        placement: 'top',
        arrow: true,
        interactive: true,
        theme: 'dark longread',
      },
      cancelModal: false,
      cancelReason: '',
      openSchedule: false,
      selectedSlot: null,
      slotDate: null,
      slotResource: null,
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
      await this.$store.dispatch(actions.DEC_LOADING);
    },
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
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
};
</script>

<style scoped lang="scss">
.cancel-row {
  td,
  th {
    opacity: 0.6;
    text-decoration: line-through;
    background-color: linen;
  }

  &:hover {
    td,
    th {
      opacity: 1;
      text-decoration: none;
    }
  }
}

.approved-row {
  td,
  th {
    background-color: rgb(232, 250, 230);
  }
}

.td-comment {
  white-space: pre-wrap;
}
</style>
