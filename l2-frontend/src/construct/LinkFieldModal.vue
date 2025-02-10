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
      <div class="scroll">
        <table class="table">
          <colgroup>
            <col class="research-col">
            <col>
            <col class="button-col">
          </colgroup>
          <thead class="sticky">
            <tr>
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
            v-for="(research, resIdx) in addedResearches"
            :key="research.id"
          >
            <td class="border">
              <VueTippyTd
                class="research-padding"
                :text="research.label"
              />
            </td>
            <td class="border">
              <div class="flex">
                <div
                  v-for="(addedTest, testIdx) in research.tests"
                  :key="addedTest.id"
                  class="flex"
                >
                  <input
                    :id="`${resIdx}-${testIdx}-${addedTest.id}`"
                    v-model="research.activeTest"
                    :value="addedTest.id"
                    type="checkbox"
                    class="checkbox"
                  >
                  <label :for="`${resIdx}-${testIdx}-${addedTest.id}`"> {{ addedTest.label }} </label>
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
        </table>
      </div>
      <div class="add-block">
        <table class="table">
          <colgroup>
            <col class="research-col">
            <col>
            <col class="button-col">
          </colgroup>
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
                  v-for="selectedTest in selectedResearch.tests"
                  :key="selectedTest.id"
                  class="flex"
                >
                  <input
                    :id="selectedTest.id"
                    v-model="selectedResearch.activeTest"
                    :value="selectedTest.id"
                    type="checkbox"
                    class="checkbox"
                  >
                  <label :for="selectedTest.id"> {{ selectedTest.label }} </label>
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
import { getCurrentInstance, ref } from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import Modal from '@/ui-cards/Modal.vue';
import VueTippyTd from '@/construct/VueTippyTd.vue';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

const root = getCurrentInstance().proxy.$root;
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
  {
    id: 1, label: 'Услуга 1', tests: [{ id: 1, label: 'тест 1' }, { id: 2, label: 'тест 2' }], activeTest: [],
  },
  {
    id: 2, label: 'Услуга 2', tests: [{ id: 3, label: 'тест 1' }, { id: 4, label: 'тест 2' }], activeTest: [],
  },
]);
const selectedResearch = ref({
  id: -1, label: 'НЕ ВЫБРАНО', tests: [], activeTest: [],
});
const checkUnique = (searchId) => addedResearches.value.find(research => research.id === searchId);
const addResearches = () => {
  if (selectedResearch.value.id !== -1) {
    const unique = checkUnique(selectedResearch.value.id);
    if (unique) {
      addedResearches.value.push({ ...selectedResearch.value });
      selectedResearch.value = {
        id: -1, label: 'НЕ ВЫБРАНО', tests: [], activeTest: [],
      };
    } else {
      root.$emit('msg', 'error', 'Такая услуга уже есть');
    }
  }
};

</script>

<style scoped lang="scss">
.body {
  height: 100%;
  width: 100%;
}
.scroll {
  max-height: calc(100% - 106px);
  overflow-y: auto;
}
.table {
  margin-bottom: 0;
  table-layout: fixed;
}
.research-col {
  width: 535px;
}
.button-col {
  width: 35px;
}
.sticky {
  position: sticky;
  top: 0;
  z-index: 1;
  background-color: white;
  border-bottom: 1px solid grey;
}
.add-research {
  width: 500px;
}
.flex {
  display: flex;
}
.border {
  border: 1px solid grey;
}
.research-padding {
  padding: 8px 6px;
}
.button {
  width: 100%;
  display: flex;
  flex-wrap: nowrap;
  flex-direction: row;
  justify-content: stretch;
}
.btn {
  align-self: stretch;
  flex: 1;
  padding: 7px 0;
}
.add-block {
  margin: 5px 0;
}
.checkbox {
  margin: 5px;
}
</style>
