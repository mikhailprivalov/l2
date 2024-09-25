<template>
  <Modal
    ref="modal"
    margin-top="30px"
    margin-left-right="auto"
    max-width="1500px"
    height="700px"
    show-footer="true"
    white-bg="true"
    width="100%"
    @close="hideModal"
  >
    <span slot="header">Настройка ёмкости ({{ props.editRelationId }}) </span>
    <div
      slot="body"
    >
      <iframe
        id="myframe"
        width="1470"
        height="605"
        :src="`/ui/construct/related-tube/${props.editRelationId}`"
      />
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-10" />
        <div class="col-xs-2">
          <button
            class="btn btn-primary-nb btn-blue-nb"
            type="button"
            @click="hideModal"
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script setup lang="ts">

import { ref } from 'vue';

import Modal from '@/ui-cards/Modal.vue';

const props = defineProps({
  editRelationId: {
    type: [Number, null],
    required: true,
  },
});
const emit = defineEmits(['hideModal']);
const modal = ref(null);
const hideModal = () => {
  emit('hideModal');
  if (modal.value) {
    modal.value.$el.style.display = 'none';
  }
};
</script>
