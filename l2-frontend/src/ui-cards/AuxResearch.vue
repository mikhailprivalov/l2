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
                @click.prevent="genAuxDirection(row.pk)"
              >{{ row.title }}</a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <Modal
      v-if="toEnter"
      ref="modalResults"
      white-bg="true"
      width="100%"
      margin-left-right="34px"
      margin-top="30px"
      show-footer="true"
      @close="hideModalResults"
    >
      <span slot="header">Заполнение </span>
      <div
        slot="body"
        class="aux-body"
      >
        <iframe
          :src="toEnterUrl"
          name="toEnter"
        />
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-4">
            <button
              class="btn btn-primary-nb btn-blue-nb"
              type="button"
              @click="hideModalResults"
            >
              Закрыть
            </button>
          </div>
        </div>
      </div>
    </Modal>
  </div>
</template>

<script lang="ts">
import api from '@/api';
import Modal from '@/ui-cards/Modal.vue';

export default {
  name: 'AuxResearch',
  components: { Modal },
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
  computed: {
    toEnterUrl() {
      return `/ui/results/descriptive?embedded=1#{"pk":${this.toEnter}}`;
    },
  },
  methods: {
    hideModalResults() {
      if (this.$refs.modalResults) {
        this.$refs.modalResults.$el.style.display = 'none';
      }
      this.toEnter = null;
    },
    async genAuxDirection(idResearch) {
      const data = await api(
        'directions/aux-generate',
        { directionId: this.mainDirection, researches: { '-9': [idResearch] } },
      );
      const pk = data.directions[0];
      this.toEnter = pk;
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

.aux-body {
  height: calc(100vh - 179px);
  position: relative;

  iframe {
    display: block;
    width: 100%;
    height: 100%;
    border: none;
  }
}
</style>
