<template>
  <div
    class="group"
    style="border-radius: 5px"
  >
    <div class="row custom-row">
      <div
        class="col-xs-4"
        style="padding-left: 0"
      >
        <div class="attached-group">
          <TreeSelect
            v-model="selectedTemplate"
            :options="templates"
            placeholder="Выберите шаблон"
            :max-height="150"
            :clearable="false"
            class="attached-select"
          />
          <button
            class="btn btn-blue-nb attached-button"
            type="button"
            :disabled="!selectedTemplate"
            @click="getTemplateData"
          >
            Загрузить шаблон
          </button>
        </div>
      </div>

      <div class="col-xs-4">
        <div class="center-wrapper">
          <label>Шаблоны лекарственных препаратов</label>
        </div>
      </div>

      <div
        class="col-xs-4"
        style="padding-right: 0"
      >
        <div
          class="attached-group"
          style="margin-top: 1px"
        >
          <input
            v-model="templateTitle"
            class="form-control attached-input"
            placeholder="Наименование шаблона"
          >
          <button
            class="btn btn-blue-nb attached-button"
            type="button"
            :disabled="!templateTitle"
            @click="updateTemplate"
          >
            Сохранить шаблон
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import TreeSelect from '@riophae/vue-treeselect';
import moment from 'moment/moment';
import {
  getCurrentInstance, onMounted, ref,
} from 'vue';
import { POSITION } from 'vue-toastification/src/ts/constants';

import * as actions from '@/store/action-types';
import api from '@/api';
import { useStore } from '@/store';

const store = useStore();
const root = getCurrentInstance().proxy.$root;
const emit = defineEmits(['template-data']);

const props = defineProps({
  value: {
    type: Array,
    default: () => [],
  },
});

const TOAST_TYPES = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info',
};

const showToast = (message, type = TOAST_TYPES.SUCCESS, options = {}) => {
  const defaultOptions = {
    position: POSITION.BOTTOM_RIGHT,
    timeout: 5000,
    closeOnClick: true,
    pauseOnHover: true,
    icon: true,
  };

  const finalOptions = { ...defaultOptions, ...options };

  root.$toast[type](message, finalOptions);
};

const templates = ref(null);
const selectedTemplate = ref(null);
const selectedTemplateData = ref(null);
const templateTitle = ref('');

const getTemplates = async () => {
  await store.dispatch(actions.INC_LOADING);
  const templatesData = await api('procedural-list/get-drug-templates');
  templates.value = templatesData.data;
  await store.dispatch(actions.DEC_LOADING);
};

const getTemplateData = async () => {
  await store.dispatch(actions.INC_LOADING);
  const response = await api('procedural-list/get-drug-template', { template_id: selectedTemplate.value });
  selectedTemplateData.value = response.data;
  await store.dispatch(actions.DEC_LOADING);

  selectedTemplateData.value.forEach((row) => {
    const data = {
      pk: Math.random() + Math.random(),
      isNew: true,
      remove: false,
      drug: row.drug.title,
      drugPk: row.drug.pk,
      timesSelected: row.times,
      form_release: row.form_release,
      method: row.method,
      dosage: row.dosage,
      step: row.step,
      dateStart: moment().format('YYYY-MM-DD'),
      dateEnd: null,
      countDays: row.days_count,
      units: row.units,
      comment: row.comment,
    };
    emit('template-data', data);
  });
};

const validateRows = () => {
  const rowsToAdd = ref([]);
  const checkRows = ref([]);

  props.value.forEach((row) => {
    if (!row.remove) {
      checkRows.value.push(row);
    }
  });

  if (!props.value || checkRows.value.length === 0) {
    showToast('Нельзя сохранить пустой шаблон', TOAST_TYPES.ERROR);
    return null;
  }

  const isValid = props.value.every(row => {
    if (row.remove) return true;
    return row.form_release > 0
         && row.method > 0
         && row.units !== null
         && row.timesSelected?.length > 0;
  });

  if (!isValid) {
    showToast('Одна из строк не соответствует условиям', TOAST_TYPES.ERROR);
    return null;
  }

  props.value.forEach((row) => {
    if (!row.remove) {
      rowsToAdd.value.push(row);
    }
  });

  return rowsToAdd;
};

