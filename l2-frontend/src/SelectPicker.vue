<template>
  <select v-selectpicker class="selectpicker" data-width="100%" :multiple="multiple" :data-actions-box="actions_box" data-none-selected-text="Ничего не выбрано" data-select-all-text="Выбрать всё"
          data-deselect-all-text="Отменить весь выбор">
    <option v-bind:value="option.value" v-for="option in options">{{ option.label }}</option>
  </select>
</template>

<script>
  export default {
    name: 'select-picker',
    props: {
      options: {
        type: Array,
        required: true
      },
      val: {},
      func: {
        type: Function,
        required: true
      },
      multiple: {
        type: Boolean,
        default: false
      },
      actions_box: {
        type: Boolean,
        default: false
      }
    },
    methods: {
      update_val(v) {
        this.func(v)
      }
    },
    created() {
      this.update_val(this.val)
    },
    directives: {
      selectpicker: {
        bind(el, binding, vnode) {
          let $el = $(el).parent().children('select')
          let v = vnode.context.val
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
        }
      }
    }
  }
</script>
