<template>
  <div v-frag>
    <div
      v-if="showNow"
      class="input-group"
    >
      <span
        v-if="!disabled"
        class="input-group-btn"
      >
        <button
          v-tippy
          type="button"
          class="btn btn-default btn-primary-nb btn30"
          title="Сегодня"
          @click="setNow"
        >
          <i class="fa fa-circle" />
        </button>
      </span>
      <input
        v-model="val"
        type="date"
        class="form-control no-context"
        :disabled="disabled"
      >
    </div>
    <input
      v-else
      v-model="val"
      type="date"
      class="form-control no-context full"
      :disabled="disabled"
    >
  </div>
</template>

<script lang="ts">
import moment from 'moment';

export default {
  model: {
    event: 'modified',
  },
  props: {
    value: {
      required: true,
    },
    disabled: {
      required: false,
      default: false,
      type: Boolean,
    },
    showNow: {
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
    value: {
      handler() {
        if (this.value !== this.val) {
          this.val = this.value;
        }
      },
      immediate: true,
    },
    val() {
      this.changeValue();
    },
  },
  methods: {
    changeValue() {
      this.$emit('modified', this.val);
    },
    setNow() {
      this.val = moment().format('YYYY-MM-DD');
    },
  },
};
</script>

<style scoped lang="scss">
.form-control {
  padding-left: 2px;
  padding-right: 2px;

  &:not(.full) {
    width: auto !important;
  }
}
</style>
