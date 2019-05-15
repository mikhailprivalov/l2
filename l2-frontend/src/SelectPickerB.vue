<template>
  <div :class="{'no-border-left': noBorderLeft === 'true'}">
    <select v-model="lv" ref="sel" class="selectpicker"
            :disabled="disabled"
            data-width="100%" data-container="body" data-none-selected-text="Ничего не выбрано">
      <option :value="option.value" v-for="option in options">{{ option.label }}</option>
    </select>
  </div>
</template>

<script>
  export default {
    name: 'select-picker-b',
    props: {
      options: {
        type: Array,
        required: true
      },
      value: {},
      noBorderLeft: {
        type: String,
        default: 'false'
      },
      disabled: {
        type: Boolean,
        required: false,
        default: false,
      }
    },
    data() {
      return {
        inited: false,
        lv: '-1'
      }
    },
    watch: {
      options() {
        if (this.inited) {
          this.resync()
        }
      },
      disabled() {
        if (this.inited) {
          this.resync()
        }
      },
      value() {
        if (this.options.length > 0 && !this.inited) {
          this.init_el()
          this.inited = true
        }
        if (this.inited) {
          this.lv = this.value
        }
      },
      lv() {
        this.update_val(this.lv)
      }
    },
    methods: {
      update_val(v) {
        this.$emit('input', v)
      },
      resync() {
        let $el = this.jel
        setTimeout(function () {
          $el.selectpicker('refresh')
        }, 5)
      },
      init_el() {
        let $el = this.jel

        let v = this.value
        if (v === '-1' || !v) {
          if (this.options.length > 0)
            v = this.options[0].value
          else
            v = ''
        }
        if (this.multiple && !Array.isArray(v)) {
          v = v.split(',')
        } else if (!this.multiple && typeof v !== 'string' && !(v instanceof String)) {
          v = v.toString()
        }
        $el.selectpicker()
        $el.selectpicker('val', v)
        this.update_val(v)
        let vm = this
        $($el).change(function () {
          let lval = $(this).selectpicker('val')
          vm.update_val(lval)
        })
        this.resync()
      },
    },
    created() {
      this.update_val(this.value)
      this.$root.$on('resync', this.resync)
    },
    computed: {
      jel() {
        return $(this.$refs.sel)
      }
    }
  }
</script>

<style>
  .no-border-left .bootstrap-select .btn {
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
  }
</style>
