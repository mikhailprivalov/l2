<template>
  <div class="base" :class="{fullWidth}">
    <a href="#" @click.prevent="changeValue(v)" :class="{ active: v === val, disabled }"
       v-for="v in variants">
      <span>{{ v }}</span>
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
                type: Array,
            },
            disabled: {
                required: false,
                default: false,
                type: Boolean,
            },
            fullWidth: {
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
                            this.val = this.value
                        }
                    }, 0)
                },
                immediate: true,
            }
        },
        data() {
            return {
                val: this.value,
            }
        },
        mounted() {
            if ((!this.val || this.val === '' || !this.variants.includes(this.val)) && this.variants.length > 0) {
                this.changeValue(this.variants[0])
            }
        },
        model: {
            event: `modified`
        },
        methods: {
            changeValue(newVal) {
                if (this.disabled) {
                    return
                }
                this.val = newVal
                this.$emit('modified', newVal)
            },
        }
    }
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
      background-color: #AAB2BD;
      color: #fff;

      &:hover:not(.disabled) {
        background-color: #434a54;
      }

      &.active {
        background: #049372 !important;
        color: #fff;
      }

      &.disabled {
        cursor: not-allowed;
        opacity: .8;
      }

      span {
        display: block;
        text-overflow: ellipsis;
        overflow: hidden;
        word-break: keep-all;
        max-height: 2.2em;
        line-height: 1.1em;
        margin: 0 auto;
      }
    }
  }
</style>
