<template>
  <transition name="fade">
    <Modal
      show-footer="true"
      ignore-body
      white-bg="true"
      max-width="810px"
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
                <col style="width: 90px">
                <col style="width: 90px">
                <col style="width: 90px">
                <col style="width: 90px">
                <col style="width: 80px">
                <col style="width: 90px">
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
                    <strong>Скидка %</strong>
                  </th>
                  <th class="text-center">
                    <strong>Скидка Р</strong>
                  </th>
                  <th class="text-center">
                    <strong>Цена со скидкой</strong>
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
                v-for="(service, idx) in servicesCoasts"
                :key="service.id"
              >
                <VueTippyTd
                  class="text-left padding service-title border"
                  :text="service.title"
                />
                <td class="text-center border">
                  {{ service.coast }}
                </td>
                <td class="text-center border">
                  <input
                    v-model.number="service.discountRelative"
                    type="number"
                    :disabled="loading || service.discountStatic"
                    class="form-control nbr input-item"
                    min="0"
                    max="100"
                    @input="changeDiscountRelative(idx, service.discountStatic)"
                  >
                </td>
                <td class="text-center border">
                  <input
                    v-model.number="service.discountAbsolute"
                    type="number"
                    :disabled="loading || service.discountStatic"
                    class="form-control nbr input-item"
                    min="0"
                    :max="service.coast"
                    @input="changeDiscountAbsolute(idx, service.discountStatic)"
                  >
                </td>
                <td class="text-center border">
                  {{ service.discountedCoast }}
                </td>
                <td class="text-center border">
                  <input
                    v-model.number="service.count"
                    min="1"
                    type="number"
                    :disabled="loading"
                    class="form-control nbr input-item"
                    @input="changeServiceCount(idx)"
                  >
                </td>
                <td class="text-center border">
                  {{ service.total }}
                </td>
              </tr>
              <tfoot class="sticky-footer">
                <tr>
                  <td class="text-right" />
                  <td class="text-center" />
                  <td class="text-center" />
                  <td class="text-center" />
                  <td class="text-center" />
                  <td class="text-center">
                    <strong>
                      Итого:
                    </strong>
                  </td>
                  <td class="text-center">
                    <strong>
                      {{ totalServicesCoast }}
                    </strong>
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
          <div v-if="!noCoast">
            <div class="flex-space">
              <div class="flex">
                <div class="input-width">
                  <label>Наличными</label>
                  <input
                    v-model.number="paymentCash"
                    type="number"
                    :disabled="loading"
                    class="form-control nbr"
                    step="0.01"
                    min="0"
                    :max="totalServicesCoast"
                    @input="changeElectronic"
                  >
                </div>
                <div class="input-width">
                  <label>Картой</label>
                  <input
                    v-model.number="paymentElectronic"
                    type="number"
                    :disabled="loading"
                    class="form-control nbr"
                    step="0.01"
                    min="0"
                    :max="totalServicesCoast"
                    @input="changeCash"
                  >
                </div>
              </div>
              <div class="discount-width">
                <label>Скидка (%)</label>
                <input
                  v-model.number="discount"
                  type="number"
                  :disabled="loading"
                  class="form-control nbr"
                  min="0"
                  step="1"
                  max="100"
                  @input="changeDiscountRelativeAll()"
                >
              </div>
            </div>
            <div class="flex-space">
              <h5>К оплате {{ totalServicesCoast }}</h5>
              <button
                class="btn btn-blue-nb nbr pay-button"
                :disabled="loading"
                @click="payment"
              >
                Оплатить
              </button>
            </div>
            <div
              v-if="paymentCash"
              class="input-width"
            >
              <label>Получено наличными</label>
              <input
                v-model.number="receivedCash"
                type="number"
                class="form-control nbr"
              >
              <h5>Сдача: {{ cashReturn }}</h5>
            </div>
          </div>
          <div v-if="noCoast">
            <h4 class="text-red text-center">
              Не все услуги имеют цену
            </h4>
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
    required: false,
  },
  directionsIds: {
    type: Array,
    required: false,
  },
});

const cashRegister = computed(() => store.getters.cashRegisterShift);
const shiftIsOpen = computed(() => !!cashRegister.value?.cashRegisterId);
const loading = ref(false);

const closeModal = () => {
  if (!loading.value) {
    emit('closeModal');
  }
};

interface serviceCoast {
  id: number,
  title: string,
  coast: number,
  discountRelative: number,
  discountAbsolute: number,
  discountStatic: boolean,
  discountedCoast: number,
  count: number,
  total: number,
}

const servicesCoasts = ref<serviceCoast[]>([]);

