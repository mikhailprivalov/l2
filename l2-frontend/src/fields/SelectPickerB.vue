<template>
  <div :class="{'no-border-left': noBorderLeft === 'true'}">
    <select v-model="lv" ref="sel" class="form-control"
            :disabled="disabled"
            data-width="100%" data-container="body" data-none-selected-text="Ничего не выбрано">
      <option :value="option.value" :key="option.value" v-for="option in options">{{ option.label }}</option>
    </select>
  </div>
</template>

<script>
export default {
  name: 'select-picker-b',
  props: {
    options: {
      type: Array,
      required: true,
    },
    value: {},
    noBorderLeft: {
      type: String,
      default: 'false',
    },
    disabled: {
      type: Boolean,
      required: false,
      default: false,
    },
    strictNotReady: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      inited: false,
      lv: '-1',
      ready: false,
    };
  },
  mounted() {
    this.check_init();
    this.ready = true;
  },
  watch: {
    options() {
      if (this.inited) {
        this.resync();
      }
    },
    disabled() {
      if (this.inited) {
        this.resync();
      }
    },
    value() {
      if (this.inited) {
        this.lv = this.value;
        this.resyncVal(this.lv);
      }
    },
    lv() {
      this.update_val(this.lv);
    },
  },
  methods: {
    check_init() {
      if (!this.inited) {
        if (!this.strictNotReady && this.options.length > 0 && this.lv === '-1') {
          this.inited = true;
          setTimeout(() => this.init_el(), 40);
        } else {
          setTimeout(() => this.check_init(), 40);
        }
      }
    },
    update_val(v) {
      if (this.inited) {
        this.$emit('input', v);
      }
    },
    resync() {
      const $el = this.jel;
      setTimeout(() => {
        $el.selectpicker('refresh');
      }, 5);
    },
    resyncVal(v) {
      if (!this.ready) {
        return;
      }
      const $el = this.jel;
      setTimeout(() => {
        $el.selectpicker('val', v);
      }, 5);
    },
    init_el() {
      const $el = this.jel;

      let v = this.value;
      if (v === '-1' || !v) {
        if (this.options.length > 0) v = this.options[0].value;
        else v = '';
      }
      if (this.multiple && !Array.isArray(v)) {
        v = v.split(',');
      } else if (!this.multiple && typeof v !== 'string' && !(v instanceof String)) {
        v = v.toString();
      }
      $el.selectpicker();
      $el.selectpicker('val', v);
      this.update_val(v);
      window.$($el).change(() => {
        const lval = window.$(this).selectpicker('val');
        this.update_val(lval);
      });
      this.resync();
    },
  },
  created() {
    this.update_val(this.value);
    this.$root.$on('resync', this.resync);
  },
  computed: {
    jel() {
      return window.$(this.$refs.sel);
    },
  },
};
</script>

<style scoped>
  .no-border-left .bootstrap-select .btn {
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
  }

  .form-control {
    opacity: 0;
    height: 38px;
  }
</style>
