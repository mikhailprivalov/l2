<template>
  <div class="flex">
    <template v-if="!right">
      <button
        class="btn"
        :class="light ? 'btn-blue-nb-light' : 'btn-blue-nb'"
        @click="decDate"
      >
        <i class="glyphicon glyphicon-arrow-left" />
      </button>
      <button
        class="btn"
        :class="light ? 'btn-blue-nb-light' : 'btn-blue-nb'"
        @click="incDate"
      >
        <i class="glyphicon glyphicon-arrow-right" />
      </button>
    </template>
    <input
      v-model="val"
      v-datepicker
      type="text"
      class="form-control no-context"
      :class="{brn: brn}"
      :style="{ width: w }"
      maxlength="10"
    >
    <template v-if="right">
      <button
        class="btn btn-blue-nb"
        @click="decDate"
      >
        <i class="glyphicon glyphicon-arrow-left" />
      </button>
      <button
        class="btn btn-blue-nb"
        @click="incDate"
      >
        <i class="glyphicon glyphicon-arrow-right" />
      </button>
    </template>
  </div>
</template>

<script lang="ts">
import moment from 'moment';

export default {
  name: 'DateFieldNav',
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
    light: {
      default: false,
      type: Boolean,
    },
  },
  data() {
    return {
      val: this.def,
      el: null,
    };
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
