<template>
  <div
    v-if="values.length > 0 && !confirmed && ![10, 12, 18, 19, 21, 24, 25, 26, 27, 28, 39, 42, 44].includes(field_type)"
    class="field-inputs"
  >
    <div class="input-values-wrap">
      <div class="input-values">
        <div class="inner-wrap">
          <div
            v-for="(val, i) in values"
            :key="`${val}_${i}`"
            class="input-value"
            @click="appendValue(val)"
          >
            {{ val }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

type UpdateValueFn = (v: string) => void;

const props = defineProps<{
  update_value: UpdateValueFn;
  value: unknown;
  values: unknown[];
  confirmed?: boolean;
  field_type?: number;
  field_title?: string;
}>();

const localValue = computed(() => String(props.value));

const appendValue = (value: string) => {
  let addVal = value;
  const val = localValue.value;
  if (addVal !== ',' && addVal !== '.') {
    if (val.length > 0 && val[val.length - 1] !== ' ' && val[val.length - 1] !== '\n') {
      if (val[val.length - 1] === '.') {
        addVal = addVal.replace(/./, addVal.charAt(0).toUpperCase());
      }
      addVal = ` ${addVal}`;
    } else if (
      (val.length === 0 || (val.length >= 2 && val[val.length - 2] === '.' && val[val.length - 1] === '\n'))
      && props.field_title === ''
    ) {
      addVal = addVal.replace(/./, addVal.charAt(0).toUpperCase());
    }
  }
  props.update_value(val + addVal);
};
</script>
