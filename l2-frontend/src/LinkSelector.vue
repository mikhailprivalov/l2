<template>
  <div>
    <a href="#" class="link">{{selected.title}}</a>
    <div class="hidden popover_content">
      <table class="table table-responsive">
        <tr v-for="row_option in options">
          <td><a href="#" @click.native.prevent="update_val(row_option.key)">{{row_option.title}}</a></td>
          <td v-html="row_option.about"></td>
        </tr>
      </table>
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
    methods: {
      update_val(v) {
        console.log(v)
        this.value = v
        this.$emit('input', v)
      }
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
    mounted() {
      let vm = this
      let $link = $('.link', this.$el)
      let $popover_content = $('.popover_content', this.$el)
      $link.popover({
        html: true,
        title: 'Выберите вариант',
        placement: 'bottom'
      }).on('show.bs.popover', () => {
        $link.attr('data-content', $popover_content.html())
      })
    }
  }
</script>

<style scoped lang="scss">
  a {
    text-decoration: underline dotted;
    color: #666;
    &:hover {
      text-decoration: underline solid;
      color: #444;
    }
  }
</style>

<style lang="scss">
  .popover {
    background: #fff;
    color: #000;
    max-width: 100%;

    .arrow {
      border-bottom-color: #fff !important;
    }

    hr {
      margin-top: 10px;
      margin-bottom: 10px;
      border: 0;
      border-top: 1px solid #aaa;
    }
  }

  .popover-title {
    color: #000
  }
</style>
