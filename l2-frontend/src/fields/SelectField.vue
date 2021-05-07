<template>
  <select :disabled="disabled" v-model="val">
    <option :value="v" :key="v" v-for="v in variantsLocal">
      {{ v }}
    </option>
  </select>
</template>

<script>
export default {
  props: {
    value: {
      required: false,
    },
    variants: {
      required: true,
    },
    disabled: {
      required: false,
      default: false,
      type: Boolean,
    },
  },
  data() {
    return {
      val: this.value,
      variantsLocal: [],
    };
  },
  watch: {
    val() {
      this.changeValue(this.val);
    },
    variants: {
      immediate: true,
      handler() {
        this.variantsLocal = Array.isArray(this.variants) ? this.variants : this.variants.split('\n');
        if ((!this.val || !this.variantsLocal.includes(this.val)) && this.variantsLocal.length > 0) {
          // eslint-disable-next-line prefer-destructuring
          this.val = this.variantsLocal[0];
        }
      },
    },
  },
  model: {
    event: 'modified',
  },
  methods: {
    changeValue(newVal) {
      this.$emit('modified', newVal);
    },
  },
};
</script>
