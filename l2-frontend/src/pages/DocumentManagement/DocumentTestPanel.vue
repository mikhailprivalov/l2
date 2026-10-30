<template>
  <div class="test-panel">
    <div
      v-if="!testId"
      class="empty"
    >
      Выберите тест
    </div>
    <div
      v-else-if="loading"
      class="empty"
    >
      Загрузка...
    </div>
    <div
      v-else-if="!loaded"
      class="empty"
    >
      Тест не найден
    </div>
    <template v-else>
      <div
        v-if="(answerable || review) && confirmed"
        class="score"
      >
        <span>Правильно {{ correct }} из {{ total }}</span>
        <span class="score-percent">{{ percent }}%</span>
      </div>
      <div
        v-if="answerable && !documentId && whoConfirmed"
        class="confirmed-line"
      >
        Подтверждено: {{ whoConfirmed }}
      </div>
      <div class="test-title">
        {{ title }}
      </div>
      <div
        v-if="answerable && (editable || canReset)"
        class="actions"
      >
        <button
          v-if="editable"
          class="btn btn-blue-nb"
          type="button"
          :disabled="saving"
          @click="save(false)"
        >
          Сохранить
        </button>
        <button
          v-if="editable && !confirmed"
          class="btn btn-blue-nb"
          type="button"
          :disabled="saving"
          @click="save(true)"
        >
          Сохранить и подтвердить
        </button>
        <button
          v-if="canReset"
          class="btn btn-blue-nb"
          type="button"
          :disabled="saving"
          @click="resetAttempt"
        >
          Сброс
        </button>
        <span
          v-if="message"
          class="error"
        >{{ message }}</span>
      </div>
      <div
        v-if="questions.length === 0"
        class="empty"
      >
        Вопросов нет
      </div>
      <div
        v-for="(question, index) in questions"
        :key="question.id || index"
        class="question"
      >
        <div class="question-text">
          {{ index + 1 }}. {{ question.text }}
        </div>
        <label
          v-for="answer in question.answers"
          :key="answer.id"
          class="answer"
          :class="answerClass(answer)"
        >
          <input
            v-if="answerable || review"
            type="checkbox"
            class="answer-check"
            :checked="isChecked(answer.id)"
            :disabled="review || !editable || saving"
            @change="toggleAnswer(answer.id)"
          >
          <span class="answer-text">{{ answer.text }}</span>
          <span
            v-if="showCorrect(answer)"
            class="mark"
          >Правильный</span>
        </label>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

import api from '@/api';

interface AnswerRow {
  id: number;
  text: string;
  isCorrect?: boolean;
}

interface QuestionRow {
  id: number;
  text: string;
  answers: AnswerRow[];
}

const props = withDefaults(defineProps<{
  testId: number | null;
  documentId?: number | null;
  answerable?: boolean;
  review?: boolean;
}>(), {
  documentId: null,
  answerable: false,
  review: false,
});

const emit = defineEmits<{(event: 'saved', payload: { confirmed: boolean; whoConfirmed: string }): void}>();

const loading = ref(false);
const loaded = ref(false);
const saving = ref(false);
const title = ref('');
const questions = ref<QuestionRow[]>([]);
const selected = ref<number[]>([]);
const confirmed = ref(false);
const canReset = ref(false);
const editable = ref(false);
const whoConfirmed = ref('');
const correct = ref(0);
const total = ref(0);
const percent = ref(0);
const message = ref('');

const showCorrect = (answer: AnswerRow) => !props.answerable && !props.review && Boolean(answer.isCorrect);

const isChecked = (id: number) => selected.value.includes(id);

const answerClass = (answer: AnswerRow) => {
  if (showCorrect(answer)) {
    return { 'answer--correct': true };
  }
  if (!confirmed.value || answer.isCorrect === undefined || !isChecked(answer.id)) {
    return {};
  }
  return {
    'answer--right': Boolean(answer.isCorrect),
    'answer--wrong': !answer.isCorrect,
  };
};

const toggleAnswer = (id: number) => {
  if (!editable.value || saving.value) {
    return;
  }
  if (selected.value.includes(id)) {
    selected.value = selected.value.filter(row => row !== id);
    return;
  }
  selected.value = [...selected.value, id];
};

