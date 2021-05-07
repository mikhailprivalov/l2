<template>
  <input v-datepicker type="text" class="form-control no-context" v-model="val" maxlength="10"/>
</template>

<script>
export default {
  name: 'date-field-2',
  props: {
    value: {
      type: String,
      required: false,
      default: '',
    },
  },
  data() {
    return {
      val: this.def,
    };
  },
  created() {
    this.val = this.value;
  },
  watch: {
    value() {
      this.val = this.value;
    },
    val() {
      this.$emit('input', this.val);
    },
  },
  directives: {
    datepicker: {
      bind(el, binding, vnode) {
        window.$(el).datepicker({
          format: 'dd.mm.yyyy',
          todayBtn: 'linked',
          language: 'ru',
          autoclose: true,
          todayHighlight: true,
          enableOnReadonly: true,
          orientation: 'top left',
        }).on('changeDate', () => {
          // eslint-disable-next-line no-param-reassign
          vnode.context.val = window.$(el).val();
          vnode.context.$emit('update:val', window.$(el).val());
        });
      },
    },
  },
};
</script>

<style scoped>
  .form-control {
    padding-left: 2px;
    padding-right: 2px;
    text-align: center;
  }
</style>
