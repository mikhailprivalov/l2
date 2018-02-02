<template>
  <input v-datepicker type="text" class="form-control no-context" v-model="val" maxlength="10"/>
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
          }).on('changeDate', () => {
            vnode.context.val = $(el).val()
            vnode.context.$emit('update:val', $(el).val())
          })
        }
      }
    }
  }
</script>

<style scoped>
  .form-control {
    padding-left: 2px;
    padding-right: 2px;
    text-align: center;
  }
</style>
