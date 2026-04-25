<template>
  <div class="wrapper-component">
    <div class="section">
      <label>Минимум файлов
        <input
          v-model.number="settings.minFiles"
          class="form-control"
          type="number"
          min="0"
        >
      </label>
      <label>Максимум файлов
        <input
          v-model.number="settings.maxFiles"
          class="form-control"
          type="number"
          min="1"
        >
      </label>
      <label>
        Максимальный размер одного файла, МБ
        <input
          v-model.number="settings.maxFileSizeMb"
          class="form-control"
          type="number"
          min="1"
        >
      </label>
      <label>
        Максимальный суммарный размер, МБ
        <input
          v-model.number="settings.maxTotalSizeMb"
          class="form-control"
          type="number"
          min="1"
        >
      </label>
      <label>
        Разрешенные расширения
        <select
          v-model="settings.allowedExtensions"
          class="form-control"
          multiple
        >
          <option
            v-for="extension in availableExtensions"
            :key="extension"
            :value="extension"
          >
            {{ extension }}
          </option>
        </select>
      </label>
    </div>
    <div class="section">
      <label>
        Regexp имени файла
        <input
          v-model="settings.filenamePattern"
          class="form-control"
          placeholder="^report_.*\\.pdf$"
        >
      </label>

      <label>
        Описание правила имени
        <input
          v-model="settings.filenamePatternDescription"
          class="form-control"
          placeholder="Файл должен начинаться с report_"
        >
      </label>

      <label>
        <input
          v-model="settings.strictFilename"
          class="form-control"
          type="checkbox"
        >
        Строго проверять имя файла
      </label>
    </div>
    <div class="section">
      <label>
        <input
          v-model="settings.rulesEnabled"
          type="checkbox"
        >
        Включить правила состава файлов
      </label>

      <div v-if="settings.rulesEnabled">
        <label>
          Режим правил
          <select v-model="settings.rulesMode">
            <option value="exact">Точный набор</option>
            <option value="one_of">Один из вариантов</option>
          </select>
        </label>

        <div
          v-for="(variant, variantIndex) in settings.rulesVariants"
          :key="variantIndex"
          class="rule-variant"
        >
          <div class="rule-variant__header">
            <strong>Вариант {{ variantIndex + 1 }}</strong>

            <button
              v-if="settings.rulesVariants.length > 1"
              type="button"
              @click="removeRuleVariant(variantIndex)"
            >
              Удалить вариант
            </button>
          </div>

          <div
            v-for="(item, itemIndex) in variant.items"
            :key="itemIndex"
            class="rule-item"
          >
            <select
              v-model="item.extension"
              class="rule-item__extension"
            >
              <option
                value=""
                disabled
              >
                Выберите расширение
              </option>

              <option
                v-for="extension in settings.allowedExtensions"
                :key="extension"
                :value="extension"
              >
                {{ extension }}
              </option>
            </select>

            <input
              v-model.number="item.count"
              type="number"
              min="1"
              placeholder="Количество"
            >

            <button
              type="button"
              @click="removeRuleItem(variantIndex, itemIndex)"
            >
              Удалить
            </button>
          </div>

          <button
            type="button"
            @click="addRuleItem(variantIndex)"
          >
            Добавить расширение
          </button>
        </div>

        <button
          v-if="settings.rulesMode === 'one_of'"
          type="button"
          @click="addRuleVariant"
        >
          Добавить вариант
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">

import {
  PropType, reactive, watch,
} from 'vue';

import { ParaclinicInputFieldRow } from '@/construct/ParaclinicResearchEditorComponents/types/ParaclinicResearcEditor';
import { FileFieldSettings } from '@/construct/ParaclinicResearchEditorComponents/types/FileField';

const props = defineProps({
  row: {
    type: Object as PropType<ParaclinicInputFieldRow>,
    required: true,
  },
});
// availableExtensions придет с бэка
const availableExtensions = [
  'pdf',
  'doc',
  'docx',
  'xls',
  'xlsx',
  'jpg',
  'jpeg',
  'png',
  'xml',
  'zip',
];

const settings = reactive<FileFieldSettings>({
  // Сюда настройки из бэкэнда
  minFiles: 0,
  maxFiles: 5,
  maxFileSizeMb: 20,
  maxTotalSizeMb: 100,
  allowedExtensions: ['pdf', 'xlsx', 'docx'],

  checkMime: true,
  blockDoubleExtension: true,
  sanitizeFilename: true,

  filenamePattern: '',
  filenamePatternDescription: '',
  strictFilename: false,

  rulesEnabled: false,
  rulesMode: 'exact',
  rulesVariants: [
    {
      items: [
        {
          extension: '',
          count: 1,
        },
      ],
    },
  ],
});

watch(
  () => [...settings.allowedExtensions],
  (allowedExtensions) => {
    settings.rulesVariants.forEach((variant) => {
      variant.items.forEach((item) => {
        if (item.extension && !allowedExtensions.includes(item.extension)) {
          // eslint-disable-next-line no-param-reassign
          item.extension = '';
        }
      });
    });
  },
);

const addRuleVariant = () => {
  settings.rulesVariants.push({
    items: [
      {
        extension: '',
        count: 1,
      },
    ],
  });
};

const removeRuleVariant = (index: number) => {
  settings.rulesVariants.splice(index, 1);
};

const addRuleItem = (variantIndex: number) => {
  settings.rulesVariants[variantIndex].items.push({
    extension: '',
    count: 1,
  });
};

const removeRuleItem = (variantIndex: number, itemIndex: number) => {
  settings.rulesVariants[variantIndex].items.splice(itemIndex, 1);

  if (settings.rulesVariants[variantIndex].items.length === 0) {
    settings.rulesVariants[variantIndex].items.push({
      extension: '',
      count: 1,
    });
  }
};

</script>

<style scoped lang="scss">
.wrapper-component {
  margin-top: 5px;
}

.section {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rule-variant {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 10px;
  background: #fafafa;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rule-variant__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.rule-item {
  display: flex;
  align-items: center;
  gap: 8px;

  input {
    padding: 4px 6px;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    font-size: 12px;
  }

  input[type="number"] {
    width: 70px;
  }

  input[type="text"] {
    width: 120px;
  }

  button {
    padding: 2px 6px;
    font-size: 11px;
    border: none;
    background: #ef4444;
    color: white;
    border-radius: 4px;
    cursor: pointer;

    &:hover {
      background: #dc2626;
    }
  }
}

button {
  align-self: flex-start;
  padding: 4px 8px;
  font-size: 12px;
  border: none;
  border-radius: 4px;
  background: #3b82f6;
  color: white;
  cursor: pointer;

  &:hover {
    background: #2563eb;
  }
}

select {
  padding: 4px 6px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 12px;
}
.rule-item__extension {
  width: 140px;
}
.rule-item {
  input,
  select {
    padding: 4px 6px;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    font-size: 12px;
  }
}
</style>
