<template>
  <select v-selectpicker ref="self" class="selectpicker" data-width="100%" :data-none-selected-text="noneText"
          data-select-all-text="Выбрать всё" data-deselect-all-text="Отменить весь выбор"
          :data-live-search="search"
          :disabled="disabled"  :multiple="multiple" :data-actions-box="actions_box"
          data-container="body">
    <option :value="option.value" v-for="option in options" :key="option.value" :selected="option.value === value">
      {{ option.label }}
    </option>
  </select>
</template>

<script>
export default {
  name: 'select-picker-m',
  props: {
    options: {
      type: Array,
      required: true,
    },
    value: {},
    search: {
      required: false,
      type: Boolean,
      default: false,
    },
    disabled: {
      required: false,
      type: Boolean,
      default: false,
    },
    noneText: {
      type: String,
      default: 'Ничего не выбрано',
    },
    uid: {
      type: String,
      default: 'default',
    },
    multiple: {
      type: Boolean,
      default: false,
    },
    actions_box: {
      type: Boolean,
      default: false,
    },
  },
  mounted() {
    this.$root.$on(`update-sp-m-${this.uid}`, () => {
      this.refresh();
    });
  },
  methods: {
    update_val(v) {
      this.$emit('input', v);
    },
    refresh() {
      if (this.elc) {
        this.elc.selectpicker('render');
        this.elc.selectpicker('refresh');
      }
    },
  },
  data() {
    return {
      elc: null,
    };
  },
  watch: {
    value: {
      handler(v) {
        if (this.elc) this.elc.selectpicker('val', v);
      },
      deep: true,
      immediate: true,
    },
    disabled: {
      handler(v) {
        if (this.elc) {
          this.elc.prop('disabled', v);
        }
        this.refresh();
      },
      deep: true,
      immediate: true,
    },
    options: {
      handler() {
        this.$forceUpdate();
      },
      deep: true,
    },
    elc: {
      handler() {
        if (this.elc) this.elc.selectpicker('val', this.value);
      },
    },
  },
  created() {
    this.update_val(this.value);
  },
  directives: {
    selectpicker: {
      bind(el, binding, vnode) {
        const $el = window.$(el).parent().children('select');
        let v = vnode.context.value;
        if (v === '-1' || !v) {
          if (vnode.context.multiple) v = [];
          else if (vnode.context.options.length > 0) v = vnode.context.options[0].value;
          else v = '';
        }
        if (vnode.context.multiple && !Array.isArray(v)) {
          v = v.split(',');
        } else if (!vnode.context.multiple && typeof v !== 'string' && !(v instanceof String)) {
          v = v.toString();
        }
        $el.selectpicker('val', v);
        vnode.context.update_val(v);
        window.$(el).change(function () {
          const lval = window.$(this).selectpicker('val');
          vnode.context.update_val(lval);
        });
      },
      inserted(el, binding, vnode) {
        window.$(el).selectpicker();
        // eslint-disable-next-line no-param-reassign
        vnode.context.elc = window.$(el);
      },
    },
  },
};
</script>
