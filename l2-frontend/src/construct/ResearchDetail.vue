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
      </div>
      <div class="code">
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
            v-model="research.ecpCode"
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
            class="form-control"
            style="height: 90px"
            rows="4"
            placeholder="Введите подготовку (напр. 'Не требуется')"
          />
        </div>
      </div>
    </div>
    <h4 class="header">
      Фракции
    </h4>
    <div class="research-fractions">
      <div
        v-for="tube in research.tubes"
        :key="tube.pk"
        class="tube-group"
      >
        <Tube :tube="tube" />
        <table class="table">
          <colgroup>
            <col>
            <col width="300">
            <col width="300">
          </colgroup>
          <thead>
            <tr>
              <th><strong>Фракция</strong></th>
              <th><strong>Ед. измерения</strong></th>
              <th><strong>Вар. комментариев</strong></th>
            </tr>
          </thead>
          <tr
            v-for="fraction in tube.fractions"
            :key="fraction.pk"
          >
            <td class="padding-td no-left-padding">
              <input
                v-model="fraction.title"
                class="form-control fraction-input"
                placeholder="Введите название фракции"
              >
            </td>
            <td class="padding-td">
              <input
                v-model="fraction.unit"
                class="form-control fraction-input"
                placeholder="Введите ед. изм"
              >
            </td>
            <td class="padding-td no-right-padding">
              <input
                v-model="fraction.variants"
                class="form-control fraction-input"
              >
            </td>
          </tr>
        </table>
      </div>
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

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';
import Tube from '@/construct/Tube.vue';

const store = useStore();

const emit = defineEmits(['updateResearch']);

const props = defineProps({
  researchPk: {
    type: Number,
    required: true,
  },
});

interface fractionsData {
  pk: number,
  title: string,
  unit: string,
  variants: string[] | null,
  sortWeight: number,
}

interface tubeData {
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
  ecpCode: number | null,
  preparation: string | null,
  tubes: tubeData[]
}
const researchShortTitle = ref('');

const root = getCurrentInstance().proxy.$root;
const research = ref<researchData>({
  pk: -1,
  title: '',
  shortTitle: '',
  code: -1,
  internalCode: -1,
  ecpCode: -1,
  preparation: '',
  tubes: [
    {
      pk: -1,
      title: '',
      color: '',
      fractions: [
        {
          pk: -1,
          title: '',
          unit: '',
          variants: null,
          sortWeight: -1,
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
.code {
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
  justify-content: end;
}
.tube-group {
  margin-bottom: 10px;
  background-color: #fff;
  padding: 10px 5px;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgb(0 0 0 / 12%), 0 1px 2px rgb(0 0 0 / 24%);
}
.table {
  table-layout: fixed;
  margin-bottom: 0;
}
.padding-td {
  padding: 2px 5px;
}
.no-left-padding {
  padding-left: 0;
}
.no-right-padding {
  padding-right: 0;
}
.border {
  border: 1px solid #bbb;
}
.fraction-input {
  height: 28px;
}
</style>
