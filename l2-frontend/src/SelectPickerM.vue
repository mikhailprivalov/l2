<template>
  <select v-selectpicker ref="self" class="selectpicker" data-width="100%" data-none-selected-text="Ничего не выбрано"
          data-select-all-text="Выбрать всё" data-deselect-all-text="Отменить весь выбор"
          :data-live-search="search"
          data-container="body">
    <option :value="option.value" v-for="option in options" :selected="option.value === value">{{ option.label }}
    </option>
  </select>
</template>

<script>
  export default {
    name: 'select-picker-m',
    props: {
      options: {
        type: Array,
        required: true
      },
      value: {},
      search: {
        required: false,
        type: Boolean,
        default: false,
      }
    },
    methods: {
      update_val(v) {
        this.$emit('input', v)
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
          if (this.elc)
          this.elc.selectpicker('val', v)
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
          if (this.elc)
          this.elc.selectpicker('val', this.value)
        },
      },
    },
    created() {
      this.update_val(this.value)
    },
    directives: {
      selectpicker: {
        bind(el, binding, vnode) {
          let $el = $(el).parent().children('select')
          let v = vnode.context.value
          if (v === '-1' || !v) {
            if (vnode.context.multiple)
              v = []
            else if (vnode.context.options.length > 0)
              v = vnode.context.options[0].value
            else
              v = ''
          }
          if (vnode.context.multiple && !Array.isArray(v)) {
            v = v.split(',')
          } else if (!vnode.context.multiple && typeof v !== 'string' && !(v instanceof String)) {
            v = v.toString()
          }
          $el.selectpicker('val', v)
          vnode.context.update_val(v)
          $(el).change(function () {
            let lval = $(this).selectpicker('val')
            vnode.context.update_val(lval)
          })
        },
        inserted(el, binding, vnode) {
          $(el).selectpicker()
          vnode.context.elc = $(el)
        }
      }
    }
  }
</script>
