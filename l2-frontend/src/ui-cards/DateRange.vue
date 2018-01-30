<template>
  <div class="input-daterange input-group">
    <input type="text" class="input-sm form-control no-context" style="height: 34px;padding: 5px;width: 80px"
           ref="from" v-model="dfrom" maxlength="10"/>
    <span class="input-group-addon" style="background-color: #fff;color: #000; height: 34px">&mdash;</span>
    <input type="text" class="input-sm form-control no-context" style="height: 34px;padding: 5px;width: 80px"
           ref="to" v-model="dto" maxlength="10"/>
  </div>
</template>

<script>
  export default {
    name: 'date-range',
    props: {
      value: {
        type: Array,
        default: [getFormattedDate(today), getFormattedDate(today)]
      }
    },
    data() {
      return {
        dfrom: '',
        dto: '',
      }
    },
    created() {
      this.dfrom = this.value[0]
      this.dto = this.value[1]
    },
    mounted() {
      let vm = this
      $(this.$el).datepicker({
        format: 'dd.mm.yyyy',
        todayBtn: 'linked',
        language: 'ru',
        autoclose: true,
        todayHighlight: true
      }).on('changeDate', () => {
        vm.$refs.from.dispatchEvent(new Event('input'))
        vm.$refs.to.dispatchEvent(new Event('input'))
      })
    },
    watch: {
      dfrom() {
        this.emit()
      },
      dto() {
        this.emit()
      }
    },
    methods: {
      emit() {
        this.$emit('input', [this.dfrom, this.dto])
      },
    }
  }
</script>

<style scoped>

</style>
