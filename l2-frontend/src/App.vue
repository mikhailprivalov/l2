<template>
  <div id="app">
    <Navbar/>
    <router-view></router-view>

    <div id="preloader" v-if="inLoading"></div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import { mapGetters } from 'vuex';
import Navbar from '@/components/Navbar.vue';

@Component({
  components: {
    Navbar,
  },
  computed: mapGetters(['inLoading']),
})
export default class App extends Vue {
}
</script>

<style lang="scss" scoped>
#preloader {
  opacity: 0;
  cursor: progress;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  position: fixed;
  height: 100%;
  width: 100%;
  background-color: rgba(0, 0, 0, .68);
  left: 0;
  top: 0;
  z-index: 100000;
  animation: fadeInFromNone 10s ease-out forwards;
}

@keyframes fadeInFromNone {
  0% {
    opacity: 0;
  }

  15% {
    opacity: 0;
  }

  100% {
    opacity: 1;
  }
}
</style>