const updateTemplate = async () => {
  const validatedRows = validateRows();

  if (!validatedRows) {
    return;
  }

  try {
    const response = await api('procedural-list/update-drug-template', {
      template_title: templateTitle.value,
      rows: validatedRows.value,
    });

    // eslint-disable-next-line no-prototype-builtins
    if (response.hasOwnProperty('message')) {
      await getTemplates();
      showToast(response.message, TOAST_TYPES.SUCCESS);
      // eslint-disable-next-line no-prototype-builtins
    } else if (response.hasOwnProperty('error')) {
      showToast(response.error, TOAST_TYPES.ERROR);
    }
  } catch {
    showToast('Ошибка при изменении шаблона', TOAST_TYPES.ERROR);
  }
};

onMounted(() => {
  getTemplates();
});

</script>

<style scoped lang="scss">
.center-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  min-height: 34px;
  margin-top: 5px;
}
.custom-row {
  padding: 5px;
  margin-left: 0;
  margin-right: 0;
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);
}
.attached-group {
  display: flex;
  width: 100%;

  > :first-child:not(:only-child) {
    border-top-right-radius: 0;
    border-bottom-right-radius: 0;
  }

  > :last-child:not(:only-child) {
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
  }

  .attached-select,
  .attached-input {
    flex: 1 1 auto;
    min-width: 0;
    position: relative;
    z-index: 2;

    &:not(:only-child) {
      border-right: none;

      &:focus {
        border-right: 1px solid #66afe9;
        outline: none;
        box-shadow: inset 0 1px 1px rgba(0,0,0,.075), 0 0 8px rgba(102, 175, 233, .6);
        z-index: 3;
      }
    }
  }

  .attached-button {
    flex: 0 0 auto;
    white-space: nowrap;
    margin-left: -1px;
    position: relative;
    z-index: 1;

    @media (max-width: 1200px) {
      font-size: 0.9rem;
      padding-left: 8px;
      padding-right: 8px;
    }

    @media (max-width: 992px) {
      font-size: 0.8rem;
      padding-left: 6px;
      padding-right: 6px;
    }

    @media (max-width: 768px) {
      font-size: 0.75rem;
      padding-left: 4px;
      padding-right: 4px;
    }

    &:hover {
      z-index: 4;
    }
  }
}

:deep(.vue-treeselect__control) {
  border: 1px solid #989898;
  border-top-left-radius: 5px;
  border-bottom-left-radius: 5px;
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
  min-height: 34px;

  border-right: none;

  &:hover {
    border-right: none;
  }
}

:deep(.vue-treeselect--focused .vue-treeselect__control) {
  border-right: 1px solid #66afe9;
  box-shadow: inset 0 1px 1px rgba(0,0,0,.075), 0 0 8px rgba(102, 175, 233, .6);
  z-index: 3;
}

.attached-input {
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;

  &:focus {
    border-right: 1px solid #66afe9;
    z-index: 3;
  }
}

@media (max-width: 480px) {
  .attached-group {
    flex-direction: column;

    > :first-child:not(:only-child) {
      border-top-right-radius: 4px;
      border-bottom-right-radius: 0;
      border-bottom-left-radius: 0;
    }

    > :last-child:not(:only-child) {
      border-top-left-radius: 0;
      border-top-right-radius: 0;
      border-bottom-left-radius: 4px;
      border-bottom-right-radius: 4px;
    }

    .attached-select,
    .attached-input {
      border-right: 1px solid #ccc;
      border-bottom: none;

      &:focus {
        border-right: 1px solid #66afe9;
        border-bottom: none;
      }
    }

    .attached-button {
      margin-left: 0;
      margin-top: -1px;
      width: 100%;
    }
  }
}
</style>
