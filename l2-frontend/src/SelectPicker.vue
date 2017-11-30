<template>
  <select v-selectpicker class="selectpicker" data-width="100%" @change="func" :multiple="multiple" :data-actions-box="actions_box" data-none-selected-text="Ничего не выбрано" data-select-all-text="Выбрать всё"
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
      val: {
        type: String,
        required: true
      },
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
    directives: {
      selectpicker: {
        bind(el, binding, vnode) {
          console.log(1)
          let $el = $(el)
          console.log(101)
          let v = vnode.context.val
          console.log(102)
          if (v === '-1' || !v)
            v = ''
          if (vnode.context.multiple) {
            console.log(111)
            $el.selectpicker('val', v.split(','))
            console.log(11)
          } else {
            console.log(121)
            $el.selectpicker('val', v)
            console.log(12)
          }
          console.log(2)
          vnode.context.func($el.val())
          console.log(3)
          $el.on('change', () => {
            vnode.context.func($el.val())
            console.log(4)
          })
        }
      }
    }
  }
</script>
