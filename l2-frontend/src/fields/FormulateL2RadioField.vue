<template>
  <div
    :class="['formulate-input-element', `formulate-input-element--${context.class}`]"
    :data-type="context.type"
  >
    <RadioFieldById
      :value="modelValue"
      :variants="variants"
      :redesigned="true"
      rounded
      @modified="onModified"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import RadioFieldById from './RadioFieldById.vue';

const props = defineProps<{ context: Record<string, any> }>();
const emit = defineEmits(['update:model']);

const modelValue = computed(() => props.context.model);
const variants = computed(() => props.context.attributes.variants);

function onModified(val: any) {
  emit('update:model', val);
}
</script>
