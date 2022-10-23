<template>
  <li v-if="rmis_queue">
    <a
      href="#"
      @click.prevent="doOpen"
    > Записать </a>
    <Modal
      v-if="open"
      ref="modal"
      show-footer="true"
      white-bg="true"
      max-width="1600px"
      width="100%"
      margin-left-right="41px"
      margin-top
      class="an"
      @close="hide_window"
    >
      <span slot="header">Записать пациента</span>
      <div
        slot="body"
        class="an-body"
      >
        <div class="d-root">
          <div>
            <div class="overflow-visible">
              <PatientPicker
                v-model="selected_card"
                history_n="false"
                :hide_card_editor="true"
              />
            </div>
          </div>
          <div>
            <div>
              <DirectionsHistory
                :patient_pk="selected_card.pk"
                :only-type="6"
                kk="ecp"
              />
            </div>
          </div>
          <div>
            <div>
              <ResearchesPicker
                v-model="selected_researches"
                :hidetemplates="true"
                :autoselect="false"
                :types-only="[4, 3, 7]"
                kk="ecp"
                :just_search="true"
              />
            </div>
          </div>
          <div class="schedule-container">
            <div
              v-if="selected_card.pk"
              class="schedule-root"
            >
              <ServiceScheduleEcp
                v-for="r in selected_researches"
                :key="r"
                :service-pk="r"
                :card-id="selected_card.pk"
                @fill-slot-ok="deselect"
              />
            </div>
          </div>
        </div>
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-4">
            <button
              class="btn btn-primary-nb btn-blue-nb"
              type="button"
              @click="hide_window"
            >
              Закрыть
            </button>
          </div>
        </div>
      </div>
    </Modal>
  </li>
</template>

<script lang="ts">
import { mapGetters } from 'vuex';

import Modal from '@/ui-cards/Modal.vue';
import ResearchesPicker from '@/ui-cards/ResearchesPicker.vue';
import PatientPicker from '@/ui-cards/PatientPicker.vue';
import ServiceScheduleEcp from '@/ui-cards/ServiceScheduleEcp.vue';
import DirectionsHistory from '@/ui-cards/DirectionsHistory/index.vue';

export default {
  name: 'EcpSchedule',
  components: {
    PatientPicker,
    ServiceScheduleEcp,
    ResearchesPicker,
    DirectionsHistory,
    Modal,
  },
  data() {
    return {
      open: false,
      args_to_preselect: null,
      selected_card: {},
      selected_researches: [],
    };
  },
  computed: {
    rmis_queue() {
      return this.$store.getters.modules.l2_rmis_queue;
    },
    card_pk() {
      return this.selected_card.pk || null;
    },
    ...mapGetters({
      bases: 'bases',
    }),
    bases_obj() {
      return this.bases.reduce(
        (a, b) => ({
          ...a,
          [b.pk]: b,
        }),
        {},
      );
    },
    internal_base() {
      for (const b of this.bases) {
        if (b.internal_type) {
          return b.pk;
        }
      }
      return -1;
    },
  },
  mounted() {
    this.$root.$on('preselect-args', (data) => {
      if (!data) {
        this.args_to_preselect = null;
      } else {
        this.args_to_preselect = data;
      }
    });
    this.$root.$emit('preselect-args-ok');
    this.$root.$on('fill-slot-ok', () => this.hide_window());
  },
  methods: {
    doOpen() {
      this.open = true;
      if (this.args_to_preselect) {
        const data = { ...this.args_to_preselect, hide: true };
        setTimeout(() => this.$root.$emit('select_card', data), 100);
      }
      this.$root.$emit('no-loader-in-header', true);
    },
    hide_window() {
      this.open = false;
      this.research = null;
      this.selected_card = {};
      this.$root.$emit('no-loader-in-header', false);
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
    },
    deselect(researchPk) {
      this.$root.$emit('researches-picker:deselectecp', researchPk);
    },
  },
};
</script>

<style scoped lang="scss">
.an-body {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  height: 100%;
  display: block;
}

.an-body > div {
  align-self: stretch;
}

.d-root {
  height: 100%;
  display: flex;
  flex-wrap: wrap;
  flex-direction: row;

  > div {
    flex-basis: calc(50% - 8px);
    margin: 4px;

    > div {
      height: 100%;
      border: 1px solid rgba(0, 0, 0, 0.3);
      overflow-x: hidden;
      overflow-y: auto;

      &.overflow-visible {
        overflow: visible;
      }
    }
  }
}

.schedule-container {
  position: relative;
}

.schedule-root {
  padding: 10px;
  position: absolute;
  top: 0 !important;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: auto;

  & > ::v-deep div {
    margin-bottom: 15px;
  }
}
</style>
