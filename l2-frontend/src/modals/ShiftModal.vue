<template>
  <component
    :is="tag"
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
        <span slot="header">{{ 'Кассовые смены' }}</span>
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
                  :disabled="shiftIsOpen"
                  class="treeselect-noborder"
                  placeholder="Выберите кассу"
                />
              </div>
              <button
                v-if="shiftIsOpen"
                class="btn btn-blue-nb nbr width-action"
                @click="closeShift"
              >
                Закрыть
              </button>
              <button
                v-else
                class="btn btn-blue-nb nbr width-action"
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

import { computed, onMounted, ref } from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import * as actions from '@/store/action-types';
import Modal from '@/ui-cards/Modal.vue';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import { useStore } from '@/store';

const store = useStore();

const props = defineProps({
  tag: {
    type: String,
    default: 'li',
    required: false,
  },
});

const cashRegister = computed(() => store.getters.cashRegister);
const shiftIsOpen = computed(() => !!cashRegister.value?.id);
const titleLocal = computed(() => (shiftIsOpen.value ? 'Смена открыта' : 'Смена закрыта'));
const selectedCashRegister = ref(null);
const cashRegisters = ref([
  { id: 1, label: 'Касса 1' },
  { id: 2, label: 'Касса 2' },
  { id: 3, label: 'Касса 3' },
]);

onMounted(() => {
  selectedCashRegister.value = shiftIsOpen.value ? cashRegister.value.id : null;
});

const open = ref(false);

const openModal = () => {
  open.value = true;
};
const closeModal = () => {
  open.value = false;
};

const openShift = () => {
  store.dispatch(actions.OPEN_SHIFT);
};
const closeShift = () => {
  store.dispatch(actions.CLOSE_SHIFT);
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
</style>
