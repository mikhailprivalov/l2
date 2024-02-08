<template>
  <span :class="$style.loader" />
</template>

<script setup lang="ts"></script>

<style module lang="scss">
.loader {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: block;
  margin: 15px auto;
  position: relative;
  color: #049372;
  left: -100px;
  box-sizing: border-box;
  animation: shadowRolling 2s linear infinite;
}

@keyframes shadowRolling {
  0% {
    box-shadow: 0 0 rgba(#049372, 0), 0 0 rgba(#049372, 0), 0 0 rgba(#049372, 0), 0 0 rgba(#049372, 0);
  }
  12% {
    box-shadow: 100px 0 #049372, 0 0 rgba(#049372, 0), 0 0 rgba(#049372, 0), 0 0 rgba(#049372, 0);
  }
  25% {
    box-shadow: 110px 0 #049372, 100px 0 #049372, 0 0 rgba(#049372, 0), 0 0 rgba(#049372, 0);
  }
  36% {
    box-shadow: 120px 0 #049372, 110px 0 #049372, 100px 0 #049372, 0 0 rgba(#049372, 0);
  }
  50% {
    box-shadow: 130px 0 #049372, 120px 0 #049372, 110px 0 #049372, 100px 0 #049372;
  }
  62% {
    box-shadow: 200px 0 rgba(#049372, 0), 130px 0 #049372, 120px 0 #049372, 110px 0 #049372;
  }
  75% {
    box-shadow: 200px 0 rgba(#049372, 0), 200px 0 rgba(#049372, 0), 130px 0 #049372, 120px 0 #049372;
  }
  87% {
    box-shadow: 200px 0 rgba(#049372, 0), 200px 0 rgba(#049372, 0), 200px 0 rgba(#049372, 0), 130px 0 #049372;
  }
  100% {
    box-shadow: 200px 0 rgba(#049372, 0),
      200px 0 rgba(#049372, 0),
      200px 0 rgba(#049372, 0),
      200px 0 rgba(#049372, 0);
  }
}
</style>
