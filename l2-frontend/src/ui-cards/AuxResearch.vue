<template>
  <div v-frag>
    <a
      v-tippy="{
        html: '#aux-view',
        reactive: true,
        interactive: true,
        arrow: true,
        animation: 'fade',
        duration: 0,
        theme: 'light',
        placement: 'bottom',
        trigger: 'click mouseenter',
        zIndex: 4999,
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
      }"
      href="#"
      class="dropdown-toggle"
      style="color: #049372"
      @click.prevent
    >
      <i class="fa-solid fa-square-caret-down" />
    </a>

    <div
      id="aux-view"
      class="tp"
    >
      <table class="table">
        <tbody>
          <tr
            v-for="row in auxResearch"
            :key="`${row.title}`"
          >
            <td>
              <a
                href="#"
                @click.prevent="genAuxDirection()"
              >{{ row.title }}</a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script lang="ts">
import api from '@/api';

export default {
  name: 'AuxResearch',
  props: {
    auxResearch: {
      type: Array,
      required: false,
    },
    mainDirection: {
      type: Number,
      required: false,
    },
  },
  data() {
    return {
      toEnter: null,
    };
  },
  methods: {
    async genAuxDirection() {
      const data = await api(
        'directions/aux-generate',
        { directionId: this.mainDirection, researches: { '-9': [this.auxResearch[0].pk] } },
      );
      window.open(`/ui/results/descriptive?embedded=1#{"pk":${data.directions[0]}}`, '_blank');
    },
  },
};
</script>

<style scoped lang="scss">

  i {
    vertical-align: middle;
    display: inline-block;
    margin-right: 3px;
  }

  .tp {
    text-align: left;
    padding: 1px;

    table {
      margin: 0;
    }

    max-height: 600px;
    overflow-y: auto;
  }
</style>
