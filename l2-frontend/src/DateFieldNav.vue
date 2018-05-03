<template>
  <div class="flex">
    <button class="btn btn-blue-nb" @click="decDate">&lAarr;</button>
    <button class="btn btn-blue-nb" @click="incDate">&rAarr;</button>
    <input v-datepicker type="text" class="form-control no-context" :class="{brn: brn}" :style="{ width: w }"
           v-model="val" maxlength="10"/>
  </div>
</template>

<script>
  import moment from 'moment'

  export default {
    name: 'date-field-nav',
    props: {
      def: {
        type: String,
        required: false,
        default: ''
      },
      w: {
        default: '94px'
      },
      brn: {
        default: true,
        type: Boolean
      },
    },
    computed: {
      md() {
        return moment(this.val, 'DD.MM.YYYY')
      }
    },
    methods: {
      decDate() {
        let a = this.md.clone()
        a.subtract(1, 'days')
        this.emit(a)
      },
      incDate() {
        let a = this.md.clone()
        a.add(1, 'days')
        this.emit(a)
      },
      emit(v) {
        this.emitf(v.format('DD.MM.YYYY'))
        this.el.datepicker('update', v.toDate())
      },
      emitf(v) {
        this.val = v
        this.$emit('update:val', v)
      }
    },
    data() {
      return {
        val: this.def,
        el: null
      }
    },
    directives: {
      datepicker: {
        bind(el, binding, vnode) {
          vnode.context.el = $(el)
          $(el).datepicker({
            format: 'dd.mm.yyyy',
            todayBtn: 'linked',
            language: 'ru',
            autoclose: true,
            todayHighlight: true,
            enableOnReadonly: true,
            orientation: 'top left'
          }).on('changeDate', () => {
            vnode.context.emitf($(el).val())
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
