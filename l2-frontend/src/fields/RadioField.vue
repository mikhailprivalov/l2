<template>
  <div class="base" :class="{fullWidth, redesigned}">
    <a href="#" @click.prevent="changeValue(v)" :class="{ active: v === val, disabled }"
       :key="v"
       v-for="v in variantsLocal">
      <span>{{ v }} <span class="badge badge-warning" v-if="Boolean(bages[v])">{{ bages[v] }}</span></span>
    </a>
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
    redesigned: {
      required: false,
      default: false,
      type: Boolean,
    },
    fullWidth: {
      required: false,
      default: false,
      type: Boolean,
    },
    bages: {
      type: Object,
      required: false,
      default: () => ({}),
    },
  },
  watch: {
    value: {
      handler() {
        setTimeout(() => {
          if (this.value !== this.val) {
            this.val = this.value;
          }
        }, 0);
      },
      immediate: true,
    },
    variants: {
      immediate: true,
      handler() {
        this.variantsLocal = Array.isArray(this.variants) ? this.variants : this.variants.split('\n');
        if ((!this.val || !this.variantsLocal.includes(this.val)) && this.variantsLocal.length > 0) {
          // eslint-disable-next-line prefer-destructuring
          this.val = this.variantsLocal[0];
          this.changeValue(this.val);
        }
      },
    },
  },
  data() {
    return {
      val: this.value,
      variantsLocal: [],
    };
  },
  model: {
    event: 'modified',
  },
  methods: {
    changeValue(newVal) {
      if (this.disabled) {
        return;
      }
      this.val = newVal;
      this.$emit('modified', newVal);
    },
  },
};
</script>

<style scoped lang="scss">
.base {
  height: 34px;
  overflow: hidden;
  display: flex;
  flex-wrap: wrap;
  justify-content: stretch;
  align-content: stretch;
  align-items: stretch;
  overflow-y: auto;

  &.fullWidth {
    width: calc(100% - 119px);
  }

  a {
    align-self: stretch;
    display: flex;
    align-items: center;
    padding: 1px 2px 1px;
    text-decoration: none;
    cursor: pointer;
    flex: 1;
    margin: 0;
    font-size: 12px;
    min-width: 0;

    &.disabled {
      cursor: not-allowed;
      opacity: .8;
    }

    > span {
      display: block;
      text-overflow: ellipsis;
      overflow: hidden;
      word-break: keep-all;
      max-height: 2.2em;
      line-height: 1.1em;
      margin: 0 auto;
    }
  }

  &:not(.redesigned) a {
    background-color: #AAB2BD;
    color: #fff;

    &:hover:not(.disabled) {
      background-color: #434a54;
    }

    &.active {
      background: #049372 !important;
      color: #fff;
    }
  }

  &.redesigned a {
    color: #000;
    padding: 0 2px;
    text-align: center;
    margin: 3px;
    display: block;
    cursor: pointer;
    border-radius: 3px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
    transition: all 0.2s ease-in-out;
    border-top: 3px solid #fff;
    border-bottom: 3px solid #fff;

    &.active {
      color: #049372 !important;
      background-color: #ECF0F1;
      box-shadow: 0 3px 6px rgba(0, 0, 0, 0.16), 0 3px 6px rgba(0, 0, 0, 0.23);
    }

    &:nth-of-type(1).active {
      border-top: 3px solid #049372;
      border-bottom: 3px solid #049372;
    }

    &:nth-of-type(2).active {
      border-top: 3px solid #93046d;
      border-bottom: 3px solid #93046d;
    }

    &:nth-of-type(3).active {
      border-top: 3px solid #932a04;
      border-bottom: 3px solid #932a04;
    }

    &:hover {
      box-shadow: 0 5px 10px rgba(0, 0, 0, 0.19), 0 6px 6px rgba(0, 0, 0, 0.23);
      background-color: #fafafa;
    }

    span {
      line-height: 22px;
      font-size: 16px;
      font-weight: bold;
    }
  }
}
</style>
