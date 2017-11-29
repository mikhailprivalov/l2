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

        bind(el) {
          console.log('bind')
          $(el).selectpicker('refresh')

          $(el).on('change', function (e) {
            this.set($(el).val())
          }.bind(this))
        },

        update(el, newValue) {
          console.log(this, 'update')
          $(el).val(newValue)
          $(el).selectpicker('val', newValue)
        },

        unbind(el) {
          console.log(this, 'unbind')
          $(el).removeClass('selectpicker').selectpicker('destroy')
        }
      }
    }
  }
</script>
