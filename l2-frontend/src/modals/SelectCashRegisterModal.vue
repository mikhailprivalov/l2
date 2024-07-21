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
        <span slot="header">{{ titleLocal }}</span>
        <div slot="body">
          <div class="body">
            <div class="flex">
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

import { onMounted, ref } from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import Modal from '@/ui-cards/Modal.vue';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

const props = defineProps({
  tag: {
    type: String,
    default: 'li',
    required: false,
  },
  title: {
    type: String,
    required: false,
  },
});

const titleLocal = ref('');

onMounted(() => {
  titleLocal.value = props.title ? props.title : 'Выбрать кассу';
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
