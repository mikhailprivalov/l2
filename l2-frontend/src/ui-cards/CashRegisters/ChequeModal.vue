<template>
  <transition name="fade">
    <Modal
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
      <div
        slot="body"
      >
        <div
          v-if="shiftIsOpen"
          class="body"
        >
          <div
            class="scroll"
          >
            <table class="table">
              <colgroup>
                <col>
                <col style="width: 100px">
              </colgroup>
              <thead class="sticky">
                <tr>
                  <th class="text-center">
                    <strong>Услуга</strong>
                  </th>
                  <th class="text-center">
                    <strong>Цена</strong>
                  </th>
                </tr>
              </thead>
              <tr
                v-for="service in servicesCoasts"
                :key="service.id"
              >
                <VueTippyTd
                  class="text-left padding service-title border"
                  :text="service.title"
                />
                <td class="text-center border padding">
                  {{ service.coast }}
                </td>
              </tr>
              <tfoot class="sticky-footer">
                <tr>
                  <td class="text-right">
                    <strong>
                      Итого:
                    </strong>
                  </td>
                  <td class="text-center">
                    <strong>
                      {{ summServiceCoasts }}
                    </strong>
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
          <div class="flex-space">
            <div class="flex">
              <div>
                <label>Наличными</label>
                <input
                  v-model="paymentCash"
                  type="number"
                  class="form-control"
                  min="0"
                >
              </div>
              <div>
                <label>Картой</label>
                <input
                  v-model="paymentCard"
                  type="number"
                  class="form-control"
                  min="0"
                >
              </div>
            </div>
            <div>
              <label>Скидка (%)</label>
              <input
                v-model="discount"
                type="number"
                class="form-control"
                min="0"
                max="100"
              >
            </div>
          </div>
          <div>
            <h5>К оплате {{ summForPay }}</h5>
          </div>
        </div>
        <h4 v-else>
          Смена не открыта
        </h4>
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
</template>

<script setup lang="ts">

import {
  computed,
  getCurrentInstance, onMounted, ref,
} from 'vue';

import Modal from '@/ui-cards/Modal.vue';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';
import VueTippyTd from '@/construct/VueTippyTd.vue';

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const emit = defineEmits(['closeModal']);
const props = defineProps({
  serviceIds: {
    type: Array,
    required: true,
  },
});

const cashRegister = computed(() => store.getters.cashRegisterShift);
const shiftIsOpen = computed(() => !!cashRegister.value?.cashRegisterId);

const loading = ref(false);

const closeModal = () => {
  emit('closeModal');
};

const servicesCoasts = ref([]);
const summServiceCoasts = ref(0);
const noCoast = ref(false);
const getServicesCoasts = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { coasts, summ, serviceWithoutCoast } = await api('cash-register/get-services-coasts', { serviceIds: props.serviceIds });
  await store.dispatch(actions.DEC_LOADING);
  servicesCoasts.value = coasts;
  summServiceCoasts.value = summ;
  noCoast.value = serviceWithoutCoast;
};
onMounted(async () => {
  await getServicesCoasts();
});

const paymentCash = ref(0);
const paymentCard = ref(0);
const discount = ref(0);

const summForPay = computed(() => {
  const summDiscount = (summServiceCoasts.value * discount.value) / 100;
  const forPay = summServiceCoasts.value - summDiscount;
  if (forPay > 0) {
    return forPay;
  }
  return 0;
});

</script>

<style scoped lang="scss">
.pointer {
  cursor: pointer;
}
.body {
  height: 500px;
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
.scroll {
  min-height: 106px;
  height: calc(100% - 113px);
  overflow-y: auto;
}
.table {
  margin-bottom: 0;
  table-layout: fixed;
}
.sticky {
  position: sticky;
  top: 0;
  z-index: 1;
  background-color: white;
}
.sticky-footer {
  position: sticky;
  bottom: 0;
  z-index: 1;
  background-color: white;
}
.table > thead > tr > th {
  border-bottom: 0;
}
.padding {
  padding: 2px 0 2px 6px
}
.service-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.border {
  border: 1px solid #ddd;
}
.flex-start {
  display: flex;
  justify-content: flex-start;
}
.flex-space {
  display: flex;
  justify-content: space-between;
}

</style>
