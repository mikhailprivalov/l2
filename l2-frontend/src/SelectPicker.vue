<template>
  <select v-selectpicker class="selectpicker" v-model="val" data-width="100%" @change="func">
    <option v-bind:value="option.value" v-for="option in options">{{ option.label }}</option>
  </select>
</template>

<script>
  export default {
    name: 'select-picker',
    props: ['options', 'val', 'func'],
    directives: {
      selectpicker: {
        twoWay: true,

        bind(el, binding, vnode) {
          let $el = $(el)
          $el.on('change', () => {
            vnode.context.func($el.val())
          })
        }
      }
    }
  }
</script>
