<template>
  <div id="app" :class="$route.meta.narrowLayout && 'container'">
    <Navbar />

    <router-view v-if="!fullPageLoader"></router-view>

    <div id="preloader" v-if="inLoading"></div>

    <transition name="fade">
      <div id="full-page-loader" v-if="fullPageLoader">
        <div class="loader-inner">
          <div class="rotated-circle">
          </div>
          <div class="fixed-loader-text">L<span>2</span></div>
        </div>
      </div>
    </transition>

    <CheckBackend />
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import { mapGetters } from 'vuex';
import Navbar from '@/components/Navbar.vue';
import CheckBackend from '@/ui-cards/CheckBackend.vue';

@Component({
  components: { CheckBackend, Navbar },
  computed: mapGetters(['inLoading', 'fullPageLoader', 'authenticated']),
  metaInfo() {
    return {
      title: `${this.$route.meta.title || 'L2'} — ${this.$orgTitle()}`,
    };
  },
})
export default class App extends Vue {
    inLoading: boolean;

    fullPageLoader: boolean;

    authenticated: boolean;
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

#full-page-loader {
  position: fixed;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 100000;
  background: radial-gradient(#CECECE, #fff);
  display: flex;
  justify-content: center;
  align-items: center;

  .loader-inner {
    width: 350px;
    height: 350px;
    border-radius: 100%;
    background: linear-gradient(
        165deg,
        rgba(240, 240, 240, 1) 0%,
        rgb(220, 220, 220) 60%,
        rgb(170, 170, 170) 99%,
        rgb(10, 10, 10) 100%
    );
    position: relative;

    .fixed-loader-text {
      position: absolute;
      top: 50%;
      left: 50%;
      text-align: center;
      width: 200px;
      transform: translateX(-50%) translateY(-50%);
      font-size: 50px;
      font-weight: 400;
      font-style: italic;
      color: #4c4c4c;

      span {
        font-size: 40px;
        position: relative;
        bottom: .8ex;
      }
    }

    .rotated-circle:before {
      position: absolute;
      content: '';
      width: 100%;
      height: 100%;
      border-radius: 100%;
      border-bottom: 0 solid #04937205;

      box-shadow: 0 -10px 20px 20px #04937240 inset,
      0 -5px 15px 10px #04937250 inset,
      0 -2px 5px #04937280 inset,
      0 -3px 2px #049372BB inset,
      0 2px 0px #049372BB,
      0 2px 3px #049372BB,
      0 5px 5px #04937290,
      0 10px 15px #04937260,
      0 10px 20px 20px #04937240;
      filter: blur(4px);
      animation: 3s rotate linear infinite;
    }
  }
}

@keyframes rotate {
  0% {
    transform: rotate(0deg)
  }

  100% {
    transform: rotate(360deg);
  }
}

.fade-enter-active, .fade-leave-active {
  transition: opacity .7s;
}

.fade-enter, .fade-leave-to {
  opacity: 0;
}
</style>
