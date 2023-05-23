<template>
  <div class="input-group">
    <span
      v-if="!disabled && canEdit"
      class="input-group-btn"
    >
      <button
        v-tippy
        type="button"
        class="btn btn-default btn-primary-nb btn30"
        title="Рассчитать значение"
        @click="directiveCalc"
      >
        <i class="fa fa-circle" />
      </button>
    </span>
    <input
      :key="n"
      v-model="content"
      class="form-control"
      :readonly="disabled || !canEdit"
      placeholder="Расчётное поле"
    >
  </div>
</template>

<script lang="ts">
import { CalculateFormula } from '../utils';

export default {
  name: 'FormulaField',
  props: ['value', 'fields', 'formula', 'patient', 'canEdit', 'disabled'],
  data() {
    return {
      content: this.value,
      n: 0,
    };
  },
  computed: {
    func_formula() {
      return this.calc();
    },
    f_obj() {
      return this.fields.reduce((a, b) => ({ ...a, [b.pk]: b }), {});
    },
  },
  watch: {
    patient: {
      handler() {
        this.reactiveCalc();
      },
      deep: true,
      immediate: true,
    },
    fields: {
      handler() {
        this.reactiveCalc();
      },
      deep: true,
    },
    value() {
      this.content = this.value;
    },
    content: {
      handler() {
        this.$emit('input', this.content);
      },
      immediate: true,
    },
    func_formula() {
      if (!this.canEdit && !this.disabled) {
        this.content = this.func_formula.toString();
      }
    },
  },
  methods: {
    reactiveCalc() {
      if (!this.canEdit && !this.disabled) {
        this.content = this.calc();
      }
    },
    directiveCalc() {
      if (!this.disabled) {
        const val = this.calc();
        this.content = val;
        this.n++;
      }
    },
    calc() {
      return CalculateFormula(this.f_obj, this.formula, this.patient);
    },
  },
};
</script>
