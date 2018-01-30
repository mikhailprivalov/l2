<template>
  <transition name="modal">
    <div class="modal-mask">
      <div class="panel panel-flt" style="align-self: flex-start;margin-top: 15px;min-width: 30%;">
        <div class="panel-heading">
          <h3 class="panel-title">
            <slot name="header">
              default header
            </slot>
            <button type="button" class="close" @click="$emit('close')">&times;</button>
          </h3>
        </div>
        <div class="panel-body" :class="{white_bg: whiteBg === 'true'}">
          <slot name="body">
            default body
          </slot>
        </div>
        <div class="panel-footer" v-if="showFooter === 'true'">
          <slot name="footer">
            default footer
          </slot>
        </div>
      </div>
    </div>
  </transition>
</template>

<script>
  export default {
    name: 'modal',
    props: {
      'show-footer': {
        required: false,
        default: 'false'
      },
      'white-bg': {
        required: false,
        default: 'false'
      }
    }
  }
</script>

<style scoped>
  .white_bg {
    background-color: #fff;
  }
</style>

<style>
  .modal-mask {
    position: fixed;
    z-index: 9998;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, .5);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: opacity .3s ease;
    overflow: auto;
  }

  .page-header {
    min-width: 400px;
  }
</style>
