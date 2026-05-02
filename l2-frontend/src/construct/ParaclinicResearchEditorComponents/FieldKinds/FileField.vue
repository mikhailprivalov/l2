<template>
  <div>
    <div class="section">
      <div class="file-form-row">
        <label class="file-form-field--small">Минимум файлов
          <input
            v-model.number="formSettings.minFiles"
            class="form-control"
            type="number"
            min="0"
          >
        </label>
        <label class="file-form-field--small">Максимум файлов
          <input
            v-model.number="formSettings.maxFiles"
            class="form-control"
            type="number"
            min="1"
          >
        </label>
        <label class="file-form-field--medium">
          Максимальный размер одного файла, МБ
          <input
            v-model.number="formSettings.maxFileSizeMb"
            class="form-control"
            type="number"
            min="1"
          >
        </label>
        <label class="file-form-field--medium">
          Максимальный суммарный размер, МБ
          <input
            v-model.number="formSettings.maxTotalSizeMb"
            class="form-control"
            type="number"
            min="1"
          >
        </label>
      </div>
      <label>
        Разрешенные расширения
        <Treeselect
          v-model="formSettings.allowedExtensions"
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
            v-model="formSettings.filenamePattern"
            class="form-control"
            placeholder="^report_.*\\.pdf$"
          >
        </label>

        <label class="file-form-field--full">
          Описание правила имени
          <input
            v-model="formSettings.filenamePatternDescription"
            class="form-control"
            placeholder="Файл должен начинаться с report_"
          >
        </label>
      </div>
    </div>
    <div class="section">
      <label>
        <input
          v-model="formSettings.rulesEnabled"
          type="checkbox"
        >
        Включить правила состава файлов
      </label>

      <div v-if="formSettings.rulesEnabled">
        <label class="rules-mode">
          <span>Режим правил</span>
          <Treeselect
            v-model="formSettings.rulesMode"
            :options="rulesMode"
            class="treeselect-29px rules-mode-select"
            :clearable="false"
          />
        </label>

        <div
          v-for="(variant, variantIndex) in formSettings.rulesVariants"
          :key="variantIndex"
          class="rule-variant"
        >
          <div class="rule-variant--header">
            <strong>Вариант {{ variantIndex + 1 }}</strong>

            <button
              v-if="formSettings.rulesVariants.length > 1"
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
          v-if="formSettings.rulesVariants.length === 0 || formSettings.rulesMode === 'oneOf'"
          type="button"
          class="btn btn-blue-nb rule-variant--add"
          @click="addRuleVariant"
        >
          {{ formSettings.rulesVariants.length === 0 ? 'Добавить правило' : 'Добавить вариант' }}
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

import { FileFieldConstructorSettings, SelectOption } from
  '@/construct/ParaclinicResearchEditorComponents/types/FileField';
import { FileFieldSettings } from '@/types/Descriptive/Fields/FileField';

const props = defineProps<{
  value: FileFieldSettings | null
  settings: FileFieldConstructorSettings | null
}>();

const emit = defineEmits<{(e: 'input', value: FileFieldSettings): void
}>();

const getDefaultAllowedExtensions = (): string[] => {
  const availableExtensionsSet = new Set(props.settings?.fileFieldAllowedExtensions ?? []);
  const defaultExtensions = props.settings?.fileFieldDefaultSettings?.allowed_extensions ?? [];

  return defaultExtensions.filter((extension) => availableExtensionsSet.has(extension));
};

const createDefaultSettings = (): FileFieldSettings => {
  const backendDefaults = props.settings?.fileFieldDefaultSettings;

  return {
    minFiles: backendDefaults?.min_files ?? 1,
    maxFiles: backendDefaults?.max_files ?? 1,
    maxFileSizeMb: backendDefaults?.max_file_size_mb ?? 20,
    maxTotalSizeMb: backendDefaults?.max_total_size_mb ?? 50,
    allowedExtensions: getDefaultAllowedExtensions(),

    filenamePattern: '',
    filenamePatternDescription: '',
    strictFilename: false,

    rulesEnabled: false,
    rulesMode: 'exact',
    rulesVariants: [],
  };
};

const formSettings = reactive<FileFieldSettings>({
  ...createDefaultSettings(),
  ...(props.value ?? {}),
});

const availableExtensions = computed<SelectOption[]>(() => (
  props.settings?.fileFieldAllowedExtensions ?? []
).map((extension) => ({
  id: extension,
  label: extension,
})));

const rulesMode = ref<SelectOption[]>([
  { id: 'exact', label: 'Точный набор' },
  { id: 'oneOf', label: 'Один из вариантов' },
]);

const ruleExtensionsOptions = computed<SelectOption[]>(() => formSettings.allowedExtensions.map((extension) => ({
  id: extension,
  label: extension,
})));

watch(
  () => [...formSettings.allowedExtensions],
  (allowedExtensions) => {
    formSettings.rulesVariants = formSettings.rulesVariants
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
  () => formSettings.rulesMode,
  (newMode, oldMode) => {
    if (oldMode === 'oneOf' && newMode === 'exact' && formSettings.rulesVariants.length > 1) {
      formSettings.rulesVariants.splice(1);
    }
  },
);

watch(
  formSettings,
  (value) => {
    emit('input', JSON.parse(JSON.stringify(value)));
  },
  { deep: true },
);

const addRuleVariant = () => {
  formSettings.rulesVariants.push({
    items: [
      {
        extension: null,
        count: 1,
      },
    ],
  });
};

const removeRuleVariant = (index: number) => {
  formSettings.rulesVariants.splice(index, 1);
};

const addRuleItem = (variantIndex: number) => {
  formSettings.rulesVariants[variantIndex].items.push({
    extension: null,
    count: 1,
  });
};

const removeRuleItem = (variantIndex: number, itemIndex: number) => {
  const variant = formSettings.rulesVariants[variantIndex];

  variant.items.splice(itemIndex, 1);

  if (variant.items.length === 0) {
    formSettings.rulesVariants.splice(variantIndex, 1);
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
