<template>
  <select v-selectpicker v-model="name" data-width="100%" @change="func">
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

        bind() {
          console.log('bind')
          $(this.$el).selectpicker()

          $(this.$el).on('change', function (e) {
            this.set($(this.$el).val())
          }.bind(this))
        },

        update(newValue) {
          console.log('update')
          $(this.$el).val(newValue)
          $(this.$el).selectpicker('val', newValue)
        },

        unbind() {
          console.log('unbind')
          $(this.$el).selectpicker('destroy')
        }
      }
    }
  }
</script>
