<template>
  <div :class="$style.root">
    <div :class="$style.left">
      <slot name="left" />
    </div>
    <div :class="$style.center">
      <slot name="center" />
    </div>
    <div :class="$style.right">
      <slot name="right" />
    </div>
  </div>
</template>

<script lang="ts" setup>
</script>

<style module lang="scss">
.root {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
}

.left, .right {
  height: 100%;
  position: relative;
}

.left {
  border-right: 1px solid #646d78;
  padding: 0;
  width: 480px;
}

.center {
  border-right: 1px solid #646d78;
  padding: 0;
  width: 480px;
}

.right {
  flex: 1;
}
</style>
