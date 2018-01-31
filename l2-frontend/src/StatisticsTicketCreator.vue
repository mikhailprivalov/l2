<template>
  <div>

  </div>
</template>

<script>
  import * as action_types from './store/action-types'
  import statistics_tickets_point from './api/statistics-tickets-point'

  export default {
    name: 'statistics-ticket-creator',
    props: {
      base: {
        type: Object,
        reqired: true
      },
      card_pk: {
        type: Number
      },
    },
    data() {
      return {
        types: {
          visit: [],
          result: [],
        }
      }
    },
    created() {
      let vm = this
      vm.$store.dispatch(action_types.INC_LOADING).then()
      statistics_tickets_point.getTicketsTypes().then(data => {
        vm.types.visit = data.visit
        vm.types.result = data.result
      }).finally(() => {
        vm.$store.dispatch(action_types.DEC_LOADING).then()
      })
    }
  }
</script>

<style scoped>

</style>
