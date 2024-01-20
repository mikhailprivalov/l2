<template>
  <div>
    <div class="margin-root">
      <h4 class="header">
        Редактирование анализа - {{ researchShortTitle }}
      </h4>
      <div class="research-detail">
        <div>
          <div class="margin">
            <label
              for="title"
              class="research-detail-label"
            >Полное наименование</label>
            <input
              id="title"
              v-model="research.title"
              v-tippy
              :title="research.title"
              class="form-control"
              placeholder="Введите полное наименование"
            >
          </div>
          <div class="margin">
            <label
              for="shortTitle"
              class="research-detail-label"
            >Краткое наименование</label>
            <input
              id="shortTitle"
              v-model="research.shortTitle"
              class="form-control"
              placeholder="Введите краткое наименование"
            >
          </div>
          <div class="margin">
            <label
              class="research-detail-label"
            >Подразделение</label>
            <Treeselect
              v-model="research.departmentId"
              :options="props.departments"
              :clearable="false"
              class="treeselect-34px"
              placeholder="Выберите подразделение"
              :append-to-body="true"
            />
          </div>
        </div>
        <div>
          <div class="flex-col">
            <div class="margin flex-item">
              <label
                for="code"
                class="research-detail-label"
              >Код НМУ</label>
              <input
                id="code"
                v-model="research.code"
                class="form-control"
                placeholder="Введите код"
              >
            </div>
            <div class="margin flex-item">
              <label
                for="ecpId"
                class="research-detail-label"
              >Код ЕЦП</label>
              <input
                id="ecpId"
                v-model="research.ecpId"
                class="form-control"
                placeholder="Введите код"
              >
            </div>
            <div class="margin flex-item">
              <label
                for="internalCode"
                class="research-detail-label"
              >Код внутренний</label>
              <input
                id="internalCode"
                v-model="research.internalCode"
                class="form-control"
                placeholder="Введите код"
              >
            </div>
          </div>
          <div class="margin">
            <label
              class="research-detail-label"
            >Биоматериал</label>
            <Treeselect
              v-model="research.laboratoryMaterialId"
              :options="props.refBooks.materials"
              placeholder="Выберите биоматериал"
              class="treeselect-34px"
              :append-to-body="true"
            />
          </div>
        </div>
        <div>
          <div class="margin">
            <label
              for="preparation"
              class="research-detail-label"
            >Подготовка</label>
            <textarea
              id="preparation"
              v-model="research.preparation"
              class="form-control"
              style="height: 90px"
              rows="4"
              placeholder="Введите подготовку (напр. 'Не требуется')"
            />
          </div>
          <div class="flex-col">
            <div class="margin flex-item">
              <label
                for="laboratoryDuration"
                class="research-detail-label"
              >Время</label>
              <input
                id="laboratoryDuration"
                v-model="research.laboratoryDuration"
                class="form-control"
                type="number"
              >
            </div>
            <div class="margin flex-item">
              <label
                class="research-detail-label"
              >Подгруппа</label>
              <Treeselect
                v-model="research.subGroupId"
                :options="props.refBooks.subGroups"
                class="treeselect-34px"
                placeholder="Выберите подгруппу"
                :append-to-body="true"
              />
            </div>
          </div>
        </div>
      </div>
      <h4 class="header">
        Фракции
      </h4>
      <div class="research-fractions">
        <div class="fraction-group">
          <FractionsGroup
            v-for="(tube, idx) in research.tubes"
            :key="tube.pk"
            :tube="tube"
            :tubeidx="idx"
            :units="props.refBooks.units"
            @updateOrder="updateOrder"
            @edit="edit"
            @addFraction="addFraction"
          />
        </div>
        <div class="main">
          <div
            v-if="currentFractionData.title"
            class="fraction-detail"
          >
            <h6>Фракция - {{ currentFractionData.title }}</h6>
            <label>По умолчанию</label>
            <input class="form-control">
            <label>Варианты</label>
            <Treeselect
              v-model="currentFractionData.variantsId"
              :options="props.refBooks.variants"
              :clearable="false"
              :append-to-body="true"
            />
            <label>Формула</label>
            <input
              v-model="currentFractionData.formula"
              class="form-control"
            >
            <label>Рефернсы М</label>
            <div
              v-for="(refM, idx) in currentFractionData.refM"
              :key="idx"
              class="flex ref-row"
            >
              <input
                v-model="refM.age"
                class="form-control reference-input-left"
              >
              <input
                v-model="refM.value"
                class="form-control reference-input-right"
              >
              <button
                class="reference-button-right transparent-button "
                @click="deleteRef(idx, 'm')"
              >
                <i class="fa fa-times" />
              </button>
            </div>
            <div>
              <button
                class="transparent-button"
                @click="addRef('m')"
              >
                <i class="fa fa-plus" />
              </button>
            </div>
            <label>Рефернсы Ж</label>
            <div
              v-for="(refF, idx) in currentFractionData.refF"
              :key="idx"
              class="flex ref-row"
            >
              <input
                v-model="refF.age"
                class="form-control reference-label-left"
              >
              <input
                v-model="refF.value"
                class="form-control reference-label-right"
              >
              <button
                class="transparent-button reference-button-right"
                @click="deleteRef(idx, 'f')"
              >
                <i class="fa fa-times" />
              </button>
            </div>
            <div>
              <button
                class="transparent-button"
                @click="addRef('f')"
              >
                <i class="fa fa-plus" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="bottom-panel">
      <div class="tube-add">
        <div>
          <label class="research-detail-label">Ёмкости</label>
          <Treeselect
            v-model="selectedTubes"
            value-format="object"
            class="treeselect-34px"
            placeholder="Выберите ёмкость"
            :options="props.refBooks.tubes"
          >
            <div
              slot="value-label"
              slot-scope="{ node }"
            >
              <ColorTitled
                :title="node.label"
                :color="node.raw.color"
              />
            </div>
            <div
              slot="option-label"
              slot-scope="{ node }"
            >
              <ColorTitled
                :title="node.label"
                :color="node.raw.color"
              />
            </div>
          </Treeselect>
        </div>
        <div>
          <button
            class="btn btn-blue-nb"
            @click="addTubes"
          >
            Добавить
          </button>
        </div>
      </div>
      <div>
        <button
          class="btn btn-blue-nb"
          @click="updateResearch"
        >
          Сохранить
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  getCurrentInstance, PropType, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';
import FractionsGroup from '@/construct/FractionsGroup.vue';
import { refBook } from '@/construct/ConstructLaboratory.vue';
import ColorTitled from '@/ui-cards/ColorTitled.vue';

