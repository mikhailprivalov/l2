<template>
  <div>
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
        <tr v-if="addedResearches.length === 0">
          <td
            colspan="3"
            class="text-center"
          >
            <div class="not-added-research">
              Нет данных
            </div>
          </td>
        </tr>
        <tr
          v-for="(research, idx) in addedResearches"
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
                <label :for="addedTest.id"> {{ addedTest.title }} </label>
              </div>
            </div>
          </td>
          <td class="border">
            <div class="button">
              <button
                v-tippy
                class="btn last btn-blue-nb nbr"
                title="Удалить услугу"
                @click="deleteResearch(idx)"
              >
                <i class="fa fa-times" />
              </button>
            </div>
          </td>
        </tr>
      </table>
    </div>
    <h5 class="margin">
      Добавить услугу
    </h5>
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
              :options="researches"
              :clearable="false"
              class="treeselect-noborder"
              placeholder="Выберите услугу"
            />
          </td>
          <td class="border" />
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
</template>

<script setup lang="ts">
import {
  computed, getCurrentInstance, PropType, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import VueTippyTd from '@/construct/VueTippyTd.vue';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

const root = getCurrentInstance().proxy.$root;
const emit = defineEmits(['add-lab-data']);

interface testData {
  id: number,
  title: string,
  isHideFraciton: boolean,
}
interface researchData {
  departmentTitle: string,
  id: number,
  label: string,
  tests: testData[]
}

const props = defineProps({
  linkValue: {
    required: true,
    type: String,
  },
  researches: {
    required: true,
    type: Object as PropType<researchData[]>,
  },
});

const addedResearches = ref([]);

const deleteResearch = (index) => {
  addedResearches.value.splice(index, 1);
};

const currentLabData = computed(() => {
  const addResearches = {};
  for (const research of addedResearches.value) {
    if (research.activeTests.length > 0) {
      addResearches[research.id] = research.activeTests.sort().join(',');
    }
  }
  return JSON.stringify(addResearches);
});

watch(currentLabData, () => {
  emit('add-lab-data', currentLabData.value);
});

const parsePropsValue = () => {
  addedResearches.value = [];
  const { linkValue } = props;
  if (!linkValue || (linkValue && linkValue.trim().length === 0)) {
    return;
  }
  const normalizedValue = linkValue.trim();
  try {
    const parseValue = JSON.parse(normalizedValue);
    if (typeof parseValue !== 'object') {
      root.$emit('msg', 'warning', 'Не удалось разобрать лаб. ссылку');
      return;
    }
    let researchNotExists = false;
    let testsNotAdd = false;
    // eslint-disable-next-line no-restricted-syntax,guard-for-in
    for (const key in parseValue) {
      const currentResearch = props.researches.find(research => research.id === Number(key));
      if (!currentResearch) {
        researchNotExists = true;
        continue;
      }
      const copyCurrentResearch = structuredClone(currentResearch);
      const tests = parseValue[key].replaceAll(' ', '').split(',');
      const allTestIsNumber = tests.every((test) => Number(test));
      if (allTestIsNumber) {
        copyCurrentResearch.activeTests = [...tests];
      } else {
        testsNotAdd = true;
      }
      addedResearches.value.push(copyCurrentResearch);
    }
    if (researchNotExists) {
      root.$emit('msg', 'warning', 'Некоторые услуги не добавлены');
    }
    if (testsNotAdd) {
      root.$emit('msg', 'warning', 'Некоторые тесты не добавлены');
    }
  } catch (error) {
    root.$emit('msg', 'error', 'Ошибка преобразования лаб. ссылки');
  }
};

watch(() => props.linkValue, () => {
  if (props.linkValue !== currentLabData.value) {
    parsePropsValue();
  }
});

const researchToAdd = ref(null);

const researchSelect = computed(() => Boolean(researchToAdd.value));
const checkExists = (searchId) => addedResearches.value.find(research => research.id === searchId);
const addResearches = () => {
  if (researchSelect.value) {
    const exists = checkExists(researchToAdd.value);
    if (!exists) {
      const currentResearch = props.researches.find(research => research.id === researchToAdd.value);
      const activeTests = currentResearch.tests.map(test => test.id);
      addedResearches.value.push({ ...currentResearch, activeTests });
      researchToAdd.value = null;
    } else {
      root.$emit('msg', 'error', 'Такая услуга уже есть');
    }
  } else {
    root.$emit('msg', 'error', 'Услуга не выбрана');
  }
};
</script>

<style scoped lang="scss">
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
.not-added-research {
  margin: 10px;
}
.margin {
  margin: 5px;
}
</style>
