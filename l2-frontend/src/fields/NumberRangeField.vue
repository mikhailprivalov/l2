<template>
  <div>
    <template v-if="!disabled">
      <input type="range" v-model="val" :min="min" :max="max" :step="step"/>
      <span>{{val}}&nbsp;{{units}}</span>
    </template>
    <template v-else>
      <span>{{val}}</span>
    </template>
  </div>
</template>

<script>
export default {
  props: {
    value: {
      required: false,
    },
    variants: {
      required: true,
    },
    disabled: {
      required: false,
      default: false,
      type: Boolean,
    },
  },
  data() {
    return {
      val: !this.disabled ? (this.value || '34').split(' ')[0] : this.value,
      min: 34,
      max: 42,
      step: 0.1,
      units: '°C',
    };
  },
  watch: {
    val: {
      handler() {
        if (this.disabled) {
          return;
        }
        this.changeValue((`${this.val} ${this.units}`).trim());
      },
      immediate: true,
    },
    disabled(_, pv) {
      if (this.disabled) {
        if (!pv) {
          this.val = (`${this.val} ${this.units}`).trim();
        }
        return;
      }
      // eslint-disable-next-line prefer-destructuring
      this.val = (this.value || '34').split(' ')[0];
    },
    variants: {
      handler() {
        if (this.disabled) {
          return;
        }
        const l = this.variants.length;
        if (l > 0) {
          this.min = Number(this.variants[0]) || 34;
        }
        if (l > 1) {
          this.max = Number(this.variants[1]) || 42;
        }
        if (l > 2) {
          this.step = Number(this.variants[2]) || 0.1;
        }
        if (l > 3) {
          this.units = (this.variants[3] || this.variants[3] === '') ? this.variants[3] : '°C';
        }
      },
      immediate: true,
    },
  },
  model: {
    event: 'modified',
  },
  methods: {
    changeValue(newVal) {
      this.$emit('modified', newVal);
    },
  },
};
</script>

<style scoped lang="scss">
  div {
    padding: 3px;
  }

  input {
    max-width: 250px;
    display: inline-block;
  }

  input, span {
    vertical-align: middle;
  }
</style>
