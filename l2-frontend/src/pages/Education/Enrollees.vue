<template>
  <div class="main">
    <h4 class="header text-center">
      Абитуриенты
    </h4>
    <div class="margin flex">
      <button
        class="btn btn-blue-nb button-icon"
        @click="showFilters = !showFilters"
      >
        <i class="fa fa-filter" />
        {{ showFilters ? 'Скрыть' : 'Показать' }}
      </button>
    </div>
    <EnrolleesFilters
      v-if="showFilters"
      @changeFilters="changeFilters"
    />
    <div>
      <label>Поиск</label>
      <input
        v-model="search"
        placeholder="Введите ФИО... "
        class="form-control"
      >
    </div>
    <div>
      <EnrolleesTable
        :enrollees="filteredEnrollees"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed, onMounted, ref,
} from 'vue';

import EnrolleesTable from '@/pages/Education/EnrolleesTable.vue';
import api from '@/api';
import EnrolleesFilters from '@/pages/Education/EnrolleesFilters.vue';

const showFilters = ref(false);

const search = ref('');

const enrollees = ref([]);
const filteredEnrollees = computed(() => enrollees.value.filter(applicaiton => {
  const applicationFio = applicaiton.fio.toLowerCase();
  const searchTerm = search.value.toLowerCase();

  return applicationFio.includes(searchTerm);
}));

const getEnrollees = async (filters: object = {}) => {
  const result = await api('/education/get-enrollees', {
    filters: {
      specialities: filters ? filters.specialties : [],
      yearStudy: filters ? filters.year : {},
      enrolled: filters ? filters.applications === 1 : false,
      expelled: filters ? filters.applications === 2 : false,
    },
  });
  enrollees.value = result.data;
};

const changeFilters = (data) => {
  getEnrollees(data);
};
onMounted(
  () => {
    getEnrollees();
  },
);
</script>

<style scoped lang="scss">
.main {
  width: 90%;
  background-color: #ffffff;
  margin: 10px auto;
}
.margin {
  margin: 5px 10px;
}
.flex {
  display: flex;
  flex-wrap: wrap;
}
.header {
  margin: 10px;
}
.button-icon {
  background-color: transparent !important;
  color: #434A54;
  border: none !important;
  font-weight: 700;
  width: 110px;
}
.button-icon:hover {
  background-color: #434a54 !important;
  color: #FFFFFF
}
.button-icon:active {
  background-color: #37BC9B !important;
}
</style>
