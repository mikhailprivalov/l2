<template>
  <div class="input-group">
    <input
      class="form-control"
      :value="content"
      readonly
      placeholder="Расчётное поле"
    >
  </div>
</template>

<script lang="ts">
import { CalculateFormula } from '../utils';

export default {
  name: 'FormulaField',
  props: ['value', 'fields', 'formula', 'patient'],
  data() {
    return {
      content: this.value,
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
        this.content = this.calc();
      },
      deep: true,
      immediate: true,
    },
    fields: {
      handler() {
        this.content = this.calc();
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
      this.content = this.func_formula.toString();
    },
  },
  methods: {
    calc() {
      return CalculateFormula(this.f_obj, this.formula, this.patient);
    },
  },
};
</script>
