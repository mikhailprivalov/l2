<template>
  <div
    :class="{small}"
    class="input-daterange input-group"
  >
    <input
      ref="from"
      v-model.lazy="dfrom"
      class="input-sm form-control no-context"
      type="text"
      maxlength="10"
    >
    <span
      class="input-group-addon"
      style="background-color: #fff;color: #000; height: 34px"
    >&mdash;</span>
    <input
      ref="to"
      v-model.lazy="dto"
      class="input-sm form-control no-context"
      type="text"
      maxlength="10"
    >
  </div>
</template>

<script lang="ts">
import moment from 'moment';

export default {
  name: 'DateRange',
  props: {
    value: {
      type: Array,
      default: () => [new Date(), new Date()],
    },
    small: {
      type: Boolean,
      default: false,
    },
    allowEmpty: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      dfrom: '',
      dto: '',
      syncingFromProp: false,
    };
  },
  computed: {
    datefull() {
      return 'DD.MM.YYYY';
    },
    datesmall() {
      return 'DD.MM.YY';
    },
    datef() {
      return this.small ? this.datesmall : this.datefull;
    },
  },
  watch: {
    value: {
      deep: true,
      handler(newValue) {
        if (!Array.isArray(newValue) || newValue.length < 2) {
          return;
        }
        const [from, to] = newValue;
        if (from === this.dfrom && to === this.dto) {
          return;
        }
        this.syncingFromProp = true;
        this.dfrom = from;
        this.dto = to;
        this.$nextTick(() => {
          this.updateDatepickers(from, to);
          this.syncingFromProp = false;
        });
      },
    },
    dfrom() {
      if (!this.syncingFromProp) {
        this.emit();
      }
    },
    dto() {
      if (!this.syncingFromProp) {
        this.emit();
      }
    },
  },
  created() {
    // eslint-disable-next-line prefer-destructuring
    this.dfrom = this.value[0];
    // eslint-disable-next-line prefer-destructuring
    this.dto = this.value[1];
    this.$root.$on('validate-datepickers', this.validate);
  },
  mounted() {
    window.$(this.$el).datepicker({
      format: this.datef.toLowerCase(),
      todayBtn: 'linked',
      language: 'ru',
      autoclose: true,
      todayHighlight: true,
      orientation: 'top',
    }).on('changeDate', () => {
      if (!window.$(this.$refs.from).is(':focus')) this.$refs.from.dispatchEvent(new Event('change'));
      if (!window.$(this.$refs.to).is(':focus')) this.$refs.to.dispatchEvent(new Event('change'));
    });
  },
  methods: {
    updateDatepickers(from, to) {
      this.updateDatepicker(this.$refs.from, from);
      this.updateDatepicker(this.$refs.to, to);
    },
    updateDatepicker(input, value) {
      if (!input) {
        return;
      }
      const parsed = moment(value, this.datef, true);
      const $input = window.$(input);
      if (parsed.isValid()) {
        $input.datepicker('update', parsed.toDate());
        return;
      }
      if (this.allowEmpty && !String(value || '').trim()) {
        $input.datepicker('update', '');
      }
    },
    emit() {
      this.validate();
      this.$emit('input', [this.dfrom, this.dto]);
    },
    validate_date(date) {
      if (this.allowEmpty && !String(date || '').trim()) {
        return true;
      }
      const r = moment(date, this.datef, true).isValid();

      if (!r) this.$root.$emit('msg', 'error', 'Неверная дата');
      return r;
    },
    validate() {
      let ch = false;
      if (!this.validate_date(this.dfrom)) {
        this.dfrom = moment().format(this.datef);
        window.$(this.$refs.from).datepicker('update', moment().toDate());
        ch = true;
      }
      if (!this.validate_date(this.dto)) {
        this.dto = moment().format(this.datef);
        window.$(this.$refs.to).datepicker('update', moment().toDate());
        ch = true;
      }
      if (ch) {
        window.$(this.$el).datepicker('update');
      }
    },
  },
};
</script>

<style lang="scss" scoped>
  .input-daterange .form-control {
    height: 34px;
    padding: 5px;
    width: 80px;
  }

  .input-daterange.small {
    .form-control {
      height: 34px;
      padding: 1px;
      width: 55px;
      font-size: 10px;
    }

    .input-group-addon {
      padding: 1px;
      font-size: 6px;
    }
  }
</style>
