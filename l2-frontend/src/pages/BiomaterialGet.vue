<template>
  <div class="root">
    <div class="a">
      <BiomaterialSearch />
    </div>
    <div class="b">2</div>
    <div class="d">3</div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import BiomaterialSearch from '@/ui-cards/BiomaterialSearch.vue';

@Component({
  components: {
    BiomaterialSearch,
  },
})
export default class BiomaterialGet extends Vue {}
</script>

<style lang="scss" scoped>
.root {
  position: absolute;
  top: 36px;
  left: 0;
  right: 0;
  bottom: 0;

  overflow-x: hidden;
  overflow-y: hidden;

  .a,
  .b,
  .d {
    position: absolute;
    overflow-y: auto;
  }

  .a {
    top: 0;
    right: 50%;
    left: 0;
    bottom: 0;
    border-right: 1px solid #aaa;
  }

  .b,
  .d {
    right: 0;
    left: 50%;
  }

  .b {
    top: 0;
    bottom: 50%;
  }

  .d {
    border-top: 1px solid #aaa;
    top: 50%;
    bottom: 0;
  }
}
</style>
