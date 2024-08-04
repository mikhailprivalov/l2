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
              class="flex"
            >
              <div class="input-group">
                <span
                  class="input-group-addon nbr width-title"
                >Касса</span>
                <Treeselect
                  v-model="selectedCashRegister"
                  :options="cashRegisters"
                  :disabled="shiftIsOpen || loading || statusShift === 2"
                  placeholder="Выберите кассу"
                />
              </div>
              <button
                v-if="shiftIsOpen"
                class="btn btn-blue-nb nbr width-action"
                :disabled="!selectedCashRegister || loading || statusShift === 2"
                @click="closeShift"
              >
                Закрыть
              </button>
              <button
                v-else
                class="btn btn-blue-nb nbr width-action"
                :disabled="!selectedCashRegister || loading || statusShift === 0"
                @click="openShift"
              >
                Открыть
              </button>
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
const shiftData = ref({});

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
  const { ok, data } = await api('cash-register/get-shift-data');
  if (ok) {
    shiftData.value = data;
    if (!shiftIsOpen.value && data.status === 'Смена открывается') {
      titleLocal.value = data.status;
      intervalReq = setTimeout(() => getShiftData(), 1000);
    } else if (!shiftIsOpen.value && data.status === 'Смена открыта') {
      await store.dispatch(actions.OPEN_SHIFT, { cashRegisterId: data.cashRegisterId, shiftId: data.shiftId });
      titleLocal.value = data.status;
      root.$emit('msg', 'ok', 'Смена открыта');
      intervalReq = null;
    } else if (shiftIsOpen.value && data.status === 'Смена закрывается') {
      titleLocal.value = data.status;
      intervalReq = setTimeout(() => getShiftData(), 1000);
    } else if (shiftIsOpen.value && data.status === 'Смена закрыта') {
      await store.dispatch(actions.CLOSE_SHIFT);
      titleLocal.value = data.status;
      root.$emit('msg', 'ok', 'Смена закрыта');
      intervalReq = null;
    }
  } else {
    shiftData.value = {};
    titleLocal.value = 'Смена закрыта';
    selectedCashRegister.value = null;
    if (shiftIsOpen.value) {
      await store.dispatch(actions.CLOSE_SHIFT);
    }
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
</style>
