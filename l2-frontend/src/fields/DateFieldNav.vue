<template>
  <div class="flex">
    <template v-if="!right">
      <button class="btn btn-blue-nb" @click="decDate"><i class="glyphicon glyphicon-arrow-left"></i></button>
      <button class="btn btn-blue-nb" @click="incDate"><i class="glyphicon glyphicon-arrow-right"></i></button>
    </template>
    <input v-datepicker type="text" class="form-control no-context" :class="{brn: brn}" :style="{ width: w }"
           v-model="val" maxlength="10"/>
    <template v-if="right">
      <button class="btn btn-blue-nb" @click="decDate"><i class="glyphicon glyphicon-arrow-left"></i></button>
      <button class="btn btn-blue-nb" @click="incDate"><i class="glyphicon glyphicon-arrow-right"></i></button>
    </template>
  </div>
</template>

<script>
import moment from 'moment';

export default {
  name: 'date-field-nav',
  props: {
    def: {
      type: String,
      required: false,
      default: '',
    },
    w: {
      default: '94px',
    },
    brn: {
      default: true,
      type: Boolean,
    },
    right: {
      default: false,
      type: Boolean,
    },
  },
  computed: {
    md() {
      return moment(this.val, 'DD.MM.YYYY');
    },
  },
  methods: {
    decDate() {
      const a = this.md.clone();
      a.subtract(1, 'days');
      this.emit(a);
    },
    incDate() {
      const a = this.md.clone();
      a.add(1, 'days');
      this.emit(a);
    },
    emit(v) {
      this.emitf(v.format('DD.MM.YYYY'));
      this.el.datepicker('update', v.toDate());
    },
    emitf(v) {
      this.val = v;
      this.$emit('update:val', v);
    },
  },
  data() {
    return {
      val: this.def,
      el: null,
    };
  },
  directives: {
    datepicker: {
      bind(el, binding, vnode) {
        // eslint-disable-next-line no-param-reassign
        vnode.context.el = window.$(el);
        window.$(el).datepicker({
          format: 'dd.mm.yyyy',
          todayBtn: 'linked',
          language: 'ru',
          autoclose: true,
          todayHighlight: true,
          enableOnReadonly: true,
          orientation: 'top left',
        }).on('changeDate', () => {
          vnode.context.emitf(window.$(el).val());
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
    border-radius: 0;
  }

  .brn {
    border: none;
  }

  .btn {
    border-radius: 0;
  }

  .flex {
    display: flex;
  }
</style>