const store = useStore();

const emit = defineEmits(['updateResearch']);

const props = defineProps({
  research: {
    type: Object,
    required: true,
  },
  departments: {
    type: Array,
    required: true,
  },
  refBooks: {
    type: Object as PropType<refBook>,
    required: true,
  },
});

interface reference {
  age: string | null,
  value: string | null,
}

interface fractionsData {
  id: number,
  title: string,
  unitId: number,
  order: number,
  ecpId: string,
  fsli: number,
  variantsId: number,
  formula: string,
  refM: reference[],
  refF: reference[],
}

export interface tubeData {
  id: number,
  tubeId: number,
  title: string,
  color: string,
  fractions: fractionsData[],
}

interface researchData {
  pk: number | null,
  title: string | null,
  shortTitle: string | null,
  code: number | null,
  order: number,
  internalCode: number | null,
  ecpId: string,
  preparation: string | null,
  departmentId: number,
  laboratoryMaterialId: number,
  subGroupId: number,
  laboratoryDuration: string,
  tubes: tubeData[]
}

const selectedTubes = ref({
  id: -1,
  label: 'Выберите ёмкость',
  color: '',
});
const researchShortTitle = ref('');

const root = getCurrentInstance().proxy.$root;

const research = ref<researchData>({
  pk: -1,
  title: '',
  shortTitle: '',
  code: null,
  order: null,
  internalCode: null,
  ecpId: '',
  preparation: '',
  departmentId: null,
  laboratoryMaterialId: null,
  subGroupId: null,
  laboratoryDuration: '',
  tubes: [],
});

const defaultFraction = ref<fractionsData>({
  ecpId: '',
  formula: '',
  fsli: null,
  order: 1,
  id: -1,
  refF: [],
  refM: [],
  title: '',
  unitId: null,
  variantsId: null,
});

const currentFractionData = ref<fractionsData>({ ...defaultFraction.value });

const addTubes = () => {
  const tubesData = {
    id: -1,
    tubeId: selectedTubes.value.id,
    title: selectedTubes.value.label,
    color: selectedTubes.value.color,
    fractions: [{ ...defaultFraction.value }],
  };
  research.value.tubes.push(tubesData);
};

const getResearch = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('construct/laboratory/get-research', { researchPk: props.research.pk });
  await store.dispatch(actions.DEC_LOADING);
  research.value = result;
  researchShortTitle.value = research.value.shortTitle ? research.value.shortTitle : research.value.title;
};

watch(() => [props.research.pk, props.research.tubes], () => {
  if (props.research.pk !== -1) {
    getResearch();
    currentFractionData.value = { ...defaultFraction.value };
  } else {
    research.value = {
      pk: -1,
      title: '',
      shortTitle: '',
      code: null,
      order: props.research.order,
      internalCode: null,
      ecpId: '',
      preparation: '',
      departmentId: props.research.departmentId,
      laboratoryMaterialId: null,
      subGroupId: null,
      laboratoryDuration: '',
      tubes: [],
    };
    for (const tube of props.research.tubes) {
      research.value.tubes.push({
        id: tube.id,
        tubeId: tube.tubeId,
        title: tube.title,
        color: tube.color,
        fractions: [
          {
            ...defaultFraction.value,
          },
        ],
      });
    }
    currentFractionData.value = { ...defaultFraction.value };
  }
}, { immediate: true });

