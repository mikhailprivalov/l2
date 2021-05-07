<template>
  <radio-field v-model="val" :variants="DIRECTION_MODES" :bages="bages"/>
</template>

<script>
import RadioField from '@/fields/RadioField.vue';
import {
  DIRECTION_MODE_DIRECTION,
  DIRECTION_MODE_CALL,
  DIRECTION_MODE_WAIT,
} from '@/constants';

export default {
  name: 'DirectAndPlanSwitcher',
  components: { RadioField },
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
  watch: {
    val: {
      handler() {
        this.$emit('modified', this.val);
      },
      immediate: true,
    },
  },
  computed: {
    l2_list_wait() {
      return this.$store.getters.modules.l2_list_wait;
    },
    l2_doc_call() {
      return this.$store.getters.modules.l2_doc_call;
    },
    DIRECTION_MODES() {
      const modes = [
        DIRECTION_MODE_DIRECTION,
      ];
      if (this.l2_doc_call) {
        modes.push(DIRECTION_MODE_CALL);
      }
      if (this.l2_list_wait) {
        modes.push(DIRECTION_MODE_WAIT);
      }
      return modes;
    },
  },
  model: {
    event: 'modified',
  },
};
</script>
