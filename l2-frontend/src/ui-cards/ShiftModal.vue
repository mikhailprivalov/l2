<template>
  <component
    :is="props.tag"
  >
    <slot>
      <a
        class="pointer"
        @click.prevent="openModal"
      >{{ titleLocal }}
      </a>
    </slot>
    <transition name="fade">
      <Modal
        v-if="open"
        show-footer="true"
        ignore-body
        white-bg="true"
        max-width="710px"
        width="100%"
        margin-left-right="auto"
        @close="closeModal"
      >
        <span
          v-if="!loading"
          slot="header"
        >{{ 'Кассовые смены' }}</span>
        <span
          v-if="loading"
          slot="header"
          class="text-center"
        >{{ 'Загрузка...' }}</span>
        <div slot="body">
          <div class="body">
            <div
              v-if="!shiftIsOpen"
              class="flex"
            >
              <div class="input-group">
                <span
                  class="input-group-addon nbr width-title"
                >Касса</span>
                <Treeselect
                  v-model="selectedCashRegister"
                  :options="cashRegisters"
                  :disabled="shiftIsOpen || loading || statusShift === 'Смена закрывается'"
                  placeholder="Выберите кассу"
                />
              </div>
              <button
                v-if="shiftIsOpen"
                class="btn btn-blue-nb nbr width-action"
                :disabled="!selectedCashRegister || loading || statusShift === 'Смена закрывается'"
                @click="closeShift"
              >
                Закрыть
              </button>
              <button
                v-else
                class="btn btn-blue-nb nbr width-action"
                :disabled="!selectedCashRegister || loading || statusShift === 'Смена открывается'"
                @click="openShift"
              >
                Открыть
              </button>
            </div>
            <div>
              <table class="table">
                <colgroup>
                  <col style="width: 50px">
                  <col style="width: 50px">
                  <col>
                  <col style="width: 100px">
                  <col style="width: 100px">
                  <col style="width: 100px">
                </colgroup>
                <thead>
                  <tr>
                    <th class="text-center">
                      <strong>Смена №</strong>
                    </th>
                    <th class="text-center">
                      <strong>Касса №</strong>
                    </th>
                    <th class="text-center">
                      <strong>Название</strong>
                    </th>
                    <th class="text-center">
                      <strong>Открыта</strong>
                    </th>
                    <th class="text-center">
                      <strong>Статус</strong>
                    </th>
                    <th />
                  </tr>
                </thead>
                <tr>
                  <td class="text-center">
                    {{ currentShiftData.shiftId }}
                  </td>
                  <td class="text-center">
                    {{ currentShiftData.cashRegisterId }}
                  </td>
                  <td>{{ currentShiftData.cashRegisterTitle }}</td>
                  <td class="text-center">
                    {{ currentShiftData.open_at }}
                  </td>
                  <td class="text-center">
                    {{ currentShiftData.status }}
                  </td>
                  <td />
                </tr>
              </table>
            </div>
          </div>
        </div>
        <div slot="footer">
          <div class="row">
            <div class="col-xs-4">
              <button
                class="btn btn-primary-nb btn-blue-nb"
                type="button"
                :disabled="loading"
                @click="closeModal"
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      </Modal>
    </transition>
  </component>
</template>

<script setup lang="ts">

import {
  computed, getCurrentInstance, onMounted, ref,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import * as actions from '@/store/action-types';
import Modal from '@/ui-cards/Modal.vue';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import { useStore } from '@/store';
import api from '@/api';

interface shiftData {
  shiftId: number,
  cashRegisterId: number,
  cashRegisterTitle: string,
  open_at: string,
  status: string
}

const store = useStore();
const root = getCurrentInstance().proxy.$root;
const props = defineProps({
  tag: {
    type: String,
    default: 'li',
    required: false,
  },
});

const loading = ref(false);

const cashRegister = computed(() => store.getters.cashRegisterShift);
const shiftIsOpen = computed(() => !!cashRegister.value?.cashRegisterId);
const selectedCashRegister = ref(null);
const cashRegisters = ref([]);
const currentShiftData = ref<shiftData>({
  shiftId: null,
  cashRegisterId: null,
  cashRegisterTitle: '',
  open_at: '',
  status: '',
});
const statusShift = ref('');

// eslint-disable-next-line @typescript-eslint/no-unused-vars
let intervalReq = null;

const titleLocal = ref('');
const getCashRegisters = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('cash-register/get-cash-registers');
  await store.dispatch(actions.DEC_LOADING);
  cashRegisters.value = result;
};
const getShiftData = async () => {
  const { ok, message, data } = await api('cash-register/get-shift-data');
  if (ok) {
    currentShiftData.value = data;
    statusShift.value = data.status;
    if (!shiftIsOpen.value && data.status === 'Открывается') {
      titleLocal.value = `Смена ${data.status.toLowerCase()}`;
      intervalReq = setTimeout(() => getShiftData(), 1000);
    } else if (!shiftIsOpen.value && data.status === 'Открыта') {
      await store.dispatch(actions.OPEN_SHIFT, { cashRegisterId: data.cashRegisterId, shiftId: data.shiftId });
      titleLocal.value = `Смена ${data.status.toLowerCase()}`;
      root.$emit('msg', 'ok', 'Смена открыта');
      intervalReq = null;
    } else if (shiftIsOpen.value && data.status === 'Закрывается') {
      titleLocal.value = `Смена ${data.status.toLowerCase()}`;
      intervalReq = setTimeout(() => getShiftData(), 1000);
    } else if (shiftIsOpen.value && data.status === 'Закрыта') {
      await store.dispatch(actions.CLOSE_SHIFT);
      titleLocal.value = `Смена ${data.status.toLowerCase()}`;
      root.$emit('msg', 'ok', 'Смена закрыта');
      intervalReq = null;
    } else {
      titleLocal.value = `Смена ${data.status.toLowerCase()}`;
    }
  } else {
    titleLocal.value = shiftIsOpen.value ? 'Смена открыта' : 'Смена закрыта';
    selectedCashRegister.value = null;
    intervalReq = null;
    root.$emit('msg', 'error', message);
  }
};

onMounted(async () => {
  await getCashRegisters();
  selectedCashRegister.value = shiftIsOpen.value ? cashRegister.value.cashRegisterId : null;
  await getShiftData();
});

const open = ref(false);

const openModal = () => {
  open.value = true;
};
const closeModal = () => {
  open.value = false;
};

const openShift = async () => {
  if (!selectedCashRegister.value) {
    root.$emit('msg', 'error', 'Касса не выбрана');
  } else {
    loading.value = true;
    const { ok, message } = await api('cash-register/open-shift', { cashRegisterId: selectedCashRegister.value });
    loading.value = false;
    if (ok) {
      await getShiftData();
    } else {
      root.$emit('msg', 'error', message);
    }
  }
};
const closeShift = async () => {
  loading.value = true;
  const { ok, message } = await api('cash-register/close-shift', { cashRegisterId: selectedCashRegister.value });
  loading.value = false;
  if (ok) {
    await getShiftData();
  } else {
    root.$emit('msg', 'error', message);
  }
};

</script>

<style scoped lang="scss">
.pointer {
  cursor: pointer;
}
.body {
  height: 300px;
}
.flex {
  display: flex;
}
.width-title {
  width: 100px;
}
.width-action {
  min-width: 100px;
}

::v-deep .vue-treeselect__control {
  border: 1px solid #AAB2BD !important;
  border-radius: 0;
}

.table {
  margin-bottom: 0;
  table-layout: fixed;
}
</style>
