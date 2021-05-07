<template>
  <div class="fv" :class="{inFavorite}" @click="click()">
    <i class="fa fa-star"></i> <span>{{inFavorite ? 'в избранном' : 'не в избранном'}}</span>
  </div>
</template>

<script>
import directionsPoint from '../../api/directions-point';

export default {
  name: 'Favorite',
  props: {
    direction: {
      type: Number,
      required: true,
    },
    inList: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      inFavorite: false,
    };
  },
  mounted() {
    if (!this.inList) {
      this.$root.$on('remove-from-favorites', () => this.load());
    }
  },
  watch: {
    direction: {
      immediate: true,
      handler() {
        this.load();
      },
    },
  },
  methods: {
    async click(forced, val) {
      this.inFavorite = forced ? Boolean(val) : !this.inFavorite;
      await directionsPoint.directionInFavorites({ pk: this.direction, update: true, status: this.inFavorite });
      if (this.inList) {
        this.$root.$emit('remove-from-favorites');
      }
      this.$root.$emit('add-to-favorites');
    },
    async load() {
      const { status } = await directionsPoint.directionInFavorites({ pk: this.direction, update: false });
      this.inFavorite = status;
    },
  },
};
</script>

<style scoped lang="scss">
  .fv {
    cursor: pointer;

    &:hover span {
      text-shadow: 0 0 3px rgba(#049372, .4);
      color: #049372;
    }
  }

  i {
    vertical-align: middle;
    display: inline-block;
    margin-right: 3px;
  }

  .inFavorite i {
    color: #93046d;
  }
</style>
