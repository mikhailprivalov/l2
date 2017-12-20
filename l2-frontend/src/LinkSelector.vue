<template>
  <div>
    <a href="#" class="link">{{selected.title}}</a>
    <div class="hidden popover_content">
      <table class="table table-responsive">
        <tr v-for="row_option in options">
          <td><a href="#" :instance_id="uuid" func="update_val" :val="row_option.key" onclick="vue_cb(this); return false">{{row_option.title}}</a></td>
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
    data() {
      return {
        uuid: ([1e7] + -1e3 + -4e3 + -8e3 + -1e11).replace(/[018]/g, c => (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16))
      }
    },
    methods: {
      update_val(v) {
        this.value = v
        this.$emit('input', v)
        $('.link', this.$el).popover('hide')
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
    created() {
      set_instance(this)
    },
    mounted() {
      let $link = $('.link', this.$el)
      let $popover_content = $('.popover_content', this.$el)
      $link.popover({
        html: true,
        title: 'Выберите вариант',
        placement: 'auto',
        trigger: 'focus',
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
      border-color: #fff !important;
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
