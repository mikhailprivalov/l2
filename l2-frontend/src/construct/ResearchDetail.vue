<template>
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
            :options="props.materials"
            placeholder="Выберите биоматериал"
            class="treeselect-34px"
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
            >Время (мин)</label>
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
              :options="props.subGroups"
              class="treeselect-34px"
              placeholder="Выберите подгруппу"
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
          :units="props.units"
          @updateOrder="updateOrder"
          @edit="edit"
          @addFraction="addFraction"
        />
        <div class="margin-bottom flex-right">
          <button
            class="btn btn-blue-nb"
            @click="updateResearch"
          >
            Сохранить
          </button>
        </div>
      </div>
      <FractionDetail
        v-if="currentFractionPk"
        :fraction-pk="currentFractionPk"
        :variants="props.variants"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  getCurrentInstance, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';
import FractionsGroup from '@/construct/FractionsGroup.vue';
import FractionDetail from '@/construct/FractionDetail.vue';

const store = useStore();

const emit = defineEmits(['updateResearch']);

const props = defineProps({
  researchPk: {
    type: Number,
    required: true,
  },
  departments: {
    type: Array,
    required: true,
  },
  units: {
    type: Array,
    required: true,
  },
  materials: {
    type: Array,
    required: true,
  },
  subGroups: {
    type: Array,
    required: true,
  },
  variants: {
    type: Array,
    required: true,
  },
  newResearch: {
    type: Object,
    required: true,
  },
  departmentId: {
    type: Number,
    required: true,
  },
});

interface fractionsData {
  pk: number,
  title: string,
  unitId: number,
  order: number,
  ecpId: number | string,
  fsli: number,
}

export interface tubeData {
  pk: number,
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
  ecpId: number | null,
  preparation: string | null,
  departmentId: number,
  laboratoryMaterialId: number,
  subGroupId: number,
  laboratoryDuration: string,
  tubes: tubeData[]
}
const researchShortTitle = ref('');

const root = getCurrentInstance().proxy.$root;

const research = ref<researchData>({
  pk: -1,
  title: '',
  shortTitle: '',
  code: null,
  order: null,
  internalCode: null,
  ecpId: null,
  preparation: '',
  departmentId: null,
  laboratoryMaterialId: null,
  subGroupId: null,
  laboratoryDuration: '',
  tubes: [],
});

const currentFractionPk = ref(null);

const getResearch = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('construct/laboratory/get-research', { researchPk: props.researchPk });
  await store.dispatch(actions.DEC_LOADING);
  research.value = result;
  researchShortTitle.value = research.value?.title;
};

watch(() => props.researchPk, () => {
  if (props.researchPk !== -1) {
    getResearch();
    currentFractionPk.value = null;
  } else {
    research.value = {
      pk: -1,
      title: '',
      shortTitle: '',
      code: null,
      order: null,
      internalCode: null,
      ecpId: null,
      preparation: '',
      departmentId: null,
      laboratoryMaterialId: null,
      subGroupId: null,
      laboratoryDuration: '',
      tubes: [],
    };
    for (const tube of props.newResearch.tubes) {
      research.value.tubes.push({
        pk: tube.pk,
        title: tube.title,
        color: tube.color,
        fractions: [
          {
            pk: -1,
            title: '',
            unitId: -1,
            order: 1,
            ecpId: '',
            fsli: -1,
          },
        ],
      });
    }
    research.value.order = props.newResearch.order;
    research.value.departmentId = props.departmentId;
    currentFractionPk.value = null;
  }
}, { immediate: true });

const updateResearch = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { ok } = await api('construct/laboratory/update-research', { research: research.value });
  await store.dispatch(actions.DEC_LOADING);
  if (ok) {
    root.$emit('msg', 'ok', 'Обновлено');
    emit('updateResearch');
  } else {
    root.$emit('msg', 'error', 'Ошибка');
  }
};

const updateOrder = async ({ fractionPk, fractionNearbyPk, action }) => {
  await store.dispatch(actions.INC_LOADING);
  const { ok } = await api('construct/laboratory/update-order-fraction', {
    fractionPk, fractionNearbyPk, action,
  });
  await store.dispatch(actions.DEC_LOADING);
  if (ok) {
    root.$emit('msg', 'ok', 'Обновлено');
    await getResearch();
  } else {
    root.$emit('msg', 'error', 'Ошибка');
  }
};

const edit = ({ fractionPk }) => {
  currentFractionPk.value = fractionPk;
};

const addFraction = (newFraction: object) => {
  const newFractionData = {
    pk: -1, title: '', unitId: null, order: newFraction.order, ecpId: null, fsli: null,
  };
  research.value.tubes[newFraction.tubeIdx].fractions.push(newFractionData);
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
}
.flex-col {
  display: flex;
  flex-wrap: wrap;
  align-content: flex-start;
}
.margin-root {
  margin: 0 10px 0 10px;
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
  grid-template-columns: repeat(auto-fit, minmax(200px, auto) minmax(150px, 350px));
}
.fraction-group {
  overflow-y: auto;
}
</style>
