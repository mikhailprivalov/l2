<template>
  <div>
    <div class="margin">
      <button
        class="btn btn-blue-nb button-icon"
        @click="clearFilters"
      >
        Очистить
      </button>
    </div>
    <div>
      <div class="four-col">
        <div class="margin">
          <label>Направление</label>
          <Treeselect
            v-model="selectedSpecialties"
            :multiple="true"
            :options="specialties"
            placeholder="Выберите направление"
            class="treeselect-wide"
          />
        </div>
        <div class="margin">
          <label>Основание</label>
          <Treeselect
            v-model="selectedPayForms"
            :multiple="true"
            :options="payForms"
            placeholder="Выберите основание"
          />
        </div>
        <div class="margin">
          <label>Заказчик</label>
          <Treeselect
            v-model="selectedCompany"
            :options="companies"
            placeholder="Выберите заказчика"
            :normalizer="normalizerCompany"
          />
        </div>
        <div class="margin">
          <label>Приказ</label>
          <Treeselect
            v-model="selectedEnrollmentOrders"
            :multiple="true"
            :options="enrollmentOrders"
            placeholder="Выберите приказ"
          />
        </div>
        <div class="margin">
          <label>Гражданство</label>
          <Treeselect
            v-model="selectedCitizenship"
            :options="citizenship"
            placeholder="Выберите гражданство"
          />
        </div>
        <div class="margin">
          <label>Источник заявления</label>
          <Treeselect
            v-model="selectedApplicationSources"
            :multiple="true"
            :options="applicationSources"
            placeholder="Выберите источник"
          />
        </div>
        <div class="margin">
          <label>Статус заявлений</label>
          <Treeselect
            v-model="selectedApplicationStatus"
            :options="applicationStatuses"
            placeholder="Выберите статус"
          />
        </div>
        <div class="margin">
          <label>Этап заявления</label>
          <Treeselect
            v-model="selectedApplicationStage"
            :options="applicationStages"
            placeholder="Выберите этап"
          />
        </div>
        <div class="margin">
          <label>Тип экзамена</label>
          <Treeselect
            v-model="selectedExamTypes"
            :multiple="true"
            :options="examTypes"
            placeholder="Выберите тип"
          />
        </div>
        <div class="margin">
          <label>Предмет</label>
          <Treeselect
            v-model="selectedExamSubjects"
            :multiple="true"
            :options="examSubjects"
            placeholder="Выберите предмет"
          />
        </div>
        <div class="margin">
          <label>Тип ИД</label>
          <Treeselect
            v-model="selectedAchievementTypes"
            :multiple="true"
            :options="achievementTypes"
            placeholder="Выберите тип"
          />
        </div>
        <div class="margin">
          <label>Статус ИД</label>
          <Treeselect
            v-model="selectedAchievementsStatuses"
            :multiple="true"
            :options="achievementsStatuses"
            placeholder="Выберите статус"
          />
        </div>
        <div class="margin">
          <label>Образование</label>
          <Treeselect
            v-model="selectedEducations"
            :multiple="true"
            value-consists-of="LEAF_PRIORITY"
            :options="educations"
            placeholder="Выберите тип"
          />
        </div>
        <div class="margin">
          <label>Особое право</label>
          <Treeselect
            v-model="selectedSpecialRights"
            :multiple="true"
            :options="specialRights"
            value-consists-of="LEAF_PRIORITY"
            placeholder="Выберите право"
          />
        </div>
        <div class="margin">
          <label>Год набора</label>
          <Treeselect
            v-model="selectedYearApplication"
            value-format="object"
            :options="yearApplication"
            value-consists-of="LEAF_PRIORITY"
            placeholder="Выберите год"
            @input="getSpecialties"
          />
        </div>
      </div>
      <div class="four-col">
        <div class="margin flex">
          <div>
            <input
              id="consent"
              v-model="consent"
              type="checkbox"
              class="input-checkbox"
            >
            <label
              for="consent"
              class="label-for-checkbox"
            >Согласие на зачисление</label>
          </div>
          <div>
            <input
              id="activeApplicationOnly"
              v-model="activeApplicationOnly"
              type="checkbox"
              class="input-checkbox"
            >
            <label
              for="activeApplicationOnly"
              class="label-for-checkbox"
            >Только активные заявления</label>
          </div>
        </div>
        <div class="margin flex">
          <div>
            <input
              id="contract"
              v-model="contract"
              type="checkbox"
              class="input-checkbox"
            >
            <label
              for="contract"
              class="label-for-checkbox"
            >Договор прикреплен</label>
          </div>
          <div>
            <input
              id="payment"
              v-model="payment"
              type="checkbox"
              class="input-checkbox"
            >
            <label
              for="payment"
              class="label-for-checkbox"
            >Есть оплата</label>
          </div>
        </div>
        <div class="margin flex">
          <div>
            <input
              id="isOriginal"
              v-model="isOriginal"
              class="input-checkbox"
              type="checkbox"
            >
            <label
              for="isOriginal"
              class="label-for-checkbox"
            >Оригинал</label>
          </div>
        </div>
        <div class="margin flex">
          <div>
            <input
              id="examChecked"
              v-model="examChecked"
              class="input-checkbox"
              type="checkbox"
            >
            <label
              for="examChecked"
              class="label-for-checkbox"
            >Экзамен проверен</label>
          </div>
          <div>
            <input
              id="isSatisfactoryScore"
              v-model="isSatisfactoryScore"
              class="input-checkbox"
              type="checkbox"
            >
            <label
              for="isSatisfactoryScore"
              class="label-for-checkbox"
            >Балл удовлетворительный</label>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  defineEmits, onMounted, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import 'vue-easytable/libs/theme-default/index.css';
