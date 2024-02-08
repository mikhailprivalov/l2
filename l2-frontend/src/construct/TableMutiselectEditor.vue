<template>
  <div>
    <table class="table table-condensed table-fixed table-bordered">
      <thead>
        <tr>
          <th style="width: 35%">
            Зависимое значение
          </th>
          <th>Доступный набор значений</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="r in rows"
          :key="`${r.relatedIndex}_${r.index}`"
        >
          <template v-if="r.isAdd">
            <td>
              <button
                type="button"
                class="btn btn-default btn-primary-nb"
                @click="addValue(r.relatedIndex)"
              >
                <i class="fa fa-plus" /> Добавить значение
              </button>
            </td>
          </template>
          <template v-else>
            <td
              v-if="r.index === 0"
              :rowspan="r.count + 1"
            >
              <div
                v-if="!hasLinkedVariants"
                class="input-group"
              >
                <input
                  v-model="r.item.key"
                  type="text"
                  class="form-control"
                  @change="updateJsonValue()"
                >
                <div class="input-group-btn">
                  <button
                    v-tippy="{ placement : 'bottom'}"
                    type="button"
                    class="btn btn-blue-nb"
                    title="Удалить зависимое значение"
                    @click="removeRelatedValue(r.relatedIndex)"
                  >
                    <i class="fa fa-times" />
                  </button>
                </div>
              </div>
              <div v-else>
                <strong>{{ r.item.key }}</strong>
              </div>
            </td>
            <td>
              <div class="input-group">
                <input
                  v-model.trim="r.item.values[r.index]"
                  type="text"
                  class="form-control"
                  @change="updateJsonValue()"
                >
                <div class="input-group-btn">
                  <button
                    v-tippy="{ placement : 'bottom'}"
                    type="button"
                    class="btn btn-blue-nb"
                    title="Удалить значение"
                    @click="removeValue(r.relatedIndex, r.index)"
                  >
                    <i class="fa fa-times" />
                  </button>
                </div>
              </div>
            </td>
          </template>
        </tr>
        <tr v-if="!hasLinkedVariants">
          <td colspan="2">
            <button
              type="button"
              class="btn btn-default btn-primary-nb"
              @click="addRelatedValue"
            >
              <i class="fa fa-plus" /> Добавить зависимое значение
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script lang="ts" setup>
import { computed, ref, watch } from 'vue';

type ModelValue = {
  key: string,
  values: string[],
};

const props = defineProps<{
  value?: ModelValue[],
  linkedVariants?: string,
}>();

const inputValue = computed(() => props.value);

const linkedVariants = computed(() => {
  if (!props.linkedVariants) {
    return [];
  }

  return props.linkedVariants.split('\n');
});

const hasLinkedVariants = computed(() => linkedVariants.value.length > 0);

const modelValue = ref<ModelValue[]>([]);

const setDefaultModelValue = () => {
  if (hasLinkedVariants.value) {
    if (!modelValue.value) {
      modelValue.value = [];
      return true;
    }

    return false;
  }

  if (!Array.isArray(modelValue.value) || modelValue.value.length === 0) {
    modelValue.value = [{ key: '', values: [''] }];
    return true;
  }

  return false;
};

const fixModelValueForLinked = () => {
  if (!hasLinkedVariants.value) {
    return false;
  }

  let needUpdate = false;

  const linkedVariantsSet = new Set(linkedVariants.value);

  for (let i = 0; i < modelValue.value.length; i++) {
    const item = modelValue.value[i];

    if (!linkedVariantsSet.has(item.key)) {
      needUpdate = true;
      modelValue.value.splice(i, 1);
      i--;
    }
  }

  for (let i = 0; i < linkedVariants.value.length; i++) {
    const linkedVariant = linkedVariants.value[i];

    if (!modelValue.value.find((item) => item.key === linkedVariant)) {
      needUpdate = true;
      modelValue.value.push({ key: linkedVariant, values: [''] });
    }
  }

  return needUpdate;
};

const valueJson = ref(JSON.stringify(modelValue.value));

const updateJsonValue = () => {
  valueJson.value = JSON.stringify(modelValue.value);
};

watch(inputValue, (value) => {
  let needUpdate = false;

  modelValue.value = value;

  if (!Array.isArray(modelValue.value)) {
    modelValue.value = [];
    needUpdate = true;
  }

  needUpdate = setDefaultModelValue() || needUpdate;

  for (let i = 0; i < modelValue.value.length; i++) {
    const item = modelValue.value[i];

    if (typeof item.key !== 'string' || !Array.isArray(item.values)) {
      modelValue.value[i] = { key: '', values: [''] };
      needUpdate = true;
    }
  }

  needUpdate = fixModelValueForLinked() || needUpdate;

  if (needUpdate) {
    updateJsonValue();
  }
}, { immediate: true });

watch([linkedVariants, modelValue], () => {
  const needUpdate = fixModelValueForLinked();

  if (needUpdate) {
    updateJsonValue();
  }
}, { immediate: true, deep: true });

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'input', value: ModelValue[]): void
  (e: 'change'): void
}>();

watch(valueJson, () => {
  emit('input', JSON.parse(valueJson.value));
  emit('change');
});

const addRelatedValue = () => {
  modelValue.value.push({ key: '', values: [''] });

  updateJsonValue();
};

const removeRelatedValue = (index: number) => {
  modelValue.value.splice(index, 1);

  updateJsonValue();
};

const addValue = (index: number) => {
  modelValue.value[index].values.push('');

  updateJsonValue();
};

const removeValue = (relatedIndex: string, index: number) => {
  modelValue.value[relatedIndex].values.splice(index, 1);

  if (modelValue.value[relatedIndex].values.length === 0) {
    modelValue.value[relatedIndex].values.push('');
  }

  updateJsonValue();
};

const rows = computed(() => {
  const result = [];

  for (let i = 0; i < modelValue.value.length; i++) {
    const item = modelValue.value[i];
    let lastIndex = 0;

    for (let j = 0; j < item.values.length; j++) {
      result.push({
        item,
        relatedIndex: i,
        index: j,
        count: item.values.length,
      });

      lastIndex = j;
    }

    result.push({
      item,
      relatedIndex: i,
      index: lastIndex + 1,
      count: item.values.length,
      isAdd: true,
    });
  }
  return result;
});
</script>