const updateResearch = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { ok } = await api('construct/laboratory/update-research', { research: research.value });
  await store.dispatch(actions.DEC_LOADING);
  if (ok) {
    root.$emit('msg', 'ok', 'Обновлено');
    await getResearch();
    emit('updateResearch');
  } else {
    root.$emit('msg', 'error', 'Ошибка');
  }
};

const updateOrder = async ({
  tubeIdx, fractionNearbyOrder, fractionOrder, action,
}) => {
  if (action === 'inc_order') {
    const currentFraction = research.value.tubes[tubeIdx].fractions.find(fraction => fraction.order === fractionOrder);
    const nearbyFraction = research.value.tubes[tubeIdx].fractions.find(fraction => fraction.order === fractionNearbyOrder);
    currentFraction.order += 1;
    nearbyFraction.order -= 1;
  } else if (action === 'dec_order') {
    const currentFraction = research.value.tubes[tubeIdx].fractions.find(fraction => fraction.order === fractionOrder);
    const nearbyFraction = research.value.tubes[tubeIdx].fractions.find(fraction => fraction.order === fractionNearbyOrder);
    currentFraction.order -= 1;
    nearbyFraction.order += 1;
  }
};

const edit = ({ fractionOrder, tubeIdx }) => {
  currentFractionData.value = research.value.tubes[tubeIdx].fractions.find(fraction => fraction.order === fractionOrder);
};

const addFraction = (newFraction: object) => {
  const newFractionData = {
    ...defaultFraction.value,
  };
  newFractionData.order = newFraction.order;
  research.value.tubes[newFraction.tubeIdx].fractions.push(newFractionData);
};

const addRef = (refKey: string) => {
  if (refKey === 'm') {
    currentFractionData.value.refM.push({ age: '', value: '' });
  } else {
    currentFractionData.value.refF.push({ age: '', value: '' });
  }
};

const deleteRef = (idx: number, refKey: string) => {
  if (refKey === 'm') {
    currentFractionData.value.refM.splice(idx, 1);
  } else {
    currentFractionData.value.refF.splice(idx, 1);
  }
};

</script>

<style scoped lang="scss">
.research-detail {
  display: grid;
  background-color: #fff;
  border-radius: 4px;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  padding: 10px 0;
  box-shadow: 0 1px 3px rgb(0 0 0 / 12%), 0 1px 2px rgb(0 0 0 / 24%);
  max-height: 185px;
  overflow-y: auto;
}
.flex-col {
  display: flex;
  flex-wrap: wrap;
  align-content: flex-start;
}
.margin-root {
  margin: 0 10px 0 10px;
  height: calc(100vh - 105px);
}
.margin {
  margin: 0 5px;
}
.margin-bottom {
  margin-bottom: 15px;
}
.research-detail-label {
  margin-bottom: 0;
  margin-left: 12px;
}
.flex-item {
  flex-grow: 1;
  flex-basis: 145px;
}
.header {
  margin: 10px 0 10px 17px;
}
.flex-right {
  display: flex;
  justify-content: flex-end;
}
::v-deep .vue-treeselect__control {
  border: 1px solid #AAB2BD !important;
  border-radius: 4px;
}
.research-fractions {
  display: grid;
  position: relative;
  grid-template-columns: repeat(auto-fit, minmax(200px, auto) minmax(150px, 320px));
  height: calc(100vh - 365px);
}
.fraction-group {
  overflow-y: auto;
  position: relative;
}
.save-button {
  position: absolute;
  bottom: 5px;
  right: 5px;
}
.bottom-panel {
  display: flex;
  margin: 0 10px 5px 15px;
  justify-content: space-between;
  align-items: flex-end;
}
.tube-add {
  max-width: 500px;
  display: flex;
  align-items: flex-end;
}

.main {
  border-left: 1px solid #b1b1b1;
  margin-left: 10px;
  padding-left: 10px;
  position: relative;
  overflow-y: auto;
}
.fraction-detail {
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgb(0 0 0 / 12%), 0 1px 2px rgb(0 0 0 / 24%);
  padding: 10px 5px 10px 5px;
  overflow-y: auto;
}
.flex {
  display: flex;
}
.flex-end {
  display: flex;
  justify-content: flex-end;
}

.reference-input-left {
  border-radius: 4px 0 0 4px;
}
.reference-input-right {
  border-radius: 0;
}
.reference-button-right {
  border-radius: 0 4px 4px 0 !important;
}

.transparent-button {
  background-color: transparent;
  align-self: stretch;
  color: #434A54;
  border: 1px solid #AAB2BD;
  border-radius: 4px;
}
.transparent-button:hover {
  background-color: #434a54;
  color: #FFFFFF;
}
.transparent-button:active {
  background-color: #37BC9B;
  color: #FFFFFF;
}
.ref-row {
  margin-bottom: 2px;
}
</style>
