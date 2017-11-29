<template>
  <input v-datepicker type="text" class="form-control no-context" v-model="val"/>
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
      datepicker: {
        bind(el, binding, vnode) {
          $(el).datepicker({
            format: 'dd.mm.yyyy',
              todayBtn: "linked",
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
