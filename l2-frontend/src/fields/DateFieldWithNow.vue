<template>
  <div v-frag>
    <div class="input-group" v-if="showNow">
      <span class="input-group-btn" v-if="!disabled">
        <button type="button"
                @click="setNow"
                class="btn btn-default btn-primary-nb btn30"
                title="Сегодня"
                v-tippy>
          <i class="fa fa-circle"></i>
        </button>
      </span>
      <input type="date" class="form-control no-context" v-model="val" :disabled="disabled"/>
    </div>
    <input v-else type="date" class="form-control no-context full" v-model="val" :disabled="disabled"/>
  </div>
</template>

<script>
import moment from 'moment';

export default {
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
  data() {
    return {
      val: this.value,
    };
  },
  model: {
    event: 'modified',
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
