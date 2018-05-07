<template>
  <tr v-show="ok" :class="{warn: warn}">
    <td>{{researche_title}}</td>
    <td v-if="in_load" colspan="3">поиск последнего результата...</td>
    <td v-if="!in_load"><a href="#" @click.prevent="show_result">просмотр результата</a></td>
    <td v-if="!in_load" class="text-center">{{date}}</td>
    <td v-if="!in_load" class="text-center">
      {{days_str}} назад
    </td>
  </tr>
</template>

<script>
  import directions_point from './api/directions-point'
  import moment from 'moment'

  moment.updateLocale('ru', {
    relativeTime: {
      d: '1 д.',
      dd: '%d д.',
      M: '1 м.',
      MM: '%d м.',
      y: '1 г.',
      yy: '%d г.'
    }
  })

  export default {
    name: 'last-result',
    props: {
      individual: {
        type: Number
      },
      research: {
        type: Number
      }
    },
    data() {
      return {
        in_load: true,
        ok: true,
        direction: -1,
        days: -1,
        days_str: -1,
        date: '',
        date_orig: '',
      }
    },
    mounted() {
      this.load()
    },
    watch: {
      individual() {
        this.load()
      }
    },
    computed: {
      researche_title() {
        for (let pk of Object.keys(this.$store.getters.researches_obj)) {
          let res = this.$store.getters.researches_obj[pk]
          if (res.pk === this.research) {
            return res.title
          }
        }
        return ''
      },
      warn() {
        return this.days <= 10 && this.ok && !this.in_load
      }
    },
    methods: {
      show_result() {
        this.$root.$emit('show_results', this.direction)
      },
      load() {
        $('.scrolldown').scrollDown()
        let vm = this
        directions_point.lastResult(this.individual, this.research).then(data => {
          vm.in_load = false
          vm.ok = data.ok
          if (data.ok) {
            vm.date = data.data.datetime
            let m = moment.unix(data.data.ts)
            let n = moment()
            vm.days = n.diff(m, 'days')
            vm.days_str = moment.duration(vm.days, 'days').locale("ru").humanize()

            vm.direction = data.data.direction
          }
        })
      },
    },
  }
</script>

<style scoped>
  td, th {
    padding: 2px !important;
    word-wrap: break-word;
    color: #000
  }

  .warn {
    background-color: #ffa04d;
  }
</style>
