<template>
  <select v-selectpicker class="selectpicker" v-model="val" data-width="100%" @change="func" :multiple="multiple" :data-actions-box="action_box">
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
          let $el = $(el)
          vnode.context.func($el.val())
          $el.on('change', () => {
            vnode.context.func($el.val())
          })
        }
      }
    }
  }
</script>
