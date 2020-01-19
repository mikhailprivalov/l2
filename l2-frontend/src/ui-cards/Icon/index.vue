<template>
  <div class="icon" :class="[`icon--${name}`, `icon--${size}`, { 'has-align-fix': fixAlign }]">
    <img :src="source" class="icon__svg" />
  </div>
</template>

<script>
    export default {
        props: {
            name: {},
            size: {
                default: 'normal',
            },
            modifier: {
                default: null,
            },
            fixAlign: {
                default: true,
            },
        },
        data() {
            return {
                source: require(`./icons/${this.name}.svg`),
            };
        }
    }
</script>

<style lang="scss" scoped>
  .icon {
    position: relative;
    display: inline-block;
    vertical-align: middle;
    width: 16px;
    height: 20px;
    fill: currentColor;

    &__svg {
      display: inline-block;
      vertical-align: top;
      width: 100%;
      height: 100%;
    }

    &:first-child {
      margin-left: 0;
    }

    &:last-child {
      margin-right: 0;
    }

  }
</style>
