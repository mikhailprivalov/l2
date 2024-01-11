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
            for="department"
            class="research-detail-label"
          >Подразделение</label>
          <Treeselect
            v-model="research.departmentId"
            :options="props.departments"
            :clearable="false"
            placeholder="Выберите подразделение"
          />
        </div>
      </div>
      <div class="flex-col">
        <div class="margin code-item">
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
        <div class="margin code-item">
          <label
            for="ecpCode"
            class="research-detail-label"
          >Код ЕЦП</label>
          <input
            id="ecpCode"
            v-model="research.ecpId"
            class="form-control"
            placeholder="Введите код"
          >
        </div>
        <div class="margin code-item">
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
            placeholder="Введите подготовку (напр. 'Не требуется')"
          />
        </div>
      </div>
    </div>
    <h4 class="header">
      Фракции
    </h4>
    <div class="research-fractions">
      <FractionsGroup
        v-for="tube in research.tubes"
        :key="tube.pk"
        :tube="tube"
        @updateOrder="updateOrder"
        @edit="edit"
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
  </div>
</template>

<script setup lang="ts">
import {
  getCurrentInstance, onMounted, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';
import FractionsGroup from '@/construct/FractionsGroup.vue';

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
});

interface fractionsData {
  pk: number,
  title: string,
  unitId: string,
  order: number,
  ecpId: number,
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
  internalCode: number | null,
  ecpId: number | null,
  preparation: string | null,
  departmentId: number,
  tubes: tubeData[]
}
const researchShortTitle = ref('');

const root = getCurrentInstance().proxy.$root;
const research = ref<researchData>({
  pk: -1,
  title: '',
  shortTitle: '',
  code: null,
  internalCode: null,
  ecpCode: null,
  preparation: '',
  department: null,
  tubes: [
    {
      pk: -1,
      title: '',
      color: '',
      fractions: [
        {
          pk: -1,
          title: '',
          unitId: '',
          order: null,
          ecpId: null,
          fsli: null,
        },
      ],
    }],
});

const getResearch = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('construct/laboratory/get-research', { researchPk: props.researchPk });
  await store.dispatch(actions.DEC_LOADING);
  research.value = result;
  researchShortTitle.value = research.value?.title;
};

watch(() => props.researchPk, () => {
  getResearch();
});

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

const currentFractionPk = ref(null);

const edit = ({ fractionPk }) => {
  currentFractionPk.value = fractionPk;
  root.$emit('msg', 'ok', 'Получили фракцию');
};

onMounted(() => {
  getResearch();
});
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
.code-item {
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
</style>
