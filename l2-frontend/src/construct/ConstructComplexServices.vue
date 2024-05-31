<template>
  <div>
    <Treeselect
      v-model="selectedComplex"
      :options="complexs"
      class="margin-bottom"
      value-format="object"
      placeholder="Выберите комплексную услугу"
    />
    <div class="block">
      <table class="table left-radius right-radius">
        <colgroup>
          <col>
          <col
            v-if="complexIsSelected"
            width="35"
          >
          <col width="100">
        </colgroup>
        <tr>
          <td>
            <input
              v-model="complexTitle"
              class="form-control nbr left-radius complex-title"
            >
          </td>
          <td v-if="complexIsSelected">
            <div class="button">
              <button
                v-if="complexIsSelected"
                v-tippy
                class="btn last btn-blue-nb nbr btn-flex"
                :title="complexIsHidden ? 'Показать': 'Скрыть'"
              >
                <i :class="complexIsHidden ? 'fa fa-eye' : 'fa fa-times'" />
              </button>
            </div>
          </td>
          <td>
            <div class="button">
              <button
                class="btn btn-blue-nb nbr btn-flex right-radius"
                :class="complexIsSelected ? 'btn-border-left' : '' "
              >
                {{ complexIsSelected ? 'Сохранить' : 'Создать' }}
              </button>
            </div>
          </td>
        </tr>
      </table>
    </div>
    <div
      v-if="complexIsSelected"
      class="block shadow nbr"
    >
      <div class="scroll">
        <table class="table">
          <colgroup>
            <col>
            <col
              v-if="!complexIsHidden"
              width="35"
            >
          </colgroup>
          <tr
            v-for="service in servicesInComplex"
            :key="service.id"
            class="tr-border"
          >
            <VueTippyTd
              class="padding-left"
              :text="service.label"
            />
            <td
              v-if="!complexIsHidden"
            >
              <div class="button">
                <button
                  v-tippy
                  class="btn btn-blue-nb nbr btn-flex"
                  :title="service.hide ? 'Показать' : 'Скрыть'"
                >
                  <i :class="service.hide ?'fa fa-eye' : 'fa fa-times'" />
                </button>
              </div>
            </td>
          </tr>
          <tr
            v-if="servicesInComplex.length === 0"
            class="text-center"
          >
            <td>
              Нет данных
            </td>
          </tr>
        </table>
      </div>
    </div>
    <div
      v-if="complexIsSelected && !complexIsHidden"
      class="block "
    >
      <table class="table left-radius right-radius">
        <colgroup>
          <col>
          <col width="100">
        </colgroup>
        <tr>
          <td>
            <Treeselect
              v-model="selectedService"
              :options="services"
              :disable-branch-nodes="true"
              class="left-radius"
              placeholder="Выберите услугу..."
            />
          </td>
          <td>
            <div class="button">
              <button
                v-tippy
                class="btn btn-blue-nb nbr btn-flex right-radius"
                title="Добавить услугу"
                :disabled="!selectedService"
                @click="addService"
              >
                Добавить
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
  computed, getCurrentInstance, onMounted, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import * as actions from '@/store/action-types';
import { useStore } from '@/store';
import api from '@/api';
import VueTippyTd from '@/construct/VueTippyTd.vue';

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const selectedComplex = ref(null);
const complexs = ref([]);
const hiddenStatus = ref(false);
const complexTitle = ref('');

const complexIsHidden = computed(() => hiddenStatus.value);
const complexIsSelected = computed(() => selectedComplex.value);

const getComplexs = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('construct/complex/get-complexs');
  await store.dispatch(actions.DEC_LOADING);
  complexs.value = result;
};

onMounted(() => {
  getComplexs();
});

const servicesInComplex = ref([]);

const getServicesInComplex = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('construct/complex/get-services', { complexId: selectedComplex.value.id });
  await store.dispatch(actions.DEC_LOADING);
  servicesInComplex.value = result;
};

const checkHidden = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('construct/complex/check-hidden', { complexId: selectedComplex.value.id });
  await store.dispatch(actions.DEC_LOADING);
  hiddenStatus.value = result;
};

watch(selectedComplex, () => {
  if (complexIsSelected.value) {
    checkHidden();
    getServicesInComplex();
    complexTitle.value = selectedComplex.value.label;
  } else {
    servicesInComplex.value = [];
    complexTitle.value = '';
    hiddenStatus.value = false;
    selectedComplex.value = null;
  }
});

const services = ref([]);
const selectedService = ref(null);
const getServices = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { data } = await api('get-research-list');
  await store.dispatch(actions.DEC_LOADING);
  services.value = data;
};

const addService = async () => {
  const serviceExists = servicesInComplex.value.find((service) => service.id === selectedService.value);
  if (!serviceExists) {
    await store.dispatch(actions.INC_LOADING);
    const { ok, message } = await api('construct/complex/add-service', {
      complexId: selectedComplex.value.id,
      serviceId: selectedService.value,
    });
    await store.dispatch(actions.DEC_LOADING);
    if (ok) {
      await getServicesInComplex();
      selectedService.value = null;
      root.$emit('msg', 'ok', 'Услуга добавлена');
    } else {
      root.$emit('msg', 'error', message);
    }
  } else {
    root.$emit('msg', 'error', 'Услуга уже добавлена');
  }
};

onMounted(() => {
  getServices();
});

</script>

<style scoped lang="scss">
.shadow {
  box-shadow: 0 1px 3px rgb(0 0 0 / 12%), 0 1px 2px rgb(0 0 0 / 24%);
}
.block {
  background-color: #fff;
  border-radius: 5px;
  margin-bottom: 20px;
}
.edit-complex {
  display: flex;
}
.complex-title {
  padding: 17px 12px;
  border: 1px solid #ddd;
}
.complex-title:focus {
  border: 1px solid #3bafda;
}
.margin-bottom {
  margin-bottom: 20px;
}
.scroll {
  min-height: 112px;
  max-height: calc(100vh - 400px);
  overflow-y: auto;
}
.table {
  margin-bottom: 0;
  table-layout: fixed;
}
.button {
  width: 100%;
  display: flex;
  flex-wrap: nowrap;
  flex-direction: row;
  justify-content: stretch;
}
.btn-flex {
    align-self: stretch;
    flex: 1;
    padding: 7px 0;
}

.btn-border-left {
  border-left: 1px solid #ddd !important;
}
.right-radius {
  border-bottom-right-radius: 5px !important;
  border-top-right-radius: 5px !important;
}
.left-radius {
  border-bottom-left-radius: 5px !important;
  border-top-left-radius: 5px !important;
}
.tr-border {
  border: 1px solid #ddd;
}
.padding-left {
  padding-left: 12px;
}
</style>
