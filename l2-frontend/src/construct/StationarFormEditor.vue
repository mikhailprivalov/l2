<template>
  <div class="root">
    <div class="top-editor">
      <div class="left">
        <div class="input-group">
          <span class="input-group-addon">Стационарная услуга</span>
          <SelectFieldTitled
            v-model="mainServicePk"
            :variants="researchesList"
          />
        </div>
      </div>
      <div class="right">
        <div class="input-group">
          <label
            v-tippy
            class="input-group-addon"
            style="height: 34px;text-align: left;"
            title="Другой цвет в ленте стационара"
          >
            <input
              v-model="anotherColorInStationarPanel"
              type="checkbox"
            > Изм. цвет
          </label>
          <label
            class="input-group-addon"
            style="height: 34px;text-align: left;"
          >
            <input
              v-model="hide"
              type="checkbox"
            > Скрытие
          </label>
        </div>
      </div>
    </div>
    <div class="content-editor">
      <ParaclinicResearchEditor
        style="position: absolute;top: 0;right: 0;bottom: 0;left: 0;"
        simple
        :main_service_pk="mainServicePk"
        :hs_pk="pk"
        :hide_main="hide"
        :pk="slaveServicePk"
        :department="department"
        :another_color_in_stationar_panel="anotherColorInStationarPanel"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';

import constructPoint from '@/api/construct-point';
import researchesPoint from '@/api/researches-point';
import SelectFieldTitled from '@/fields/SelectFieldTitled.vue';
import * as actions from '@/store/action-types';
import { useStore } from '@/store';

import ParaclinicResearchEditor from './ParaclinicResearchEditor.vue';

const props = defineProps<{
  pk: number;
  department: number;
}>();

const store = useStore();

const hide = ref(false);
const hasUnsaved = ref(false);
const loadedPk = ref(-2);
const mainServicePk = ref(-1);
const slaveServicePk = ref(-1);
const researchesList = ref<any[]>([]);
const anotherColorInStationarPanel = ref(false);

const load = async () => {
  hide.value = false;
  anotherColorInStationarPanel.value = false;
  mainServicePk.value = -1;
  slaveServicePk.value = -1;
  await store.dispatch(actions.INC_LOADING);
  const { researches } = await researchesPoint.getResearchesByDepartment({ department: -5 });
  researchesList.value = researches;
  if (props.pk >= 0) {
    const data = await constructPoint.hospServiceDetails({ pk: props.pk }, 'pk');

    mainServicePk.value = data.main_service_pk;
    slaveServicePk.value = data.slave_service_pk;
    hide.value = data.hide;
    anotherColorInStationarPanel.value = data.another_color_in_stationar_panel;
    loadedPk.value = props.pk;
  }
  await store.dispatch(actions.DEC_LOADING);
  if (mainServicePk.value === -1) {
    mainServicePk.value = researchesList.value[0].pk;
  }
};

watch(() => props.pk, () => {
  load();
});

watch(loadedPk, () => {
  hasUnsaved.value = false;
});

onMounted(() => {
  load();
});
</script>

<style scoped lang="scss">
  .top-editor {
    display: flex;
    width: 100%;
    flex: 0 0 34px;

    .left {
      flex: 0 0 calc(100% - 200px);
      ::v-deep .form-control {
        width: 100%;
      }
    }

    .right {
      flex: 0 0 200px
    }

    .input-group-addon {
      border-top: none;
      border-left: none;
      border-right: none;
      border-radius: 0;
    }

    ::v-deep .form-control {
      border-top: none;
      border-radius: 0;
    }
  }

  .content-editor {
    height: 100%;
    position: relative;
  }

  .top-editor, .content-editor{
    align-self: stretch;
  }

  .root {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    align-content: stretch;
  }

  .content-editor {
    overflow: visible;
  }
</style>
