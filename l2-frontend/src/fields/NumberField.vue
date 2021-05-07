<template>
  <input type="number" v-model="val" :readonly="disabled" min="-1000" max="1000" class="form-control" />
</template>

<script>
export default {
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

<style scoped lang="scss">
  .form-control {
    max-width: 150px;
  }
</style>
