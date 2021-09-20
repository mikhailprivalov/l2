<template>
  <div class="base">
    <a href="#" @click.prevent="changeValue(v.id)" :class="{ active: v.id === val, disabled }" :key="v.id" v-for="v in variants">
      <span>
        {{ v.label }}
      </span>
    </a>
  </div>
</template>

<script lang="ts">
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
  watch: {
    value: {
      handler() {
        setTimeout(() => {
          if (this.value !== this.val) {
            this.val = this.value;
            this.fixVal();
          }
        }, 0);
      },
      immediate: true,
    },
    variants: {
      immediate: true,
      handler() {
        this.fixVal();
      },
    },
  },
  data() {
    return {
      val: this.value,
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
    fixVal() {
      if ((!this.val || !this.variants.find(v => v.id === this.val)) && this.variants.length > 0) {
        // eslint-disable-next-line prefer-destructuring
        this.val = this.variants[0].id;
        this.changeValue(this.val);
      }
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
  width: 100%;

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
      opacity: 0.8;
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

  a {
    background-color: #aab2bd;
    color: #fff;

    &:hover:not(.disabled) {
      background-color: #434a54;
    }

    &.active {
      background: #049372 !important;
      color: #fff;
    }
  }
}
</style>
