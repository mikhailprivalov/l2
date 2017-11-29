<template>
  <input type="text" class="form-control no-context" v-model="val"/>
</template>

<script>
  export default {
    name: 'date-field',
    props: {
      def: {
        type: String,
        required: false,
        default: ''
      }
    },
    data() {
      return {
        val: this.def
      }
    },
    directives: {
      selectpicker: {
        bind(el, binding, vnode) {
          let $el = $(el)
          $el.datepicker({
            format: 'dd.mm.yyyy',
            language: 'ru',
            autoclose: true,
            todayHighlight: true,
            enableOnReadonly: true,
            orientation: 'top left'
          })
        }
      }
    }
  }
</script>
