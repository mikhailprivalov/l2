<template>
  <div class="telemedicine">
    <div class="filters">
      <div class="date-range">
        <div>
          <label>С</label>
          <input
            v-model="startDate"
            type="date"
            class="form-control date-range-input"
          >
        </div>
        <div>
          <label>По</label>
          <input
            v-model="endDate"
            type="date"
            class="form-control date-range-input"
          >
        </div>
      </div>
      <div class="service">
        <label>Услуга</label>
        <Treeselect
          v-model="selectedService"
          :options="Services"
          placeholder="Выберите услугу"
          :clearable="false"
        />
      </div>
      <div class="service-status">
        <label>Статус</label>
        <Treeselect
          v-model="selectedServiceStatus"
          :options="serviceStatuses"
          placeholder="Выберите статус"
          :clearable="false"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed, getCurrentInstance, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
// import * as actions from '@/store/action-types';
// import api from '@/api';
// import { useStore } from '@/store';

// const store = useStore();
// const root = getCurrentInstance().proxy.$root;

const startDate = ref(null);
const endDate = ref(null);

const selectedService = ref(null);
const services = ref([
  { id: 1, label: 'Услуга 1' },
  { id: 2, label: 'Услуга 2' },
  { id: 3, label: 'Услуга 3' },
  { id: 4, label: 'Услуга 4' },
]);
const getServices = async () => {
//   await store.dispatch(actions.INC_LOADING);
//   const { result } = await api('', {
//     startDate: startDate.value,
//     endDate: endDate.value,
//     serviceId: selectedService.value,
//     serviceStatus: selectedServiceStatus.value,
//   });
//   await store.dispatch(actions.DEC_LOADING);
//   services.value = result;
  console.log('получили услуги');
};

const selectedServiceStatus = ref('all');
const serviceStatuses = ref([
  { id: 'all', label: 'Все' },
  { id: 'confirm', label: 'Подтвержденные' },
]);

const filtersFilled = computed(() => !!((startDate.value && endDate.value
    && (new Date(startDate) < new Date(endDate))) && selectedService.value && selectedServiceStatus.value));
watch(filtersFilled, () => {
  if (filtersFilled.value) {
    getServices();
  }
});
</script>

<style scoped>
.telemedicine {
  width: 100%;
  margin: 0 auto;
}
.filters {
  display: flex;
  gap: 10px;
  margin: 0 10px 5px 10px;
}
.date-range {
  display: flex;
  width: 296px;
  gap: 10px;
}
.date-range-input {
  height: 36px;
  border-color: #d8d8d8;
}
.service {
  width: 490px;
}
.service-status {
  width: 130px;
}
</style>
