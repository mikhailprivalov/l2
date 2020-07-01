<template>
  <fragment>
    <a href="#" class="dropdown-toggle" @click.prevent
       v-tippy="{
                html: '#favorites-view',
                reactive: true,
                interactive: true,
                arrow: true,
                animation: 'fade',
                duration: 0,
                theme: 'light',
                placement: 'bottom',
                trigger: 'click mouseenter focus',
                popperOptions: {
                  modifiers: {
                    preventOverflow: {
                      boundariesElement: 'window'
                    },
                    hide: {
                      enabled: false
                    }
                  }
                },
             }">
      Избранные истории <span class="badge badge-light">{{data.length}}</span>
    </a>

    <div id="favorites-view" class="tp">
      <table class="table table-condensed table-bordered">
        <tbody>
        <tr v-for="row in data">
          <td>
            <LinkToHistory :direction="row.direction" />
          </td>
          <td>
            {{row.client}}
          </td>
          <td>
            {{row.card}}
          </td>
          <td>
            <Favorite :direction="row.direction" in-list />
          </td>
        </tr>
        </tbody>
      </table>
      <div v-if="data.length === 0">
        Нет избранных историй
      </div>
    </div>
  </fragment>
</template>

<script>
  import directions_point from "../api/directions-point";
  import LinkToHistory from "../pages/Stationar/LinkToHistory";
  import Favorite from "../pages/Stationar/Favorite";

  export default {
    name: "Favorites",
    components: {Favorite, LinkToHistory},
    data() {
      return {
        inFavorite: false,
        data: [],
      }
    },
    mounted() {
      this.load();

      this.$root.$on('add-to-favorites', () => this.load());
    },
    methods: {
      async load() {
        const {data} = await directions_point.allDirectionsInFavorites()
        this.data = data;
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

  .tp {
    text-align: left;
    line-height: 1.1;
    padding: 5px;

    table {
      margin: 0;
    }

    max-height: 600px;
    overflow-y: auto;
  }
</style>
