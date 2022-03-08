<template>
  <select
    v-model="val"
    :disabled="disabled"
    class="form-control"
    :class="fullWidth && 'fullWidth'"
  >
    <option
      v-for="v in variants"
      :key="v.pk"
      :value="v.pk"
    >
      {{ v.title }}
    </option>
  </select>
</template>

<script lang="ts">
export default {
  model: {
    event: 'modified',
  },
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
    fullWidth: {
      required: false,
      default: false,
      type: Boolean,
    },
  },
  data() {
    return {
      val: this.value,
    };
  },
  watch: {
    value() {
      this.val = this.value;
    },
    val() {
      this.changeValue(this.val);
    },
  },
  mounted() {
    this.fixVal();
  },
  methods: {
    changeValue(newVal) {
      this.$emit('modified', newVal);
    },
    fixVal() {
      if ((!this.val || !this.variants.map((v) => v.pk).includes(this.val)) && this.variants.length > 0) {
        this.val = this.variants[0].pk;
      }
    },
  },
};
</script>

<style lang="scss" scoped>
.fullWidth {
  width: 100%;
}
</style>
