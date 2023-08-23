<template>
  <div class="main">
    <h4 class="header text-center">
      Абитуриенты
    </h4>
    <div class="margin-div flex-div">
      <button
        class="btn btn-blue-nb button-icon"
        @click="showFilters = !showFilters"
      >
        {{ showFilters ? 'Скрыть' : 'Фильтры' }}
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
            v-model="selectedDestinations"
            :multiple="true"
            :options="destinations"
            placeholder="Выберите направление"
          />
        </div>
        <div class="margin-div">
          <label>Конкурс</label>
          <Treeselect
            v-model="selectedCompetitions"
            :multiple="true"
            :options="competitions"
            placeholder="Выберите конкурс"
          />
        </div>
        <div class="margin-div">
          <label>Заказчик</label>
          <Treeselect
            v-model="selectedCustomers"
            :options="customers"
            placeholder="Выберите заказчика"
          />
        </div>
        <div class="margin-div">
          <label>Статус зачисления</label>
          <Treeselect
            v-model="selectedEnrollmentStatuses"
            :options="enrollmentStatuses"
            placeholder="Выберите статус"
          />
        </div>
        <div class="margin-div">
          <label>Статус отчисления</label>
          <Treeselect
            v-model="selectedDeductionStatuses"
            :options="deductionStatuses"
            placeholder="Выберите статус"
          />
        </div>
        <div class="margin-div">
          <label>Приказ</label>
          <Treeselect
            v-model="selectedCommands"
            :multiple="true"
            :options="commands"
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
            v-model="selectedApplicationSource"
            :multiple="true"
            :options="applicationSources"
            placeholder="Выберите источник"
          />
        </div>
        <div class="margin-div">
          <label>Статус заявлений</label>
          <Treeselect
            v-model="selectedApplicationStatus"
            :multiple="true"
            :options="applicationStatuses"
            placeholder="Выберите статус"
          />
        </div>
        <div class="margin-div">
          <label>Этап заявления</label>
          <Treeselect
            v-model="selectedApplicationStage"
            :options="applicationsStages"
            placeholder="Выберите этап"
          />
        </div>
      </div>
      <div class="four-col-div">
        <div class="margin-div">
          <label>Тип экзамена</label>
          <Treeselect
            v-model="selectedTypeExam"
            :multiple="true"
            :options="typesExam"
            placeholder="Выберите тип"
          />
        </div>
        <div class="margin-div">
          <label>Предмет</label>
          <Treeselect
            v-model="selectedSubject"
            :multiple="true"
            :options="subjects"
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
            v-model="selectedTypeIA"
            :multiple="true"
            :options="typeIA"
            placeholder="Выберите тип"
          />
        </div>
        <div class="margin-div">
          <label>Статус ИД</label>
          <Treeselect
            v-model="selectedIAStatus"
            :multiple="true"
            :options="iAStatuses"
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
            v-model="selectedEducation"
            :multiple="true"
            value-consists-of="LEAF_PRIORITY"
            :options="education"
            placeholder="Выберите тип"
          />
        </div>
        <div class="margin-div">
          <label>Особое право</label>
          <Treeselect
            v-model="selectedSpecialRight"
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
  computed, ref,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import 'vue-easytable/libs/theme-default/index.css';
import EnrolleesTable from '@/pages/Education/EnrolleesTable.vue';


const showFilters = ref(false);

const selectedDestinations = ref([]);
const destinations = ref([
  { id: 1, label: 'Направление 1' },
  { id: 2, label: 'Направление 2' },
  { id: 3, label: 'Направление 3' },
]);
const selectedCompetitions = ref([]);
const competitions = ref([
  { id: 1, label: 'Конкурс 1' },
  { id: 2, label: 'Конкурс 2' },
  { id: 3, label: 'Конкурс 3' },
]);
const selectedCustomers = ref([]);
const customers = ref([
  { id: 1, label: 'Заказчик 1' },
  { id: 2, label: 'Заказчик 2' },
  { id: 3, label: 'Заказчик 3' },
]);
const selectedEnrollmentStatuses = ref([]);
const enrollmentStatuses = ref([
  { id: 1, label: 'Статус зачисления 1' },
  { id: 2, label: 'Статус зачисления 2' },
  { id: 3, label: 'Статус зачисления 3' },
]);
const selectedDeductionStatuses = ref([]);
const deductionStatuses = ref([
  { id: 1, label: 'Статус отчисления 1' },
  { id: 2, label: 'Статус отчисления 2' },
  { id: 3, label: 'Статус отчисления 3' },
]);
const selectedCommands = ref([]);
const commands = ref([
  { id: 1, label: 'Приказ 1' },
  { id: 2, label: 'Приказ 2' },
  { id: 3, label: 'Приказ 3' },
]);

