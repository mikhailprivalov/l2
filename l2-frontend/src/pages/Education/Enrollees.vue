<template>
  <div class="main">
    <h4 class="header text-center">
      Абитуриенты
    </h4>
    <div class="margin-div flex-div">
      <button
        v-if="!showFilters"
        class="btn btn-blue-nb button-icon"
        @click="showFilters = !showFilters"
      >
        <i class="fa fa-filter" />
        Показать
      </button>
      <button
        v-else
        class="btn btn-blue-nb button-icon"
        @click="showFilters = !showFilters"
      >
        <i class="fa fa-filter" />
        Скрыть
      </button>
      <button
        class="btn btn-blue-nb button-icon"
        @click="clearFilters"
      >
        Очистить
      </button>
    </div>
    <div v-if="showFilters">
      <div class="four-col-div">
        <div class="margin-div">
          <label>Направление</label>
          <Treeselect
            v-model="selectedSpecialties"
            :multiple="true"
            :options="specialties"
            placeholder="Выберите направление"
          />
        </div>
        <div class="margin-div">
          <label>Основание</label>
          <Treeselect
            v-model="selectedPayForms"
            :multiple="true"
            :options="payForms"
            placeholder="Выберите основание"
          />
        </div>
        <div class="margin-div">
          <label>Заказчик</label>
          <Treeselect
            v-model="selectedCompany"
            :options="companies"
            placeholder="Выберите заказчика"
            :normalizer="normalizerCompany"
          />
        </div>
        <div class="margin-div">
          <label>Статус зачисления</label>
          <Treeselect
            v-model="selectedEnrollmentStatus"
            :options="enrollmentStatuses"
            placeholder="Выберите статус"
          />
        </div>
        <div class="margin-div">
          <label>Статус отчисления</label>
          <Treeselect
            v-model="selectedDeductionStatus"
            :options="deductionStatuses"
            placeholder="Выберите статус"
          />
        </div>
        <div class="margin-div">
          <label>Приказ</label>
          <Treeselect
            v-model="selectedEnrollmentOrders"
            :multiple="true"
            :options="enrollmentOrders"
            placeholder="Выберите приказ"
          />
        </div>
        <div class="margin-div">
          <label>Гражданство</label>
          <Treeselect
            v-model="selectedCitizenship"
            :options="citizenship"
            placeholder="Выберите гражданство"
          />
        </div>
      </div>
      <div class="four-col-div">
        <div class="margin-div">
          <label>Источник заявления</label>
          <Treeselect
            v-model="selectedStatementSources"
            :multiple="true"
            :options="statementSources"
            placeholder="Выберите источник"
          />
        </div>
        <div class="margin-div">
          <label>Статус заявлений</label>
          <Treeselect
            v-model="selectedStatementStatuses"
            :multiple="true"
            :options="statementStatuses"
            placeholder="Выберите статус"
          />
        </div>
        <div class="margin-div">
          <label>Этап заявления</label>
          <Treeselect
            v-model="selectedStatementStage"
            :options="statementStages"
            placeholder="Выберите этап"
          />
        </div>
      </div>
      <div class="four-col-div">
        <div class="margin-div">
          <label>Тип экзамена</label>
          <Treeselect
            v-model="selectedExams"
            :multiple="true"
            :options="exams"
            placeholder="Выберите тип"
          />
        </div>
        <div class="margin-div">
          <label>Предмет</label>
          <Treeselect
            v-model="selectedExamSubjects"
            :multiple="true"
            :options="examSubjects"
            placeholder="Выберите предмет"
          />
        </div>
        <div class="margin-div">
          <label>Статус экзамена</label>
          <Treeselect
            v-model="selectedExamStatus"
            :options="examStatuses"
            placeholder="Выберите статус"
          />
        </div>
        <div class="margin-div">
          <label>Тип ИД</label>
          <Treeselect
            v-model="selectedAchievements"
            :multiple="true"
            :options="achievements"
            placeholder="Выберите тип"
          />
        </div>
        <div class="margin-div">
          <label>Статус ИД</label>
          <Treeselect
            v-model="selectedAchievementsStatuses"
            :multiple="true"
            :options="achievementsStatuses"
            placeholder="Выберите статус"
          />
        </div>
        <div class="margin-div">
          <label>Удовлетворительный балл</label>
          <Treeselect
            v-model="selectedSatisfactoryBall "
            :options="satisfactoryBalls"
            placeholder="Выберите балл"
          />
        </div>
        <div class="margin-div">
          <label>Образование</label>
          <Treeselect
            v-model="selectedEducations"
            :multiple="true"
            value-consists-of="LEAF_PRIORITY"
            :options="educations"
            placeholder="Выберите тип"
          />
        </div>
        <div class="margin-div">
          <label>Особое право</label>
          <Treeselect
            v-model="selectedSpecialRights"
            :multiple="true"
            :options="specialRights"
            value-consists-of="LEAF_PRIORITY"
            placeholder="Выберите право"
          />
        </div>
      </div>
      <div class="four-col-div">
        <div class="margin-div flex-div">
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
        <div class="margin-div flex-div">
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
            >Есть договор</label>
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
        <div class="margin-div flex-div">
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
      </div>
    </div>
    <div>
      <input
        v-model="search"
        placeholder="Поиск"
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
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import 'vue-easytable/libs/theme-default/index.css';
import EnrolleesTable from '@/pages/Education/EnrolleesTable.vue';
import api from '@/api';

