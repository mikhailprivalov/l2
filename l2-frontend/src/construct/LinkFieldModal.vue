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
        <table class="table">
          <colgroup>
            <col style="width: 535px">
            <col>
            <col style="width: 35px">
          </colgroup>
          <thead class="sticky">
            <tr class="border-no-top">
              <th class="text-center border-right">
                <strong>Услуга</strong>
              </th>
              <th class="text-center border-right">
                <strong>Тесты</strong>
              </th>
              <th />
            </tr>
          </thead>
          <tr
            v-for="research in addedResearches"
            :key="research.id"
          >
            <td class="border">
              <VueTippyTd :text="research.label" />
            </td>
            <td class="border">
              <div class="flex">
                <div
                  v-for="test in research.tests"
                  :key="test.id"
                  class="flex"
                >
                  <input
                    :id="test.id"
                    type="checkbox"
                  >
                  <label :for="test.id">{{ test.label }}</label>
                </div>
              </div>
            </td>
            <td class="border">
              <div class="button">
                <button
                  v-tippy
                  class="btn last btn-blue-nb nbr"
                  title="Удалить услугу"
                >
                  <i class="fa fa-times" />
                </button>
              </div>
            </td>
          </tr>
          <tr>
            <td class="border">
              <Treeselect
                v-model="selectedResearch"
                value-format="object"
                :options="researches"
                :clearable="false"
                class="treeselect-noborder"
                placeholder="Выберите услугу"
              />
            </td>
            <td class="border">
              <div class="flex">
                <div
                  v-for="test in selectedResearch.tests"
                  :key="test.id"
                  class="flex"
                >
                  <input
                    :id="test.id"
                    type="checkbox"
                  >
                  <label :for="test.id">{{ test.label }}</label>
                </div>
              </div>
            </td>
            <td class="border">
              <div class="button">
                <button
                  v-tippy
                  class="btn last btn-blue-nb nbr"
                  title="Добавить услугу"
                  @click="addResearches"
                >
                  <i class="fa fa-plus" />
                </button>
              </div>
            </td>
          </tr>
        </table>
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
import Treeselect from '@riophae/vue-treeselect';

import Modal from '@/ui-cards/Modal.vue';
import VueTippyTd from '@/construct/VueTippyTd.vue';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

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

const addedResearches = ref([]);

const researches = ref([
  { id: 1, label: 'Услуга 1', tests: [{ id: 1, label: 'тест 1' }, { id: 2, label: 'тест 2' }] },
  { id: 2, label: 'Услуга 2', tests: [{ id: 3, label: 'тест 1' }, { id: 4, label: 'тест 2' }] },
]);
const selectedResearch = ref({ id: -1, label: 'НЕ ВЫБРАНО', tests: [] });
const addResearches = () => {
  if (selectedResearch.value.id !== -1) {
    addedResearches.value.push(selectedResearch.value);
  }
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
.add-research {
  width: 500px;
}
.flex {
  display: flex;
}
.table {
  margin-bottom: 0;
  table-layout: fixed;
}
.border {
  border: 1px solid grey;
}
</style>