import api from '@/api';

const emit = defineEmits(['changeFilters']);

const selectedPayForms = ref([]);
const payForms = ref([]);
const getPayForms = async () => {
  const data = await api('/education/get-pay-forms');
  payForms.value = data.result;
};

const selectedCompany = ref(null);
const companies = ref([]);
const getCompanies = async () => {
  const result = await api('/get-companies');
  companies.value = result.data;
};

const normalizerCompany = (node) => ({
  id: node.pk,
  label: node.title,
});

const isEnrolled = ref(false);
const isExpelled = ref(false);

const selectedEnrollmentOrders = ref([]);
const enrollmentOrders = ref([]);

const selectedCitizenship = ref(null);
const citizenship = ref([]);
const getCitizenship = async () => {
  const data = await api('/education/get-citizenship');
  citizenship.value = data.result;
};

const selectedApplicationSources = ref([]);
const applicationSources = ref([]);
const selectedApplicationStatus = ref(null);
const applicationStatuses = ref([
  { id: 1, label: 'Зачислен' },
  { id: 2, label: 'Отчислен' },
]);
const selectedApplicationStage = ref(null);
const applicationStages = ref([]);

const selectedExamTypes = ref([]);
const examTypes = ref([]);
const selectedExamSubjects = ref([]);
const examSubjects = ref([]);
const examChecked = ref(false);
const getExamsFilters = async () => {
  const data = await api('/education/get-exams-filters');
  examTypes.value = data.exam_types;
  examSubjects.value = data.subjects;
};

const selectedAchievementTypes = ref([]);
const achievementTypes = ref([]);
const selectedAchievementsStatuses = ref([]);
const achievementsStatuses = ref([]);
const getAchievementsFilters = async () => {
  const data = await api('/education/get-achievements-filters');
  achievementTypes.value = data.achievements;
};

const isSatisfactoryScore = ref(false);
const selectedEducations = ref([]);
const educations = ref([]);
const getEducations = async () => {
  const data = await api('/education/get-educations');
  educations.value = data.result;
};
const selectedSpecialRights = ref([]);
const specialRights = ref([]);
const getSpecialRights = async () => {
  const data = await api('/education/get-special-rights');
  specialRights.value = data.result;
};

const consent = ref(false);
const activeApplicationOnly = ref(false);
const contract = ref(false);
const payment = ref(false);
const isOriginal = ref(false);
const selectedYearApplication = ref({ id: 2, label: 2023 });
const yearApplication = ref([
  { id: 1, label: 2022 },
  { id: 2, label: 2023 },
]);

const selectedSpecialties = ref([]);
const specialties = ref([]);
const getSpecialties = async () => {
  const data = await api('/education/get-specialties', { yearStartStudy: selectedYearApplication });
  specialties.value = data.result;
};

const clearFilters = () => {
  selectedSpecialties.value = [];
  selectedPayForms.value = [];
  selectedCompany.value = null;
  isEnrolled.value = false;
  isExpelled.value = false;
  selectedEnrollmentOrders.value = [];
  consent.value = false;
  activeApplicationOnly.value = false;
  contract.value = false;
  payment.value = false;
  selectedCitizenship.value = null;
  selectedApplicationSources.value = [];
  selectedApplicationStatus.value = null;
  selectedApplicationStage.value = null;
  selectedExamTypes.value = [];
  selectedExamSubjects.value = [];
  examChecked.value = false;
  selectedAchievementTypes.value = [];
  selectedAchievementsStatuses.value = [];
  isSatisfactoryScore.value = false;
  selectedEducations.value = [];
  isOriginal.value = false;
  selectedSpecialRights.value = [];
  selectedYearApplication.value = { id: 2, label: 2023 };
};

onMounted(
  () => {
    getSpecialties();
    getPayForms();
    getCompanies();
    getCitizenship();
    getExamsFilters();
    getAchievementsFilters();
    getEducations();
    getSpecialRights();
  },
);
watch(
  [selectedSpecialties, selectedYearApplication, selectedApplicationStatus],
  ([specialtiesValue, yearValue, applicationsValue]) => {
    const result = {
      specialties: specialtiesValue,
      year: yearValue,
      applications: applicationsValue,
    };
    emit('changeFilters', result);
  },
);
</script>

<style lang="scss" scoped>
.four-col {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-bottom: 5px;
}
.margin {
  margin: 5px 10px;
}
.flex {
  display: flex;
  flex-wrap: wrap;
}
.input-checkbox {
  margin: auto 0;
  height: 20px;
  vertical-align: middle;
}
.label-for-checkbox {
  margin: auto 10px auto 0;
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
