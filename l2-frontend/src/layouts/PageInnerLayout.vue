<template>
  <div :class="$style.root">
    <slot />
  </div>
</template>

<script lang="ts" setup>
</script>

<style module lang="scss">
.root {
    position: absolute;
    top: 36px;
    right: 0;
    bottom: 0;
    left: 0;
}
</style>
