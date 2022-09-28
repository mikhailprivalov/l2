<template>
  <div
    class="root"
    :class="{ hasGrid }"
  >
    <div class="a">
      <ResearchesPicker
        v-model="research"
        :hidetemplates="true"
        :oneselect="true"
        :autoselect="false"
        :types-only="[14]"
        kk="me"
        :just_search="true"
      />
    </div>
    <div class="b gutter gutter-col gutter-column-1" />
    <div class="c">
      <SelectedResearches
        :researches="research ? [research] : []"
        :card_pk="card_pk"
        :selected_card="selected_card"
        :valid="true"
        :hide_diagnosis="true"
        :hide_params="true"
        :monitoring="true"
        kk="me"
        :base="base"
      />
    </div>
    <div class="d gutter gutter-row gutter-row-1" />
    <div class="e">
      <MonitoringHistoryViewer />
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
      <span slot="header">Заполнение мониторинга</span>
      <div
        slot="body"
        class="monitoring-body"
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
import Split from 'split-grid';

import ResearchesPicker from '@/ui-cards/ResearchesPicker.vue';
import SelectedResearches from '@/ui-cards/SelectedResearches.vue';
import Modal from '@/ui-cards/Modal.vue';
import MonitoringHistoryViewer from '@/ui-cards/MonitoringHistoryViewer.vue';

export default {
  components: {
    ResearchesPicker,
    SelectedResearches,
    Modal,
    MonitoringHistoryViewer,
  },
  data() {
    return {
      show_results_pk: -1,
      show_rmis_directions: false,
      show_rmis_send_directions: false,
      diagnos: '',
      research: -1,
      hasGrid: window.Modernizr.cssgrid,
      selected_card: {},
      card_pk: -1,
      base: {},
      toEnter: null,
    };
  },
  computed: {
    toEnterUrl() {
      return `/ui/results/descriptive?embedded=1#{"pk":${this.toEnter}}`;
    },
  },
  mounted() {
    if (this.hasGrid) {
      Split({
        columnGutters: [
          {
            track: 1,
            element: document.querySelector('.gutter-column-1'),
          },
        ],
        rowGutters: [
          {
            track: 1,
            element: document.querySelector('.gutter-row-1'),
          },
        ],
        minSize: 200,
      });
    }

    this.$root.$on('embedded-form:open', pk => {
      this.toEnter = pk;
    });
  },
  methods: {
    hideModalResults() {
      if (this.$refs.modalResults) {
        this.$refs.modalResults.$el.style.display = 'none';
      }
      this.$root.$emit('embedded-form:hide', this.toEnter);
      this.toEnter = null;
    },
  },
};
</script>

<style scoped lang="scss">
.root {
  position: absolute;
  top: 36px;
  left: 0;
  right: 0;
  bottom: 0;

  &.hasGrid {
    display: grid;
    grid-template-columns: 1fr 5px 1fr;
    grid-template-rows: 1fr 5px 1fr;
    gap: 0;
    height: calc(calc(100vh - calc(100vh - 100%)) - 36px);
  }

  .a {
    grid-area: 1 / 1 / 2 / 2;

    padding-right: 0;
    padding-bottom: 0;
    text-align: left;
    background: #fff;
  }

  .b {
    grid-area: 1 / 2 / 2 / 3;
    display: block;
  }

  .c {
    grid-area: 1 / 3 / 2 / 4;

    padding-left: 0;
    padding-bottom: 0;
    text-align: left;
    background: #fff;
  }

  .d {
    grid-area: 2 / 1 / 3 / 4;
    display: block;
  }

  .e {
    grid-area: 3 / 1 / 4 / 4;
    padding: 0;
    margin: 5px;
    margin-top: 0;
    text-align: left;
    background: #fff;
  }

  .f {
    grid-area: 3 / 2 / 4 / 3;
    display: block;
  }

  .g {
    grid-area: 3 / 3 / 4 / 4;

    &.onlyDocCall {
      grid-area: 1 / 3 / 4 / 4;
    }

    &:not(.onlyDocCall) {
      padding-top: 0;
    }

    padding-left: 0;
    text-align: left;
    background: #fff;
  }

  @media (max-width: 760px) {
    grid-template-columns: 1fr !important;
    grid-template-rows: repeat(4, 320px) !important;
    gap: 5px !important;

    & > div {
      padding: 5px !important;
    }

    .a {
      grid-area: 1 / 1 / 2 / 2;
    }

    .b {
      display: none;
    }

    .c {
      grid-area: 2 / 1 / 3 / 2;
    }

    .d {
      display: none;
    }

    .e {
      grid-area: 3 / 1 / 4 / 2;
    }

    .f {
      display: none;
    }

    .g {
      grid-area: 4 / 1 / 5 / 2;
    }
  }

  & > div {
    padding: 5px;

    & > div {
      border: 1px solid #aab2bd;
      position: relative;
    }
  }
}

#right_top {
  overflow: visible !important;
}

.hasGrid {
  .gutter-col {
    cursor: col-resize;
    position: relative;
    padding: 0 !important;
    width: 5px;

    &::after {
      position: absolute;
      height: 10px;
      width: 1px;
      background-color: gray;
      top: calc(50% - 5px);
      left: 2px;

      content: ' ';
    }
  }

  .gutter-row {
    cursor: row-resize;
    position: relative;
    padding: 0 !important;
    height: 5px;

    &::before {
      position: absolute;
      height: 1px;
      width: 10px;
      background-color: gray;
      top: 2px;
      left: calc(25% - 5px);

      content: ' ';
    }

    &:not(.onlyDocCall)::after {
      position: absolute;
      height: 1px;
      width: 10px;
      background-color: gray;
      top: 2px;
      right: calc(25% - 5px);

      content: ' ';
    }
  }
}

.g {
  display: flex;
  flex-direction: column;
  justify-content: stretch;

  &:not(.noMoreModules) {
    > div:first-child {
      height: 34px;
      flex: 1 1 34px;
      width: 100%;
    }

    > div:not(:first-child) {
      flex: 1 calc(100% - 34px);
      height: calc(100% - 34px);
      width: 100%;
    }

    &:not(.onlyDocCall) {
      > div:first-child {
        border: none !important;
      }

      > div:not(:first-child) {
        border-top: none;
      }
    }
  }

  &.noMoreModules {
    > div:first-child {
      flex: 1 100%;
      height: 100%;
      width: 100%;
    }
  }
}

.monitoring-body {
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
