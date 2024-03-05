<template>
  <Modal
    ref="modal"
    show-footer="true"
    white-bg="true"
    max-width="600px"
    width="100%"
    height="20%"
    margin-left-right="auto"
    margin-top
    class="an"
    @close="hide"
  >
    <span slot="header">Расписание</span>
    <div
      slot="body"
      class="modal-body"
    >
      <ServiceScheduleEcp
        :card-id="props.cardPk"
        :service-pk="props.serviceNumber"
      />
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-8" />
        <div class="col-xs-4">
          <button
            class="btn btn-primary-nb btn-blue-nb"
            type="button"
            @click="hide"
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script setup lang="ts">

import Modal from '@/ui-cards/Modal.vue';
import ServiceScheduleEcp from '@/ui-cards/ServiceScheduleEcp.vue';

const props = defineProps({
  cardPk: {
    type: Number,
    required: true,
  },
  serviceNumber: {
    type: Number,
    required: true,
  },
});

const emit = defineEmits(['hide']);

const hide = () => {
  emit('hide');
};

</script>

<style scoped lang="scss">

</style>
