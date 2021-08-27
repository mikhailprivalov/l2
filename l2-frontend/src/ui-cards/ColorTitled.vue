<template>
  <div v-frag>
    <div class="color" :style="`background-color: ${color};color: ${color};`"></div>

    {{ title }}
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';

@Component({
  props: {
    color: { type: String, required: true },
    title: { type: String, required: true },
  },
})
export default class ColorTitled extends Vue {
  color: string;

  title: string;
}
</script>

<style lang="scss" scoped>
.color {
  width: 13px;
  height: 13px;
  border-radius: 4px;
  display: inline-block;
  vertical-align: middle;
  margin-bottom: 3px;
  border: 1px #e2e2e2 solid;
  box-shadow: 0 0 3px;
}
</style>
