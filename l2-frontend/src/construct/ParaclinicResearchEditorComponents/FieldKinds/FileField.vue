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
              type="button"
              class="btn btn-blue-nb rule-variant--delete"
              @click="removeRuleVariant(variantIndex)"
            >
              Удалить вариант
            </button>
          </div>

          <div class="rule-item rule-item--header">
            <span>Расширение</span>
            <span>Кол-во</span>
            <span />
          </div>

          <div
            v-for="(item, itemIndex) in variant.items"
            :key="itemIndex"
            class="rule-item"
          >
            <Treeselect
              v-model="item.extension"
              :options="ruleExtensionsOptions"
              class="treeselect-29px rule-item--extension"
              placeholder="pdf, xlsx ..."
              :clearable="false"
            />

            <input
              v-model.number="item.count"
              type="number"
              min="1"
              placeholder="Количество"
            >

            <button
              type="button"
              class="btn btn-blue-nb rule-item--delete"
              @click="removeRuleItem(variantIndex, itemIndex)"
            >
              Удалить
            </button>
          </div>

          <button
            type="button"
            class="btn btn-blue-nb rule-item--add"
            @click="addRuleItem(variantIndex)"
          >
            Добавить расширение
          </button>
        </div>

        <button
          v-if="settings.rulesVariants.length === 0 || settings.rulesMode === 'oneOf'"
          type="button"
          class="btn btn-blue-nb rule-variant--add"
          @click="addRuleVariant"
        >
          {{ settings.rulesVariants.length === 0 ? 'Добавить правило' : 'Добавить вариант' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed, reactive, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import { FileFieldSettings, SelectOption } from '@/construct/ParaclinicResearchEditorComponents/types/FileField';

const props = defineProps<{
  value: FileFieldSettings | null
}>();

const emit = defineEmits<{(e: 'input', value: FileFieldSettings): void
}>();

const createDefaultSettings = (): FileFieldSettings => ({
  minFiles: null,
  maxFiles: null,
  maxFileSizeMb: null,
  maxTotalSizeMb: null,
  allowedExtensions: [],

  filenamePattern: '',
  filenamePatternDescription: '',
  strictFilename: false,

  rulesEnabled: false,
  rulesMode: 'exact',
  rulesVariants: [],
});

const settings = reactive<FileFieldSettings>({
  ...createDefaultSettings(),
  ...(props.value ?? {}),
});

// availableExtensions придет с бэка
const availableExtensions = ref<SelectOption[]>([
  { id: 'pdf', label: 'pdf' },
  { id: 'docx', label: 'docx' },
  { id: 'xlsx', label: 'xlsx' },
  { id: 'jpeg', label: 'jpeg' },
]);

const rulesMode = ref<SelectOption[]>([
  { id: 'exact', label: 'Точный набор' },
  { id: 'oneOf', label: 'Один из вариантов' },
]);

const ruleExtensionsOptions = computed<SelectOption[]>(() => settings.allowedExtensions.map((extension) => ({
  id: extension,
  label: extension,
})));

watch(
  () => [...settings.allowedExtensions],
  (allowedExtensions) => {
    settings.rulesVariants = settings.rulesVariants
      .map((variant) => ({
        ...variant,
        items: variant.items.filter(
          (item) => !item.extension || allowedExtensions.includes(item.extension),
        ),
      }))
      .filter((variant) => variant.items.length > 0);
  },
);
watch(
  () => settings.rulesMode,
  (newMode, oldMode) => {
    if (oldMode === 'oneOf' && newMode === 'exact' && settings.rulesVariants.length > 1) {
      settings.rulesVariants.splice(1);
    }
  },
);

watch(
  settings,
  (value) => {
    emit('input', JSON.parse(JSON.stringify(value)));
  },
  { deep: true },
);

const addRuleVariant = () => {
  settings.rulesVariants.push({
    items: [
      {
        extension: null,
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
    extension: null,
    count: 1,
  });
};

const removeRuleItem = (variantIndex: number, itemIndex: number) => {
  const variant = settings.rulesVariants[variantIndex];

  variant.items.splice(itemIndex, 1);

  if (variant.items.length === 0) {
    settings.rulesVariants.splice(variantIndex, 1);
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

.rule-item--add {
  padding: 4px 8px;
  font-size: 12px;
  align-self: flex-start;
}

.rule-item {
  display: grid;
  grid-template-columns: 140px 70px auto;
  gap: 8px;
  align-items: center;

  input,
  select {
    width: 100%;
    padding: 4px 6px;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    font-size: 12px;
  }
}
.rule-item--header {
  font-size: 12px;
  font-weight: 600;
  color: #374151;
  margin-bottom: -4px;
}

.rule-item--delete {
  justify-self: start;
  padding: 2px 6px;
  font-size: 11px;
}

.rule-item--extension {
  width: 100%;
}
</style>