const changeDiscountRelative = (index: number, discountStatic: boolean, serviceObj: object = null) => {
  if (!loading.value && !discountStatic) {
    let service;
    if (serviceObj) {
      service = serviceObj;
    } else {
      service = servicesCoasts.value[index];
    }
    if (service.discountRelative >= 0 && service.discountRelative <= 100) {
      const discountAbsolute = (service.coast * service.discountRelative) / 100;
      service.discountAbsolute = Number(discountAbsolute.toFixed(2));
      const discountedCoast = service.coast - service.discountAbsolute;
      service.discountedCoast = Number(discountedCoast.toFixed(2));
      const total = service.count * service.discountedCoast;
      service.total = Number(total.toFixed(2));
    }
  }
};

const changeDiscountAbsolute = (index: number, discountStatic: boolean) => {
  if (!loading.value && !discountStatic) {
    const service = servicesCoasts.value[index];
    if (service.discountAbsolute >= 0 && service.discountAbsolute <= service.coast) {
      const discountRelative = (service.discountAbsolute / service.coast) * 100;
      service.discountRelative = Number(discountRelative.toFixed(2));
      const discountedCoast = service.coast - service.discountAbsolute;
      service.discountedCoast = Number(discountedCoast.toFixed(2));
      const total = service.count * service.discountedCoast;
      service.total = Number(total.toFixed(2));
    }
  }
};

const changeServiceCount = (index) => {
  if (!loading.value) {
    const service = servicesCoasts.value[index];
    if (service.total >= 1) {
      service.total = service.count * service.discountedCoast;
    }
  }
};

const totalServicesCoast = computed(() => {
  let result = 0;
  for (const service of servicesCoasts.value) {
    result += Number(service.total);
  }
  return Number(result.toFixed(2));
});
const noCoast = ref(true);
const getServicesCoasts = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { coasts, serviceWithoutCoast } = await api('cash-register/get-services-coasts', {
    directionsIds: props.directionsIds,
  });
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

const changeDiscountRelativeAll = () => {
  if (discount.value >= 0 && discount.value <= 100) {
    for (const service of servicesCoasts.value) {
      if (!service.discountStatic) {
        service.discountRelative = discount.value;
        changeDiscountRelative(null, service.discountStatic, service);
      }
    }
  }
};

const changeElectronic = () => {
  if (paymentCash.value < 0) {
    paymentCash.value = 0.00;
  }
  const result = totalServicesCoast.value - paymentCash.value;
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
  const result = totalServicesCoast.value - paymentElectronic.value;
  if (result >= 0) {
    paymentCash.value = Number(result.toFixed(2));
  } else {
    paymentCash.value = 0;
  }
};

watch([totalServicesCoast], () => {
  if (totalServicesCoast.value) {
    paymentElectronic.value = Number((totalServicesCoast.value - paymentCash.value).toFixed(2));
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
  const { ok, message, chequeReady } = await api('cash-register/get-cheque-data', {
    chequeId: chequeId.value,
  });
  if (ok) {
    if (chequeReady) {
      root.$emit('msg', 'ok', 'Чек проведён');
      intervalReq = null;
      loading.value = false;
    } else {
      intervalReq = setTimeout(() => getChequeData(), 1000);
    }
  } else {
    root.$emit('msg', 'error', message);
    intervalReq = null;
  }
};

const payment = async () => {
  if (!loading.value) {
    loading.value = true;
    await store.dispatch(actions.INC_LOADING);
    const { ok, message, cheqId } = await api('cash-register/payment', {
      shiftId: cashRegister.value.shiftId,
      serviceCoasts: servicesCoasts.value,
      totalCoast: totalServicesCoast.value,
      cash: paymentCash.value,
      receivedCash: receivedCash.value,
      electronic: paymentElectronic.value,
    });
    await store.dispatch(actions.DEC_LOADING);
    chequeId.value = cheqId;
    if (ok) {
      root.$emit('msg', 'ok', 'Заявка отправлена');
      await getChequeData();
    } else {
      root.$emit('msg', 'error', message);
    }
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
  background-color: #FFF;
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
.table > tfoot > tr > td {
  border-top: 0;
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
.no-r-border {
  border-right: none;
}
.no-l-border {
  border-left: none;
}

.flex-space {
  display: flex;
  justify-content: space-between;
}
.input-width {
  width: 165px;
}
.discount-width {
  width: 120px;
}
.discount-type {
  flex: 1 1 50px;
}
.text-red {
  color: red;
}
.pay-button {
  margin: 5px 0;
}
.no-border {
  border: none;
}
.input-item {
  border: 1px solid transparent;
  padding: 6px;
}
.input-item:focus {
  border: 1px solid #3bafda;
}
</style>
