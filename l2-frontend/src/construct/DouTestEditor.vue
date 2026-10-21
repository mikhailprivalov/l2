<template>
  <div class="root">
    <div class="top-editor">
      <div class="left">
        <div class="input-group">
          <div class="field-slot">
            <span class="input-group-addon">Название</span>
            <input
              v-model="title"
              type="text"
              class="form-control"
            >
          </div>
        </div>
      </div>
    </div>
    <div class="test-settings">
      <div class="setting-row">
        <span class="setting-label">Порядок вопросов</span>
        <select
          v-model="orderMode"
          class="form-control setting-select"
        >
          <option value="sequential">
            Последовательный
          </option>
          <option value="random">
            Произвольный
          </option>
        </select>
      </div>
      <div class="setting-row">
        <span class="setting-label">Количество вопросов</span>
        <select
          v-model="limitMode"
          class="form-control setting-select"
        >
          <option value="all">
            Все
          </option>
          <option value="count">
            Количество
          </option>
        </select>
        <input
          v-if="limitMode === 'count'"
          v-model.number="questionLimit"
          type="number"
          min="1"
          :max="questionCount || 1"
          class="form-control setting-number"
        >
      </div>
      <div class="setting-row">
        <span class="setting-label">Вопросы</span>
        <select
          v-model="questionPick"
          class="form-control setting-select"
        >
          <option value="all">
            Все
          </option>
          <option value="random">
            Произвольно
          </option>
        </select>
        <span class="question-count">Вопросов: {{ questionCount }}</span>
      </div>
    </div>
    <div class="content-editor">
      <div
        v-for="question in orderedQuestions"
        :key="question.clientKey"
        class="ed-group"
      >
        <div class="question-row">
          <span class="question-label">Вопрос</span>
          <input
            v-model="question.text"
            type="text"
            class="form-control"
            placeholder="Текст вопроса"
          >
          <button
            class="btn btn-blue-nb"
            type="button"
            @click="removeQuestion(question)"
          >
            Удалить
          </button>
        </div>
        <div
          v-for="answer in orderedAnswers(question.answers)"
          :key="answer.clientKey"
          class="answer-row"
        >
          <label class="correct">
            <input
              v-model="answer.isCorrect"
              type="checkbox"
            >
            Правильный
          </label>
          <input
            v-model="answer.text"
            type="text"
            class="form-control"
            placeholder="Вариант ответа"
          >
          <button
            class="btn btn-blue-nb"
            type="button"
            @click="removeAnswer(question, answer)"
          >
            Удалить
          </button>
        </div>
        <button
          class="btn btn-blue-nb add-row"
          type="button"
          @click="addAnswer(question)"
        >
          Добавить вариант
        </button>
      </div>
      <button
        class="btn btn-blue-nb add-row"
        type="button"
        @click="addQuestion"
      >
        Добавить вопрос
      </button>
    </div>
    <div class="footer-editor">
      <button
        class="btn btn-blue-nb"
        type="button"
        @click="loadExcel"
      >
        Загрузить
      </button>
      <div class="footer-actions">
        <button
          class="btn btn-blue-nb"
          type="button"
          @click="emit('cancel')"
        >
          Отмена
        </button>
        <button
          class="btn btn-blue-nb"
          type="button"
          @click="save"
        >
          Сохранить
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed, getCurrentInstance, ref, watch,
} from 'vue';

import api from '@/api';
import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import { selectFile } from '@/utils';

interface AnswerRow {
  clientKey: number;
  text: string;
  isCorrect: boolean;
  order: number;
}

interface QuestionRow {
  clientKey: number;
  text: string;
  order: number;
  answers: AnswerRow[];
}

interface AnswerPayload {
  text?: string;
  isCorrect?: boolean;
  order?: number;
}

interface QuestionPayload {
  text?: string;
  order?: number;
  answers?: AnswerPayload[];
}

const props = defineProps<{
  testId: number;
}>();

// eslint-disable-next-line no-spaced-func, func-call-spacing
const emit = defineEmits<{
  (e: 'saved', payload: { id: number }): void;
  (e: 'cancel'): void;
}>();

const store = useStore();
const root = getCurrentInstance().proxy.$root;
const title = ref('');
const questions = ref<QuestionRow[]>([]);
const orderMode = ref<'sequential' | 'random'>('sequential');
const limitMode = ref<'all' | 'count'>('all');
const questionLimit = ref<number | null>(null);
const questionPick = ref<'all' | 'random'>('all');
let nextKey = 1;

const questionCount = computed(() => questions.value.length);

