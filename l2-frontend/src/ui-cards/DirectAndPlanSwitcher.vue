<template>
  <radio-field v-model="val" :variants="DIRECTION_MODES" :bages="bages"/>
</template>

<script>
  import RadioField from "@/fields/RadioField";
  import {DIRECTION_MODES} from "@/constants";

  export default {
    name: "DirectAndPlanSwitcher",
    components: {RadioField},
    props: {
      value: {
        type: String,
        required: false,
      },
      bages: {
        type: Object,
        required: false,
        default: () => {},
      },
    },
    data() {
      return {
        DIRECTION_MODES,
        val: this.value || DIRECTION_MODES[0],
      }
    },
    watch: {
      val: {
        handler() {
          this.$emit('modified', this.val);
        },
        immediate: true,
      },
    },
    model: {
      event: 'modified',
    },
  }
</script>
