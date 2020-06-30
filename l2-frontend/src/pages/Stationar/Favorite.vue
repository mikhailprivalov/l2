<template>
  <div class="fv" :class="{inFavorite}" @click="click">
    <i class="fa fa-star"></i> <span>{{inFavorite ? 'в избранном' : 'не в избранном'}}</span>
  </div>
</template>

<script>
  import * as action_types from "../../store/action-types";
  import directions_point from "../../api/directions-point";

  export default {
    name: "Favorite",
    props: {
      direction: {
        type: Number,
        required: true,
      }
    },
    data() {
      return {
        inFavorite: false,
      }
    },
    mounted() {
      this.load();
    },
    watch: {
      direction: {
        immediate: true,
        handler() {
          this.load();
        },
      }
    },
    methods: {
      async click() {
        await this.$store.dispatch(action_types.INC_LOADING)
        this.inFavorite = !this.inFavorite;
        await directions_point.directionInFavorites({pk: this.direction, update: true, status: this.inFavorite})
        await this.$store.dispatch(action_types.DEC_LOADING)
      },
      async load() {
        await this.$store.dispatch(action_types.INC_LOADING)
        const {status} = await directions_point.directionInFavorites({pk: this.direction, update: false})
        this.inFavorite = status;
        await this.$store.dispatch(action_types.DEC_LOADING)
      },
    }
  }
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
