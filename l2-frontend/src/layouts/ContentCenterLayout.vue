<template>
  <div :class="$style.root">
    <div :class="$style.contentWrapper">
      <slot />
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
  justify-content: center;
  align-items: center;
}

.contentWrapper {
  text-align: center;
}
</style>