const orderedQuestions = computed(() => [...questions.value].sort((a, b) => a.order - b.order));
const orderedAnswers = (rows: AnswerRow[]) => [...rows].sort((a, b) => a.order - b.order);

const addAnswer = (question: QuestionRow) => {
  const order = question.answers.reduce((max, row) => Math.max(max, row.order), 0) + 1;
  nextKey += 1;
  question.answers.push({
    clientKey: nextKey,
    text: '',
    isCorrect: false,
    order,
  });
};

const removeAnswer = (question: QuestionRow, answer: AnswerRow) => {
  const index = question.answers.findIndex(row => row.clientKey === answer.clientKey);
  if (index >= 0) {
    question.answers.splice(index, 1);
  }
};

const addQuestion = () => {
  const order = questions.value.reduce((max, row) => Math.max(max, row.order), 0) + 1;
  nextKey += 1;
  const question: QuestionRow = {
    clientKey: nextKey,
    text: '',
    order,
    answers: [],
  };
  addAnswer(question);
  questions.value.push(question);
};

const removeQuestion = (question: QuestionRow) => {
  questions.value = questions.value.filter(row => row.clientKey !== question.clientKey);
};

const mapAnswer = (row: AnswerPayload, index: number): AnswerRow => {
  nextKey += 1;
  return {
    clientKey: nextKey,
    text: row.text || '',
    isCorrect: !!row.isCorrect,
    order: row.order ?? index,
  };
};

const applyQuestions = (rows: QuestionPayload[]) => {
  questions.value = (rows || []).map((question, index) => {
    nextKey += 1;
    return {
      clientKey: nextKey,
      text: question.text || '',
      order: question.order ?? index,
      answers: (question.answers || []).map(mapAnswer),
    };
  });
};

const applySettings = (data: { orderMode?: string; questionLimit?: number | null; questionPick?: string }) => {
  orderMode.value = data.orderMode === 'random' ? 'random' : 'sequential';
  questionPick.value = data.questionPick === 'random' ? 'random' : 'all';
  if (data.questionLimit == null) {
    questionLimit.value = null;
    limitMode.value = 'all';
    return;
  }
  questionLimit.value = Number(data.questionLimit);
  limitMode.value = 'count';
};

