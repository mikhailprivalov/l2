<template>
  <div>
    <a href="#" ref="link">{{selected.title}}</a>
    <div class="hidden" ref="popover_content">
      <div v-for="row_option in options" class="row">
        <div class="col-xs-6"><a href="#">{{row_option.title}}</a></div>
        <div class="col-xs-6 text-right" v-html="row_option.about"></div>
        <div class="col-xs-12">
          <hr/>
        </div>
      </div>
    </div>
  </div>
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
    },
    created() {
      let vm = this
      $(vm.$refs.link).popover({
        html: true
      }).on('show.bs.popover', () => {
        $(vm.$refs.link).data('content', $(vm.$refs.popover_content).html())
      })
    }
  }
</script>

<style scoped lang="scss">
  a {
    text-decoration: underline dotted;
    color: #737373;
    &:hover {
      text-decoration: underline solid;
      color: #393939;
    }
  }
</style>
