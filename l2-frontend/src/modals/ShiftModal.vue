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
        <span slot="header">{{ reverseTitle }}</span>
        <div slot="body">
          <div class="body">
            <div
              v-if="!shiftId"
              class="flex"
            >
              <div class="input-group">
                <span
                  class="input-group-addon nbr"
                  style="width: 150px"
                >Касса</span>
                <Treeselect
                  v-model="selectedCashRegister"
                  :options="cashRegisters"
                  class="treeselect-noborder"
                  placeholder="Выберите кассу"
                />
              </div>
              <button class="btn btn-blue-nb">
                выбрать
              </button>
            </div>
            <div v-else>
              <button class="btn btn-blue-nb">
                Закрыть смену
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

const titleLocal = ref('');
const reverseTitle = ref('');
const shiftId = computed(() => store.getters.shift);

onMounted(() => {
  titleLocal.value = shiftId.value ? 'Смена открыта' : 'Смена закрыта';
  reverseTitle.value = shiftId.value ? 'Закрытие смены' : 'Открытие смены';
});

const open = ref(false);

const openModal = () => {
  open.value = true;
};
const closeModal = () => {
  open.value = false;
};

const selectedCashRegister = ref(null);
const cashRegisters = ref([
  { id: 1, label: 'Касса 1' },
  { id: 2, label: 'Касса 2' },
  { id: 3, label: 'Касса 3' },
]);

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
</style>
