<template>
  <Modal
    ref="modal"
    show-footer="true"
    white-bg="true"
    min-width="95%"
    @close="closeModal"
  >
    <span slot="header">Создание ссылочных строк</span>
    <div
      slot="body"
      class="body"
    >
      <LinkLabAdd
        :field-value="props.fieldValue"
        :field-id="props.fieldId"
        @add-link="addLink"
      />
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-8" />
        <div class="col-xs-4">
          <button
            type="button"
            class="btn btn-primary-nb btn-blue-nb"
            @click="closeModal"
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
import LinkLabAdd from '@/construct/LinkLabAdd.vue';

const emit = defineEmits(['close-modal', 'add-link']);
const props = defineProps({
  fieldId: {
    required: true,
    type: Number,
  },
  fieldValue: {
    required: true,
    type: String,
  },
});

const closeModal = () => {
  emit('close-modal');
};

const addLink = () => {
  emit('add-link');
};
</script>

<style scoped lang="scss">
.body {
  height: 100%;
  width: 100%;
}
</style>
