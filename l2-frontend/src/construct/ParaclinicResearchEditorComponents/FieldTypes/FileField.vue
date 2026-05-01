<template>
  <div>
    <div class="section">
      <div class="file-form-row">
        <label class="file-form-field--small">Минимум файлов
          <input
            v-model.number="settings.minFiles"
            class="form-control"
            type="number"
            min="0"
          >
        </label>
        <label class="file-form-field--small">Максимум файлов
          <input
            v-model.number="settings.maxFiles"
            class="form-control"
            type="number"
            min="1"
          >
        </label>
        <label class="file-form-field--medium">
          Максимальный размер одного файла, МБ
          <input
            v-model.number="settings.maxFileSizeMb"
            class="form-control"
            type="number"
            min="1"
          >
        </label>
        <label class="file-form-field--medium">
          Максимальный суммарный размер, МБ
          <input
            v-model.number="settings.maxTotalSizeMb"
            class="form-control"
            type="number"
            min="1"
          >
        </label>
      </div>
      <label>
        Разрешенные расширения
        <Treeselect
          v-model="settings.allowedExtensions"
          :options="availableExtensions"
          class="treeselect-34px"
          placeholder="pdf, xlsx ..."
          :multiple="true"
        />
      </label>
    </div>
    <div class="section">
      <div class="file-form-row">
        <label class="file-form-field--medium">
          Regexp имени файла
          <input
            v-model="settings.filenamePattern"
            class="form-control"
            placeholder="^report_.*\\.pdf$"
          >
        </label>

        <label class="file-form-field--full">
          Описание правила имени
          <input
            v-model="settings.filenamePatternDescription"
            class="form-control"
            placeholder="Файл должен начинаться с report_"
          >
        </label>
      </div>
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
        <label class="rules-mode">
          <span>Режим правил</span>
          <Treeselect
            v-model="settings.rulesMode"
            :options="rulesMode"
            class="treeselect-29px rules-mode-select"
            :clearable="false"
          />
        </label>

        <div
          v-for="(variant, variantIndex) in settings.rulesVariants"
          :key="variantIndex"
          class="rule-variant"
        >
          <div class="rule-variant--header">
            <strong>Вариант {{ variantIndex + 1 }}</strong>

            <button
              v-if="settings.rulesVariants.length > 1"
              class="btn btn-blue-nb rule-variant--delete"
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
              class="btn btn-blue-nb rule-item--delete"
              @click="removeRuleItem(variantIndex, itemIndex)"
            >
              Удалить
            </button>
          </div>

          <button
            class="btn btn-blue-nb rule-item--add"
            @click="addRuleItem(variantIndex)"
          >
            Добавить расширение
          </button>
        </div>

        <button
          v-if="settings.rulesMode === 'oneOf'"
          class="btn btn-blue-nb rule-variant--add"
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
  PropType, reactive, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import { ParaclinicInputFieldRow } from '@/construct/ParaclinicResearchEditorComponents/types/ParaclinicResearcEditor';
import { FileFieldSettings } from '@/construct/ParaclinicResearchEditorComponents/types/FileField';

const props = defineProps({
  row: {
    type: Object as PropType<ParaclinicInputFieldRow>,
    required: true,
  },
});
// availableExtensions придет с бэка
const availableExtensions = ref([
  { id: 'pdf', label: 'pdf' },
  { id: 'docx', label: 'docx' },
  { id: 'xlsx', label: 'xlsx' },
  { id: 'jpeg', label: 'jpeg' },
]);

const rulesMode = ref([
  { id: 'exact', label: 'Точный набор' },
  { id: 'oneOf', label: 'Один из вариантов' },
]);

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

  rulesEnabled: true,
  rulesMode: 'oneOf',
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
.section {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-form-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 6px;
}

.file-form-field--small {
  flex: 0 0 130px;
  margin-bottom: 0;
}

.file-form-field--medium {
  flex: 0 0 260px;
  margin-bottom: 0;
}

.file-form-field--full {
  flex: 1 1 auto;
  margin-bottom: 0;
  min-width: 0;
}

::v-deep .treeselect-34px .vue-treeselect {
  &__control {
    border: 1px solid #aab2bd !important;
  }
}

::v-deep .treeselect-29px .vue-treeselect {
  &__control {
    height: 29px !important;
    border: 1px solid #aab2bd !important;
  }

  &__placeholder,
  &__single-value {
    line-height: 29px !important;
  }
}

.rules-mode {
  display: flex;
  align-items: center;
  gap: 8px;
}
.rules-mode > span {
  white-space: nowrap;
}
.rules-mode-select {
  width: 190px;
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

.rule-variant--header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.rule-variant--delete {
  padding: 4px 8px;
  font-size: 12px;
}

.rule-variant--add {
  padding: 4px 8px;
  font-size: 12px;
}

.rule-item--delete {
  padding: 2px 6px;
  font-size: 11px;
}
.rule-item--add {
  padding: 4px 8px;
  font-size: 12px;
  align-self: flex-start;
}

.rule-item {
  display: flex;
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
