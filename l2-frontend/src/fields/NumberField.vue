<template>
  <input
    v-model="val"
    type="number"
    :readonly="disabled"
    min="-1000"
    max="1000"
    class="form-control"
  >
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
    disabled: {
      required: false,
      default: false,
      type: Boolean,
    },
  },
  data() {
    return {
      val: this.value || 0,
    };
  },
  watch: {
    val: {
      handler() {
        this.changeValue(this.val);
      },
      immediate: true,
    },
  },
  methods: {
    changeValue(newVal) {
      this.$emit('modified', newVal);
    },
  },
};
</script>

<style scoped lang="scss">
  .form-control {
    max-width: 150px;
  }
</style>