const apply = (data) => {
  title.value = data.title || '';
  questions.value = data.questions || [];
  selected.value = Array.isArray(data.selected) ? data.selected.map(Number) : [];
  confirmed.value = Boolean(data.confirmed);
  canReset.value = Boolean(data.canReset);
  editable.value = data.editable === undefined ? !confirmed.value || canReset.value : Boolean(data.editable);
  if (props.review) {
    editable.value = false;
  }
  whoConfirmed.value = data.whoConfirmed || '';
  correct.value = Number(data.correct || 0);
  total.value = Number(data.total || 0);
  percent.value = Number(data.percent || 0);
  message.value = '';
  loaded.value = true;
  emit('saved', { confirmed: confirmed.value, whoConfirmed: whoConfirmed.value });
};

const save = async (confirm: boolean) => {
  if (!props.testId || saving.value || !editable.value) {
    return;
  }
  saving.value = true;
  message.value = '';
  try {
    const data = await api('document-manager/tests/attempt/save', {
      id: props.testId,
      documentId: props.documentId,
      answerIds: selected.value,
      confirm,
    });
    if (!data?.ok) {
      message.value = data?.message || 'Не удалось сохранить';
      return;
    }
    apply(data);
  } finally {
    saving.value = false;
  }
};

const resetAttempt = async () => {
  if (!props.testId || !canReset.value || saving.value) {
    return;
  }
  saving.value = true;
  message.value = '';
  try {
    const data = await api('document-manager/tests/attempt/reset', { id: props.testId });
    if (!data?.ok) {
      message.value = data?.message || 'Не удалось сбросить';
      return;
    }
    apply(data);
  } finally {
    saving.value = false;
  }
};

const load = async () => {
  loaded.value = false;
  title.value = '';
  questions.value = [];
  selected.value = [];
  confirmed.value = false;
  canReset.value = false;
  editable.value = false;
  whoConfirmed.value = '';
  correct.value = 0;
  total.value = 0;
  percent.value = 0;
  message.value = '';
  if (!props.testId) {
    return;
  }
  loading.value = true;
  try {
    let point = 'document-manager/tests/details';
    if (props.answerable || props.review) {
      point = 'document-manager/tests/attempt';
    }
    const data = await api(point, props.documentId ? { documentId: props.documentId } : { id: props.testId });
    if (!data?.ok) {
      return;
    }
    apply(data);
  } finally {
    loading.value = false;
  }
};

watch(() => [props.testId, props.documentId], load, { immediate: true });
</script>

<style scoped lang="scss">
.test-panel {
  height: 100%;
  overflow: auto;
  padding: 8px 10px;
  background: #fff;
}

.empty {
  padding: 10px;
  color: #656d78;
}

.score {
  display: flex;
  align-items: baseline;
  gap: 16px;
  min-height: 34px;
  padding: 6px 0;
  font-size: 16px;
  color: #434a54;
}

.score-percent {
  color: #049372;
}

.confirmed-line {
  padding: 0 0 6px;
  color: #434a54;
}

.test-title {
  min-height: 34px;
  padding: 6px 0;
  font-size: 16px;
  color: #434a54;
}

.actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 4px 0 8px;
}

.error {
  color: #da4453;
}

.question {
  margin-top: 8px;
  border-top: 1px solid #e6e9ed;
}

.question-text {
  padding: 8px 0 4px;
  color: #000;
  font-weight: 700;
}

.answer {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 28px;
  margin: 0;
  padding: 2px 8px;
  color: #434a54;
  font-weight: normal;
}

.answer-check {
  margin: 0;
}

.answer-text {
  font-weight: inherit;
}

.answer--correct {
  background: #e8f6ef;
}

.answer--right {
  color: #049372;
}

.answer--right .answer-check {
  accent-color: #049372;
}

.answer--wrong {
  color: #da4453;
}

.answer--wrong .answer-check {
  accent-color: #da4453;
}

.mark {
  flex: 0 0 auto;
  margin-left: auto;
  color: #049372;
}
</style>
