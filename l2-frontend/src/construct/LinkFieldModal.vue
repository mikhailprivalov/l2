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
            v-for="research in addedResearches"
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
                  v-for="addedTest in research.tests"
                  :key="addedTest.id"
                  class="flex"
                >
                  <input
                    :id="addedTest.id"
                    v-model="research.activeTests"
                    :value="addedTest.id"
                    type="checkbox"
                    class="checkbox"
                  >
                  <label :for="addedTest.id"> {{ addedTest.label }} </label>
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
                v-model="researchToAdd"
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
                  v-for="selectedTest in researchToAdd.tests"
                  :key="selectedTest.id"
                  class="flex"
                >
                  <input
                    :id="`add-${selectedTest.id}`"
                    v-model="researchToAdd.activeTests"
                    :value="selectedTest.id"
                    type="checkbox"
                    class="checkbox"
                  >
                  <label :for="`add-${selectedTest.id}`"> {{ selectedTest.label }} </label>
                </div>
              </div>
            </td>
            <td class="border">
              <div class="button">
                <button
                  v-tippy
                  class="btn last btn-blue-nb nbr"
                  title="Добавить услугу"
                  :disabled="!researchSelect"
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
import {
  computed, getCurrentInstance, onMounted, ref,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import Modal from '@/ui-cards/Modal.vue';
import VueTippyTd from '@/construct/VueTippyTd.vue';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

const root = getCurrentInstance().proxy.$root;
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

const addedResearches = ref([]);

const researches = ref([
  {
    id: 1, label: 'Услуга 1', tests: [{ id: 1, label: 'тест 1' }, { id: 2, label: 'тест 2' }], activeTests: [],
  },
  {
    id: 2, label: 'Услуга 2', tests: [{ id: 3, label: 'тест 1' }, { id: 4, label: 'тест 2' }], activeTests: [],
  },
]);

const hospType = '%root_hosp';

// const currentLinkString = computed(() => {
//   const [hosp, type, value]: [string, string, string] = props.fieldValue.split('#');
//
// });

onMounted(async () => {
  const [hosp, type, value]: [string, string, string] = props.fieldValue.split('#');
  if (type === 'laboratory') {
    try {
      const parseValue = JSON.parse(value);
      if (typeof parseValue === 'object') {
        let researchNotExists = false;
        // eslint-disable-next-line no-restricted-syntax,guard-for-in
        for (const key in parseValue) {
          const currentResearch = researches.value.find(research => research.id === Number(key));
          if (currentResearch) {
            const tests = parseValue[key].split(',');
            currentResearch.activeTests.push(...tests);
            addedResearches.value.push(currentResearch);
          } else {
            researchNotExists = true;
          }
        }
        if (researchNotExists) {
          root.$emit('msg', 'warning', 'Некоторые услуги не добавлены');
        }
      } else {
        root.$emit('msg', 'error', 'Не удалось преобразовать лаб. ссылку');
      }
    } catch (error) {
      root.$emit('msg', 'error', 'Ошибка преобразования лаб. ссылки');
    }
  } else {
    root.$emit('msg', 'error', 'Текущее значение не лаб. ссылка');
  }
});

const researchToAdd = ref({
  id: -1, label: 'НЕ ВЫБРАНО', tests: [], activeTests: [],
});

const researchSelect = computed(() => researchToAdd.value.id !== -1);
const checkExists = (searchId) => addedResearches.value.find(research => research.id === searchId);
const addResearches = () => {
  if (researchSelect.value) {
    const exists = checkExists(researchToAdd.value.id);
    if (!exists) {
      addedResearches.value.push({ ...researchToAdd.value });
      researchToAdd.value = {
        id: -1, label: 'НЕ ВЫБРАНО', tests: [], activeTests: [],
      };
    } else {
      root.$emit('msg', 'error', 'Такая услуга уже есть');
    }
  } else {
    root.$emit('msg', 'error', 'Услуга не выбрана');
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
