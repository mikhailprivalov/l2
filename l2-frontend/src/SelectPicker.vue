<template>
  <select v-model="name" data-width="100%" @change="func">
    <option v-bind:value="option.value" v-for="option in options">{{ option.label }}</option>
  </select>
</template>

<script>
  export default {
    name: 'select-picker',
    props: ['options', 'name', 'func'],
    updated: function () {
      console.log(this)
      $(this.$el).selectpicker('refresh')
    },
    directives: {
      selectpicker: {
        twoWay: true,

        bind() {
          $(this.el).selectpicker()

          $(this.el).on('change', function (e) {
            this.set($(this.el).val())
          }.bind(this))
        },

        update(newValue) {
          $(this.el).val(newValue)
          $(this.el).selectpicker('val', newValue)
        },

        unbind() {
          $(this.el).selectpicker('destroy')
        }
      }
    }
  }
</script>
