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
                <col style="width: 100px">
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
                  <th class="text-center">
                    <strong>Кол-во</strong>
                  </th>
                  <th>
                    <strong>Сумма</strong>
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
                <td class="text-center border padding">
                  <input
                    v-model="service.count"
                    min="1"
                    type="number"
                    class="form-control"
                    @change="changeServiceAmount(service.id)"
                  >
                </td>
                <td class="text-center border padding">
                  {{ service.amount }}
                </td>
              </tr>
              <tfoot class="sticky-footer">
                <tr>
                  <td class="text-right" />
                  <td class="text-center" />
                  <td class="text-center">
                    <strong>
                      Итого:
                    </strong>
                  </td>
                  <td class="text-center">
                    <strong>
                      {{ sumServiceCoasts }}
                    </strong>
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
          <div v-if="cardIsSelected">
            <div class="flex-space">
              <div class="flex">
                <div class="input-width">
                  <label>Наличными</label>
                  <input
                    v-model.number="paymentCash"
                    type="number"
                    class="form-control"
                    step="0.01"
                    min="0"
                    @input="changeElectronic"
                  >
                </div>
                <div class="input-width">
                  <label>Картой</label>
                  <input
                    v-model.number="paymentElectronic"
                    type="number"
                    class="form-control"
                    step="0.01"
                    min="0"
                    @input="changeCash"
                  >
                </div>
              </div>
              <div class="discount-width">
                <label>Скидка (%)</label>
                <input
                  v-model.number="discount"
                  type="number"
                  class="form-control"
                  min="0"
                  step="1"
                  max="100"
                >
              </div>
            </div>
            <div class="flex-space">
              <h5>К оплате {{ summForPay.toFixed(2) }}</h5>
              <button
                v-if="!noCoast"
                class="btn btn-blue-nb pay-button"
                @click="payment"
              >
                Оплатить
              </button>
              <h5
                v-else
                class="text-red"
              >
                Не все услуги имеют цену
              </h5>
            </div>
            <div
              v-if="paymentCash"
              class="input-width"
            >
              <label>Получено наличными</label>
              <input
                v-model.number="receivedCash"
                type="number"
                class="form-control"
              >
              <h5>Сдача: {{ cashReturn.toFixed(2) }}</h5>
            </div>
          </div>
          <div v-else>
            <h4>Пациент не выбран</h4>
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
  computed, getCurrentInstance,
  onMounted, ref, watch,
} from 'vue';

import Modal from '@/ui-cards/Modal.vue';
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
  cardId: {
    type: Number,
    required: true,
  },
});

const cashRegister = computed(() => store.getters.cashRegisterShift);
const shiftIsOpen = computed(() => !!cashRegister.value?.cashRegisterId);
const cardIsSelected = computed(() => props.cardId !== -1);
const loading = ref(false);

const closeModal = () => {
  emit('closeModal');
};

interface serviceCoast {
  id: number,
  title: string,
  coast: number,
  count: number,
  amount: number,
}

const servicesCoasts = ref<serviceCoast[]>([]);

const changeServiceAmount = (serviceId) => {
  const service = servicesCoasts.value.find(i => i.id === serviceId);
  service.amount = service.count * service.coast;
};

const sumServiceCoasts = computed(() => {
  let result = 0;
  for (const service of servicesCoasts.value) {
    console.log(service.amount);
    result += Number(service.amount);
  }
  console.log(result);
  return result;
});
const noCoast = ref(false);
const getServicesCoasts = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { coasts, serviceWithoutCoast } = await api('cash-register/get-services-coasts', { serviceIds: props.serviceIds });
  await store.dispatch(actions.DEC_LOADING);
  servicesCoasts.value = coasts;
  noCoast.value = serviceWithoutCoast;
};
onMounted(async () => {
  await getServicesCoasts();
});

const paymentCash = ref(0);
const paymentElectronic = ref(0);
const discount = ref(0);

const summForPay = computed(() => {
  if (discount.value >= 0 && discount.value <= 100) {
    const summDiscount = (sumServiceCoasts.value * discount.value) / 100;
    return Number((sumServiceCoasts.value - summDiscount).toFixed(2));
  }
  if (discount.value < 0) {
    return Number(sumServiceCoasts.value.toFixed(2));
  }
  return 0.00;
});

const changeElectronic = () => {
  if (paymentCash.value < 0) {
    paymentCash.value = 0.00;
  }
  const result = summForPay.value - paymentCash.value;
  if (result >= 0) {
    paymentElectronic.value = Number(result.toFixed(2));
  } else {
    paymentElectronic.value = 0;
  }
};
const changeCash = () => {
  if (paymentElectronic.value < 0) {
    paymentElectronic.value = 0.00;
  }
  const result = summForPay.value - paymentElectronic.value;
  if (result >= 0) {
    paymentCash.value = Number(result.toFixed(2));
  } else {
    paymentCash.value = 0;
  }
};

watch([summForPay], () => {
  if (summForPay.value) {
    paymentElectronic.value = Number((summForPay.value - paymentCash.value).toFixed(2));
  } else {
    paymentElectronic.value = 0;
    paymentCash.value = 0;
  }
});

const receivedCash = ref(0);
const cashReturn = computed(() => {
  if (receivedCash.value && receivedCash.value >= paymentCash.value) {
    return receivedCash.value - paymentCash.value;
  }
  return 0;
});

// eslint-disable-next-line @typescript-eslint/no-unused-vars
let intervalReq = null;
const chequeId = ref(null);
const getChequeData = async () => {
  const { ok, message } = await api('cash-register/get-cheque-data', {
    chequeId: chequeId.value,
  });
  intervalReq = setTimeout(() => getChequeData(), 1000);
  if (ok) {
    root.$emit('msg', 'ok', 'чек проверен');
  } else {
    root.$emit('msg', 'ok', message);
  }
};

const payment = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { ok, message, cheqId } = await api('cash-register/payment', {
    shiftId: cashRegister.value.shiftId,
    serviceCoasts: servicesCoasts.value,
    sumCoasts: sumServiceCoasts.value,
    discount: discount.value,
    cash: paymentCash.value,
    receivedCash: receivedCash.value,
    electronic: paymentElectronic.value,
    forPay: summForPay.value,
    cardId: props.cardId,
  });
  await store.dispatch(actions.DEC_LOADING);
  chequeId.value = cheqId;
  if (ok) {
    root.$emit('msg', 'ok', 'Заявка отправлена');
    await getChequeData();
  } else {
    root.$emit('msg', 'error', message);
  }
};

</script>

<style scoped lang="scss">
.body {
  height: 500px;
}
.flex {
  display: flex;
}
.scroll {
  min-height: 106px;
  height: calc(100% - 200px);
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
.flex-space {
  display: flex;
  justify-content: space-between;
}
.input-width {
  width: 165px;
}
.discount-width {
  width: 90px;
}
.text-red {
  color: red;
}
.pay-button {
  margin: 5px 0;
}
</style>
