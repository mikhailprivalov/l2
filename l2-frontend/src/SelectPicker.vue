<template>
  <select v-selectpicker class="selectpicker" v-model="name" data-width="100%" @change="func">
    <option v-bind:value="option.value" v-for="option in options">{{ option.label }}</option>
  </select>
</template>

<script>
  export default {
    name: 'select-picker',
    props: ['options', 'name', 'func'],
    directives: {
      selectpicker: {
        twoWay: true,

        bind(el, binding, vnode) {
          vnode.context.func()
        },

        update(el, binding, vnode) {
          vnode.context.name = binding.value
        }
      }
    }
  }
</script>
