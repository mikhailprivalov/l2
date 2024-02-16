<template>
  <RadioField
    v-model="val"
    :variants="DIRECTION_MODES"
    :bages="bages"
  />
</template>

<script lang="ts">
import RadioField from '@/fields/RadioField.vue';
import {
  DIRECTION_MODE_CALL,
  DIRECTION_MODE_DIRECTION,
  DIRECTION_MODE_ECP_REGISTRATION,
  DIRECTION_MODE_WAIT,
} from '@/constants';

export default {
  name: 'DirectAndPlanSwitcher',
  components: { RadioField },
  model: {
    event: 'modified',
  },
  props: {
    value: {
      type: String,
      required: false,
    },
    bages: {
      type: Object,
      required: false,
      default: () => ({}),
    },
  },
  data() {
    return {
      val: this.value,
    };
  },
  computed: {
    l2_list_wait() {
      return this.$store.getters.modules.l2_list_wait;
    },
    l2_doc_call() {
      return this.$store.getters.modules.l2_doc_call;
    },
    rmis_queue() {
      return this.$store.getters.modules.l2_rmis_queue;
    },
    schedule_in_protocol() {
      return this.$store.getters.modules.l2_schedule_in_protocol;
    },
    DIRECTION_MODES() {
      const modes = [
        DIRECTION_MODE_DIRECTION,
      ];
      if (this.rmis_queue || this.schedule_in_protocol) {
        modes.push(DIRECTION_MODE_ECP_REGISTRATION);
      }
      if (this.l2_doc_call) {
        modes.push(DIRECTION_MODE_CALL);
      }
      if (this.l2_list_wait) {
        modes.push(DIRECTION_MODE_WAIT);
      }
      return modes;
    },
  },
  watch: {
    val: {
      handler() {
        this.$emit('modified', this.val);
      },
      immediate: true,
    },
  },
};
</script>
