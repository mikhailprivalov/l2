<template>
  <tr v-show="ok" :class="{warn: warn, direction: type === 'direction'}">
    <td>{{researche_title}}</td>
    <td v-if="in_load" colspan="3">поиск результата или назначения...</td>
    <td v-if="!in_load">
      <a href="#" @click.prevent="show_result" v-if="type === 'result'">просмотр результата</a>
      <div v-else>
        Есть созданное направление без результата<br/>
        <a href="#" @click.prevent="show_direction">просмотр направления</a>
      </div>
    </td>
    <td v-if="!in_load" class="text-center">{{date}}</td>
    <td v-if="!in_load" class="text-center">
      {{days_str}}
    </td>
  </tr>
</template>

<script>
  import directions_point from './api/directions-point'
  import moment from 'moment'

  moment.updateLocale('ru', {
    relativeTime: {
      s: 'только что',
      m: 'только что',
      mm: '%d мин. назад',
      h: 'час назад',
      hh: '%d ч. назад',
      d: '1 д. назад',
      dd: '%d д. назад',
      M: '1 м. назад',
      MM: '%d м. назад',
      y: '1 г. назад',
      yy: '%d г. назад'
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
        ms: 0,
        days: -1,
        days_str: -1,
        date: '',
        date_orig: '',
        type: 'result'
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
      show_direction() {
        this.$root.$emit('print:directions', [this.direction])
      },
      load() {
        $('.scrolldown').scrollDown()
        let vm = this
        directions_point.lastResult(this.individual, this.research).then(data => {
          vm.in_load = false
          vm.ok = data.ok
          if (data.ok) {
            vm.type = data.type
            vm.date = data.data.datetime
            let m = moment.unix(data.data.ts)
            let n = moment()
            vm.ms = n.diff(m)
            vm.days = n.diff(m, 'days')
            vm.days_str = moment.duration(vm.ms).locale('ru').humanize()
            vm.direction = data.data.direction
          }
          setTimeout(() => {
            $('.scrolldown').scrollDown()
          }, 10)
        })
      },
    },
  }
</script>

<style scoped lang="scss">
  td, th {
    padding: 2px !important;
    word-wrap: break-word;
    color: #000
  }

  .warn {
    background-color: #ffa04d;
    &.direction {
      background-color: #ff391a;
      td {
        color: #fff;
      }
      a {
        color: #fff !important;
      }
    }
  }
</style>
