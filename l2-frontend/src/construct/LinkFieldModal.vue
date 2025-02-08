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
    >
      <div class="scroll">
        <table class="table no-margin-bottom">
          <colgroup>
            <col>
            <col>
          </colgroup>
          <thead class="sticky">
            <tr class="border-no-top">
              <th class="text-center border-right">
                <strong>Услуга</strong>
              </th>
              <th class="text-center border-right">
                <strong>Тесты</strong>
              </th>
            </tr>
          </thead>
          <tr>
            <td>
              <input class="form-control nbr">
            </td>
            <td>
              <div class="flex">
                <input
                  id="test1"
                  type="checkbox"
                >
                <label for="test1">тест1</label>
                <input
                  id="test2"
                  type="checkbox"
                >
                <label for="test2">тест2</label>
                <input
                  id="test3"
                  type="checkbox"
                >
                <label for="test3">тест3</label>
              </div>
            </td>
          </tr>
        </table>
      </div>
      <div class="button">
        <button
          v-tippy
          class="btn last btn-blue-nb nbr"
          title="Добавить услугу"
        >
          <i class="fa fa-save" />
        </button>
      </div>
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

const emit = defineEmits(['close-modal']);
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
</script>

<style scoped lang="scss">
.scroll {
  max-height: calc(100vh - 463px);
  overflow-y: auto;
}
.sticky {
  position: sticky;
  top: 0;
  z-index: 1;
  background-color: white;
}
.no-margin-bottom {
  margin-bottom: 0;
}
</style>
