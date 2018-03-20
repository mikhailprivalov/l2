<template>
  <tr v-show="ok">
    <th>{{researche_title}}</th>
    <td v-if="in_load">поиск последнего результата...</td>
    <td v-else><a href="#" @click.prevent="show_result">просмотр результата</a></td>
    <th class="text-center">{{date}}</th>
    <th class="text-center">
      <div v-if="!in_load && ok">{{days}} д. назад</div>
    </th>
  </tr>
</template>

<script>
  import directions_point from './api/directions-point'
  import moment from 'moment'

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
            return res.full_title
          }
        }
        return ''
      },
    },
    methods: {
      show_result() {
        this.$root.$emit('show_results', this.direction)
      },
      load() {
        let vm = this
        directions_point.lastResult(this.individual, this.research).then(data => {
          vm.in_load = false
          vm.ok = data.ok
          if (data.ok) {
            vm.date = data.data.datetime
            let m = moment(data.data.datetime, 'DD.MM.YYYY')
            let n = moment()
            vm.days = n.diff(m, 'days')
            vm.direction = data.data.direction
            $('.scrolldown').scrollDown()
          }
        })
      }
    },
  }
</script>

<style scoped>
  td, th {
    padding: 2px !important;
    word-wrap: break-word;
  }

  tr:not(.warn) {
    background-color: #fff;
  }
</style>
