<template>
  <div class="custom-form-container">
    <formulate-form
      v-model="formValues"
      :debounce="100"
      @input="onInput"
    >
      <div class="form-grid">
        <div class="form-col">
          <FormulateInput
            type="text"
            name="clinic"
            label="Клиника"
            placeholder="Введите клинику"
          />
        </div>
        <div class="form-col">
          <!-- TODO -->
        </div>
      </div>
    </formulate-form>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import isEqual from 'lodash/isEqual';

const props = defineProps<{ value: { clinic: string } }>();
// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'input', id: Record<string, any>): void
}>();

const formValues = ref({ ...props.value });

function onInput() {
  emit('input', formValues.value);
}

watch(() => props.value, (val) => {
  if (!isEqual(val, formValues.value)) {
    formValues.value = { ...val };
  }
});
</script>

<style scoped>
.custom-form-container {
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 12px;
  width: 100%;
  margin-top: 12px;
}
.form-grid {
  display: flex;
  gap: 24px;
}
.form-col {
  flex: 1 1 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
@media (max-width: 700px) {
  .form-grid {
    flex-direction: column;
    gap: 0;
  }
  .form-col {
    gap: 12px;
  }
}
</style>
