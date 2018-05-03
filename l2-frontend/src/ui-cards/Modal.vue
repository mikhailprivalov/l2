<template>
  <transition name="modal">
    <div class="modal-mask">
      <div class="panel panel-flt" :style="{ minWidth: minWidth, alignSelf: 'flex-start', marginTop: marginTop }">
        <div class="panel-heading">
          <h3 class="panel-title">
            <slot name="header">
              default header
            </slot>
            <button type="button" class="close" v-show="!noClose" @click="$emit('close')">&times;</button>
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
        default: 'false',
      },
      'white-bg': {
        required: false,
        default: 'false',
      },
      'min-width': {
        required: false,
        default: '30%',
      },
      'margin-top': {
        required: false,
        default: '15px',
      },
      'no-close': {
        required: false,
        default: false,
        type: Boolean,
      },
    }
  }
</script>

<style scoped>
  .white_bg {
    background-color: #fff;
  }

  .close {
    line-height: 12px;
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
