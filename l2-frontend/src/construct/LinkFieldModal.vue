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
          <tr
            v-for="research in researches"
            :key="research.pk"
          >
            <td>
              <input
                v-model="research.title"
                class="form-control nbr"
              >
            </td>
            <td>
              <div class="flex">
                <div
                  v-for="test in research.tests"
                  :key="test.pk"
                  class="flex"
                >
                  <input
                    :id="test.pk"
                    type="checkbox"
                  >
                  <label :for="test.pk">{{ test.title }}</label>
                </div>
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
          @click="addResearches"
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
import { ref } from 'vue';

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

const researches = ref([]);
const addResearches = () => {
  const newResearch = { pk: 1, title: 'Услуга 1', tests: [{ pk: 1, title: 'тест 1' }] };
  researches.value.push(newResearch);
};

</script>

<style scoped lang="scss">
.scroll {
  max-height: 400px;
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
