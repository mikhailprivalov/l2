<template>
  <div class="modal fade" v-bind:class="{ 'in': isShow, 'hide': !isShow }" tabindex="-1" role="dialog">
    <div class="modal-dialog" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <button type="button" class="close" @click=""><span aria-hidden="true">&times;</span></button>
          <h4 class="modal-title">Test1</h4>
        </div>
        <div class="modal-body content">
          Test
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  export default {
    name: 'journal-get-material-modal',
    data() {
      return {
        isShow: false
      }
    },
    methods: {
      show() {
        this.isShow = true
      },
      hide() {
        this.isShow = false
      }
    }
  }
</script>
