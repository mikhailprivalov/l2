<template>
  <div class="input-daterange input-group">
    <input type="text" class="input-sm form-control no-context" style="height: 34px;padding: 5px;width: 80px"
           ref="from" v-model.lazy="dfrom" maxlength="10"/>
    <span class="input-group-addon" style="background-color: #fff;color: #000; height: 34px">&mdash;</span>
    <input type="text" class="input-sm form-control no-context" style="height: 34px;padding: 5px;width: 80px"
           ref="to" v-model.lazy="dto" maxlength="10"/>
  </div>
</template>

<script>
  import moment from 'moment'

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
      this.$root.$on('validate-datepickers', this.validate)
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
        if(!$(vm.$refs.from).is(':focus'))
          vm.$refs.from.dispatchEvent(new Event('change'))
        if(!$(vm.$refs.to).is(':focus'))
          vm.$refs.to.dispatchEvent(new Event('change'))
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
        this.validate()
        this.$emit('input', [this.dfrom, this.dto])
      },
      validate_date(date) {
        let r = moment(date, 'DD.MM.YYYY', true).isValid()
        if (!r)
          errmessage('Неверная дата')
        return r
      },
      validate() {
        let ch = false
        if (!this.validate_date(this.dfrom)) {
          this.dfrom = moment().format('DD.MM.YYYY')
          $(this.$refs.from).datepicker('update', moment().toDate())
          ch = true
        }
        if (!this.validate_date(this.dto)) {
          this.dto = moment().format('DD.MM.YYYY')
          $(this.$refs.to).datepicker('update', moment().toDate())
          ch = true
        }
        if (ch) {
          $(this.$el).datepicker('update')
        }
      },
    }
  }
</script>

<style scoped>

</style>
