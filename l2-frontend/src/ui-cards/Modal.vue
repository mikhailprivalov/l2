<template>
  <transition name="modal">
    <div class="modal-mask">
      <div class="panel panel-flt"
           :style="{
          minWidth, maxWidth, alignSelf, marginTop, width, marginLeft: marginLeftRight, marginRight: marginLeftRight
        }">
        <div class="panel-heading">
          <h3 class="panel-title">
            <slot name="header">
              default header
            </slot>
            <button type="button" class="close" v-show="!noClose" @click="$emit('close')">&times;</button>
          </h3>
        </div>
        <div v-if="resultsEditor" class="results-editor">
          <div class="panel-body" :class="{white_bg: whiteBg === 'true', overflowUnset: overflowUnset === 'true'}">
            <slot name="body">
              default body
            </slot>
          </div>
        </div>
        <div v-else class="panel-body" :class="{white_bg: whiteBg === 'true', overflowUnset: overflowUnset === 'true'}">
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
    'overflow-unset': {
      required: false,
      default: 'false',
    },
    'min-width': {
      required: false,
      default: '30%',
    },
    'max-width': {
      required: false,
      default: '100%',
    },
    width: {
      required: false,
      default: 'auto',
    },
    'margin-top': {
      required: false,
      default: '15px',
    },
    alignSelf: {
      required: false,
      default: 'flex-start',
    },
    'no-close': {
      required: false,
      default: false,
      type: Boolean,
    },
    marginLeftRight: {
      required: false,
      default: '41px',
    },
    resultsEditor: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
};
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
  z-index: 5000;
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

.panel-body {
  overflow-y: auto;
  overflow-x: hidden;
}

.panel-body.overflowUnset {
  overflow: unset;
}
</style>