const showFilters = ref(false);

const selectedSpecialties = ref([]);
const specialties = ref([]);
const getSpecialties = async () => {
  const data = await api('/education/get-specialties');
  specialties.value = data.result;
};

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

const selectedEnrollmentStatus = ref(null);
const enrollmentStatuses = ref([]);
const getEnrollmentStatuses = async () => {
  const data = await api('/education/get-enrollment-statuses');
  enrollmentStatuses.value = data.result;
};

const selectedDeductionStatus = ref(null);
const deductionStatuses = ref([]);
const getDeductionStatuses = async () => {
  const data = await api('/education/get-deduction-statuses');
  deductionStatuses.value = data.result;
};

const selectedEnrollmentOrders = ref([]);
const enrollmentOrders = ref([]);
const getEnrollmentOrders = async () => {
  const data = await api('/education/get-enrollment-orders');
  enrollmentOrders.value = data.result;
};

const selectedCitizenship = ref(null);
const citizenship = ref([]);
const getCitizenship = async () => {
  const data = await api('/education/get-citizenship');
  citizenship.value = data.result;
};

const selectedStatementSources = ref([]);
const statementSources = ref([]);
const selectedStatementStatuses = ref([]);
const statementStatuses = ref([]);
const selectedStatementStage = ref(null);
const statementStages = ref([]);
const getStatementFilters = async () => {
  const data = await api('/education/get-statement-filters');
  statementSources.value = data.sources;
  statementStatuses.value = data.statuses;
  statementStages.value = data.stages;
};

const selectedExams = ref([]);
const exams = ref([]);
const selectedExamSubjects = ref([]);
const examSubjects = ref([]);
const selectedExamStatus = ref(null);
const examStatuses = ref([]);
const getExamsFilters = async () => {
  const data = await api('/education/get-exams-filters');
  exams.value = data.exams;
  examSubjects.value = data.subjects;
  examStatuses.value = data.statuses;
};

const selectedAchievements = ref([]);
const achievements = ref([]);
const selectedAchievementsStatuses = ref([]);
const achievementsStatuses = ref([]);
const getAchievementsFilters = async () => {
  const data = await api('/education/get-achievements-filters');
  achievements.value = data.achievements;
  achievementsStatuses.value = data.statuses;
};

const selectedSatisfactoryBall = ref(null);
const satisfactoryBalls = ref([]);
const getSatisfactoryBalls = async () => {
  const data = await api('/education/get-satisfactory-balls');
  satisfactoryBalls.value = data.result;
};
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

const search = ref('');

const enrollees = ref([]);
const getEnrollees = async () => {
  const data = await api('/education/get-enrollees');
  enrollees.value = data.result;
};

const filteredEnrollees = computed(() => enrollees.value.filter(enrollee => {
  const enrolleeFio = enrollee.fio.toLowerCase();
  const searchTerm = search.value.toLowerCase();

  return enrolleeFio.includes(searchTerm);
}));

const clearFilters = () => {
  selectedSpecialties.value = [];
  selectedCompany.value = null;
  selectedEnrollmentStatus.value = null;
  selectedDeductionStatus.value = null;
  selectedEnrollmentOrders.value = [];
  consent.value = false;
  activeApplicationOnly.value = false;
  contract.value = false;
  payment.value = false;
  selectedCitizenship.value = null;
  selectedStatementSources.value = [];
  selectedStatementStatuses.value = [];
  selectedStatementStage.value = null;
  selectedExams.value = [];
  selectedExamSubjects.value = [];
  selectedExamStatus.value = null;
  selectedAchievements.value = [];
  selectedAchievementsStatuses.value = [];
  selectedSatisfactoryBall.value = null;
  selectedEducations.value = [];
  isOriginal.value = false;
  selectedSpecialRights.value = [];
};

onMounted(
  () => {
    getSpecialties();
    getPayForms();
    getCompanies();
    getEnrollmentStatuses();
    getDeductionStatuses();
    getEnrollmentOrders();
    getCitizenship();
    getStatementFilters();
    getExamsFilters();
    getAchievementsFilters();
    getSatisfactoryBalls();
    getEducations();
    getSpecialRights();
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
.four-col-div {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-bottom: 5px;
}
.margin-div {
  margin: 5px 10px;
}
.flex-div {
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
.div-checkbox {
  margin: auto 0;
  height: 0;
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
