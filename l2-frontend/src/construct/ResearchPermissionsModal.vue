<template>
  <Modal
    ref="modal"
    show-footer="true"
    white-bg="true"
    min-width="95%"
    margin-top
    @close="hide"
  >
    <span slot="header">Настройка шаблонов быстрого ввода ({{ title }})</span>
    <div
      slot="body"
      style="min-height: 200px"
      class="directions-manage"
    />
    <div slot="footer">
      <div class="row">
        <div class="col-xs-8" />
        <div class="col-xs-4">
          <button
            type="button"
            class="btn btn-primary-nb btn-blue-nb"
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

const emit = defineEmits(['hide']);
const props = defineProps({
  researchId: {
    type: Number,
    required: true,
  },
});

const hide = () => {
  emit('hide');
};
</script>

<style scoped lang="scss">

</style>
