<template>
  <span class="plan-due">
    <select
      class="form-control due-kind"
      disabled
      :value="row.dueKind"
    >
      <option value="absolute">
        Дата
      </option>
      <option value="employment">
        От даты приема на работу
      </option>
    </select>
    <input
      v-if="row.dueKind !== 'employment'"
      class="form-control due-date"
      type="date"
      readonly
      :value="row.dueDate"
    >
    <span
      v-else
      class="offset"
    >
      <input
        class="form-control offset-value"
        type="number"
        readonly
        :value="row.offsetValue ?? ''"
      >
      <select
        class="form-control offset-unit"
        disabled
        :value="row.offsetUnit"
      >
        <option value="days">
          дни
        </option>
        <option value="months">
          месяцы
        </option>
        <option value="years">
          годы
        </option>
      </select>
    </span>
  </span>
</template>

<script setup lang="ts">
defineProps<{
  row: {
    dueKind: 'absolute' | 'employment';
    dueDate: string;
    offsetValue: number | null;
    offsetUnit: string;
  };
}>();
</script>
