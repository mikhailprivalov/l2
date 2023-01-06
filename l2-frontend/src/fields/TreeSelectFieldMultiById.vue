<template>
  <Treeselect
    v-model="val"
    :multiple="true"
    :disable-branch-nodes="true"
    class="treeselect-wide"
    :options="variants"
    label="label"
    :append-to-body="true"
    :clearable="false"
    :disabled="disabled"
    :z-index="5001"
  />
</template>

<script lang="ts">
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

export default {
  components: {
    Treeselect,
  },
  model: {
    event: 'modified',
  },
  props: {
    value: {
      type: Array,
      required: false,
    },
    variants: {
      type: Array,
      required: true,
    },
    disabled: {
      required: false,
      default: false,
      type: Boolean,
    },
  },
  data() {
    return {
      val: this.value,
    };
  },
  watch: {
    val() {
      this.changeValue(this.val);
    },
    value() {
      this.val = this.value;
    },
  },
  methods: {
    changeValue(newVal) {
      this.$emit('modified', newVal);
    },
  },
};
</script>
