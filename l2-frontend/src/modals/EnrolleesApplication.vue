<template>
  <Modal
    ref="modal"
    margin-top
    margin-left-right="auto"
    max-width="800px"
    show-footer="true"
    white-bg="true"
    width="100%"
    @close="hideModal"
  >
    <span slot="header">Данные абитуриента - {{ fio }} </span>
    <div
      slot="body"
      class="registry-body"
      style="min-height: 100px"
    >
      <h4 class="text-center">
        Заявления
      </h4>
      <VeTable
        :columns="applicationsColumns"
        :table-data="application"
      />
      <div
        v-show="application.length === 0"
        class="empty-list"
      >
        Нет записей
      </div>
      <h4 class="text-center">
        Достижения
      </h4>
      <VeTable
        :columns="achievementsColumns"
        :table-data="achievements"
      />
      <div
        v-show="application.length === 0"
        class="empty-list"
      >
        Нет записей
      </div>
    </div>
    <div slot="footer">
      <div>
        <button
          class="btn btn-blue-nb"
          type="button"
          @click="hideModal"
        >
          Закрыть
        </button>
      </div>
    </div>
  </Modal>
</template>

<script setup lang="ts">

import {
  defineEmits, defineProps, onMounted,
  ref,
} from 'vue';
import {
  VeLocale,
  VeTable,
} from 'vue-easytable';

import 'vue-easytable/libs/theme-default/index.css';
import ruRu from '@/locales/ve';
import Modal from '@/ui-cards/Modal.vue';
import api from '@/api';

VeLocale.use(ruRu);
const emit = defineEmits(['hideEnrollees']);
const props = defineProps({
  card_pk: {
    type: Number,
    required: true,
  },
  fio: {
    type: String,
    required: true,
  },
});
const application = ref([]);
const applicationsColumns = ref([]);
const getApplications = async () => {
  const data = await api('/education/get-applications-by-card', { card_pk: props.card_pk });
  application.value = data.applications;
  applicationsColumns.value = data.columns;
};

const achievements = ref([]);
const achievementsColumns = ref([
  { field: 'pk', key: 'pk', title: '№' },
  { field: 'title', key: 'title', title: 'Название' },
  { field: 'date', key: 'date', title: 'Статус' },
  { field: 'grade', key: 'grade', title: 'Оценка' },
]);
const getAchievements = async () => {
  const data = await api('/education/get-achievements-by-card', { card_pk: props.card_pk });
  achievements.value = data.achievements;
};

const hideModal = () => {
  emit('hideEnrollees');
};

onMounted(() => {
  getApplications();
  getAchievements();
});
</script>

<style lang="scss" scoped>
.three-col-div {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-bottom: 5px;
}
.application-div {
  margin: 5px;
  padding: 0 5px;
}
.empty-list {
  width: 85px;
  margin: 20px auto;
}
</style>
