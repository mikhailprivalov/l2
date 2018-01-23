<template>
  <div class="input-daterange input-group">
    <input type="text" class="input-sm form-control no-context" style="height: 34px;padding: 5px;width: 80px"
           v-model="dfrom" ref="from" readonly/>
    <span class="input-group-addon" style="background-color: #fff;color: #000; height: 34px">&mdash;</span>
    <input type="text" class="input-sm form-control no-context" style="height: 34px;padding: 5px;width: 80px"
           v-model="dto" ref="to" readonly/>
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
        dto: ''
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
        vm.dfrom = $(vm.$refs.from).val()
        vm.to = $(vm.$refs.to).val()
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
      }
    }
  }
</script>

<style scoped>

</style>
