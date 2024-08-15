<template>
  <div>
    <button
      class="btn btn-blue-nb nbr"
      :disabled="!shiftIsOpen"
      @click="openModal"
    >
      Оплата
    </button>
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
        >{{ 'Чек' }}</span>
        <span
          v-if="loading"
          slot="header"
          class="text-center"
        >{{ 'Загрузка...' }}</span>
        <div slot="body">
          <div class="body" />
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
  </div>
</template>

<script setup lang="ts">

import {
  computed,
  getCurrentInstance, ref,
} from 'vue';

import Modal from '@/ui-cards/Modal.vue';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import { useStore } from '@/store';

const store = useStore();
const root = getCurrentInstance().proxy.$root;
const props = defineProps({
  tag: {
    type: String,
    default: 'li',
    required: false,
  },
});

const cashRegister = computed(() => store.getters.cashRegisterShift);
const shiftIsOpen = computed(() => !!cashRegister.value?.cashRegisterId);

const loading = ref(false);

const open = ref(false);

const openModal = () => {
  if (shiftIsOpen.value) {
    open.value = true;
  } else {
    root.$emit('msg', 'error', 'Смена не открыта');
  }
};
const closeModal = () => {
  open.value = false;
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
.button {
  width: 100%;
  display: flex;
  flex-wrap: nowrap;
  flex-direction: row;
  justify-content: stretch;
}
  .btn {
    align-self: stretch;
    flex: 1;
    padding: 7px 0;
  }
.cash-register-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.close-button {
  padding: 9px 0;
}
</style>