const consent = ref(false);
const activeApplicationOnly = ref(false);
const contract = ref(false);
const payment = ref(false);

const selectedCitizenship = ref([]);
const citizenship = ref([
  { id: 1, label: 'Россия' },
  { id: 2, label: 'Греция' },
  { id: 3, label: 'Китай' },
]);

const selectedApplicationSource = ref([]);
const applicationSources = ref([
  { id: 1, label: 'Лично' },
  { id: 2, label: 'ЕПГУ' },
  { id: 3, label: 'ЛК' },
]);

const selectedApplicationStatus = ref([]);
const applicationStatuses = ref([
  { id: 1, label: 'Статус 1' },
  { id: 2, label: 'Статус 2' },
  { id: 3, label: 'Статус 3' },
]);
const selectedApplicationStage = ref([]);
const applicationsStages = ref([
  { id: 1, label: 'Проверка' },
  { id: 2, label: 'Принято' },
  { id: 3, label: 'Отклонено' },
]);

const selectedTypeExam = ref([]);
const typesExam = ref([]);
const selectedSubject = ref([]);
const subjects = ref([]);
const selectedExamStatus = ref([]);
const examStatuses = ref([]);
const selectedTypeIA = ref([]);
const typeIA = ref([]);
const selectedIAStatus = ref([]);
const iAStatuses = ref([]);
const selectedSatisfactoryBall = ref([]);
const satisfactoryBalls = ref([]);
const selectedEducation = ref([]);
const education = ref([
  {
    id: 1,
    label: 'Среднее общее',
    children: [{ id: 4, label: 'Аттестат школы 9 классов' },
      { id: 5, label: 'Аттестат лицея 9 классов' }],
  },
  { id: 2, label: 'Среднее проф', children: [{ id: 6, label: 'диплом Колледжа' }, { id: 7, label: 'Аттестат Техникума' }] },
  { id: 3, label: 'Высшее' }]);
const isOriginal = ref(false);
const selectedSpecialRight = ref([]);
const specialRights = ref([
  { id: 1, label: 'Инвалид', children: [{ id: 2, label: 'Инвалид 1-й группы' }, { id: 3, label: 'Инвалид 2-й группы' }] },
  { id: 4, label: 'Сирота', children: [{ id: 5, label: 'Сирота1' }, { id: 6, label: 'Сирота2' }] },
]);

const search = ref('');

const enrollees = ref([
  {
    card: 1,
    fio: 'Котова Аделия Ивановна',
    application: '1-СТОМ-ОО',
    сhemistry: 33,
    biology: 43,
    mathematics: 55,
    russian_language: 33,
    ia: 3,
    iaPlus: 3,
    amount: 555,
    is_original: true,
    status: 'Принято',
    create_date: '12.07.2023 16:59',
  },
  {
    card: 2,
    fio: 'Котова2 Аделия2 Ивановна2',
    application: 'ОО-СТОМ-11',
    сhemistry: 33,
    biology: 43,
    mathematics: 55,
    russian_language: 33,
    ia: 3,
    iaPlus: 3,
    amount: 33,
    is_original: false,
    status: 'Принято',
    create_date: '13.07.2023 16:59',
  },
]);

const filteredEnrollees = computed(() => enrollees.value.filter(enrollee => {
  const enrolleeFio = enrollee.fio.toLowerCase();
  const searchTerm = search.value.toLowerCase();

  return enrolleeFio.includes(searchTerm);
}));

const clearFilters = () => {
  selectedDestinations.value = [];
  selectedCompetitions.value = [];
  selectedCustomers.value = [];
  selectedEnrollmentStatuses.value = [];
  selectedDeductionStatuses.value = [];
  selectedCommands.value = [];
  consent.value = false;
  activeApplicationOnly.value = false;
  contract.value = false;
  payment.value = false;
  selectedCitizenship.value = [];
  selectedApplicationSource.value = [];
  selectedApplicationStatus.value = [];
  selectedApplicationStage.value = [];
  selectedTypeExam.value = [];
  selectedSubject.value = [];
  selectedExamStatus.value = [];
  selectedTypeIA.value = [];
  selectedIAStatus.value = [];
  selectedSatisfactoryBall.value = [];
  selectedEducation.value = [];
  isOriginal.value = false;
  selectedSpecialRight.value = [];
};
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
}
.button-icon:hover {
  background-color: #434a54 !important;
  color: #FFFFFF
}
.button-icon:active {
  background-color: #37BC9B !important;
}
</style>
