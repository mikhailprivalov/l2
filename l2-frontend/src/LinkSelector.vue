<template>
  <div><a href="#" @click.prevent="">{{selected.title}}</a></div>
</template>

<script>
  export default {
    name: 'link-selector',
    props: {
      options: {
        type: Array,
        required: true
      },
      value: {}
    },
    computed: {
      selected() {
        for (let b of this.options) {
          if (b.key === this.value) {
            return b
          }
        }
        return {key: '', title: 'не выбрано', about: ''}
      }
    }
  }
</script>

<style scoped>

</style>