const load = async () => {
  title.value = '';
  questions.value = [];
  applySettings({});
  await store.dispatch(actions.INC_LOADING);
  try {
    const data = await api('document-manager/tests/details', { id: props.testId });
    if (!data?.ok) {
      root.$emit('msg', 'error', data?.message || 'Тест не найден');
      return;
    }
    title.value = data.title || '';
    applySettings(data);
    applyQuestions(data.questions || []);
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const save = async () => {
  if (limitMode.value === 'count' && (!questionLimit.value || questionLimit.value < 1)) {
    root.$emit('msg', 'error', 'Укажите количество вопросов');
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/tests/update', {
      id: props.testId,
      title: title.value,
      orderMode: orderMode.value,
      questionLimit: limitMode.value === 'count' ? questionLimit.value : null,
      questionPick: questionPick.value,
      questions: orderedQuestions.value.map((question, index) => ({
        text: question.text,
        order: index,
        answers: orderedAnswers(question.answers).map((answer, answerIndex) => ({
          text: answer.text,
          isCorrect: answer.isCorrect,
          order: answerIndex,
        })),
      })),
    });
    if (result?.ok) {
      root.$emit('msg', 'ok', 'Сохранено');
      emit('saved', { id: result.id });
    } else {
      root.$emit('msg', 'error', result?.message || 'Ошибка сохранения');
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const loadExcel = async () => {
  const file = await selectFile('.xlsx');
  if (!file) {
    return;
  }
  const name = (file.name || '').toLowerCase();
  if (!name.endsWith('.xlsx')) {
    root.$emit('msg', 'error', 'Нужен файл .xlsx');
    return;
  }
  const formData = new FormData();
  formData.append('file', file);
  await store.dispatch(actions.INC_LOADING);
  try {
    const result = await api('document-manager/tests/import', null, null, null, formData);
    if (!result?.ok) {
      root.$emit('msg', 'error', result?.message || 'Не удалось прочитать файл');
      return;
    }
    applyQuestions(result.questions || []);
    root.$emit('msg', 'ok', 'Файл загружен');
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

watch(limitMode, (mode) => {
  if (mode === 'count' && (questionLimit.value == null || questionLimit.value < 1)) {
    questionLimit.value = Math.max(questionCount.value, 1);
  }
});

watch(() => props.testId, load, { immediate: true });
</script>

<style scoped lang="scss">
.root {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  height: 100%;
  background-color: #f8f7f7;
}

.top-editor {
  display: flex;
  flex: 0 0 34px;
  align-self: stretch;
  width: 100%;
  min-width: 0;
  height: 34px;

  .left {
    flex: 1 1 auto;
    width: 100%;
    min-width: 0;
  }

  .input-group {
    display: flex !important;
    flex-wrap: nowrap;
    align-items: stretch;
    width: 100%;
    margin-bottom: 0;
    height: 34px;
  }

  .input-group-addon {
    display: flex !important;
    align-items: center;
    flex: 0 0 auto;
    float: none !important;
    width: auto;
    height: 34px;
    padding: 0 10px;
    line-height: 22px;
    font-size: 14px;
    font-weight: normal;
    color: #fff;
    white-space: nowrap;
    background-color: #aab2bd;
    border-top: none;
    border-left: none;
    border-right: none;
    border-bottom: 1px solid #96a0ad;
    border-radius: 0;
  }

  .form-control {
    flex: 1 1 0;
    float: none !important;
    width: auto !important;
    min-width: 0;
    height: 34px;
    padding: 0 10px;
    line-height: 22px;
    font-size: 14px;
    color: #434a54;
    border-top: none;
    border-left: 1px solid #96a0ad;
    border-right: none;
    border-bottom: 1px solid #96a0ad;
    border-radius: 0;
    display: block !important;
    box-shadow: none;
  }

  .field-slot {
    display: flex;
    flex: 1 1 0;
    min-width: 0;
    align-items: stretch;
  }
}

.test-settings {
  flex: 0 0 auto;
  background-color: #f0f0f0;
  border-bottom: 1px solid #b1b1b1;
}

.setting-row {
  display: flex;
  align-items: stretch;
  min-width: 0;
  border-bottom: 1px solid #d0d0d0;

  &:last-child {
    border-bottom: none;
  }
}

.setting-label,
.question-count {
  display: flex;
  align-items: center;
  flex: 0 0 auto;
  height: 34px;
  padding: 0 10px;
  line-height: 22px;
  font-size: 14px;
  white-space: nowrap;
}

.setting-label {
  flex-basis: 190px;
  color: #fff;
  background-color: #aab2bd;
}

.setting-select,
.setting-number {
  flex: 0 0 180px;
  width: 180px;
  height: 34px;
  border-radius: 0;
  box-shadow: none;
}

.setting-number {
  flex-basis: 90px;
  width: 90px;
}

.question-count {
  margin-left: auto;
  color: #434a54;
}

.content-editor {
  flex: 1;
  padding: 5px;
  overflow-y: auto;
}

.ed-group {
  padding: 5px;
  margin: 5px;
  background: #f0f0f0;
}

.question-row {
  display: flex;
  align-items: stretch;
  width: 100%;
  min-width: 0;
  margin-bottom: 0;

  .question-label,
  .form-control,
  .btn {
    height: 34px;
    border-radius: 0;
  }

  .question-label {
    display: flex;
    align-items: center;
    flex: 0 0 auto;
    padding: 0 10px;
    line-height: 22px;
    font-size: 14px;
    color: #fff;
    white-space: nowrap;
    background-color: #aab2bd;
    border: 1px solid #96a0ad;
    border-right: none;
  }

  .form-control {
    flex: 1 1 0;
    float: none !important;
    width: auto !important;
    min-width: 0;
    box-shadow: none;
  }

  .btn {
    flex: 0 0 auto;
    float: none;
    white-space: nowrap;
  }
}

.answer-row {
  display: flex;
  align-items: stretch;
  margin-top: 5px;
  min-width: 0;

  .form-control {
    flex: 1 1 0;
    float: none !important;
    width: auto !important;
    min-width: 0;
    height: 34px;
    border-radius: 0;
    box-shadow: none;
  }

  .btn {
    flex: 0 0 auto;
    float: none;
    height: 34px;
    border-radius: 0;
    white-space: nowrap;
  }
}

.correct {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 0 0 auto;
  height: 34px;
  margin: 0;
  padding: 0 10px;
  font-weight: normal;
  color: #434a54;
  white-space: nowrap;
  background-color: #fff;
  border: 1px solid #ccc;
  border-right: none;
}

.add-row {
  margin-top: 5px;
}

.footer-editor {
  flex: 0 0 34px;
  display: flex;
  justify-content: space-between;
  background-color: #f4f4f4;
  border-top: 1px solid #b1b1b1;

  .btn {
    border-radius: 0;
    height: 34px;
    white-space: nowrap;
  }
}

.footer-actions {
  display: flex;
}
</style>
