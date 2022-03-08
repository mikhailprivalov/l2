<template>
  <Treeselect
    v-model="val"
    :multiple="false"
    :disable-branch-nodes="true"
    class="treeselect-wide"
    :options="variantsTree"
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
      required: false,
    },
    variants: {
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
      variantsLocal: [],
    };
  },
  computed: {
    variantsTree() {
      return this.variantsLocal.map(v => ({ id: v, label: v }));
    },
  },
  watch: {
    val() {
      this.changeValue(this.val);
    },
    variants: {
      immediate: true,
      handler() {
        this.variantsLocal = Array.isArray(this.variants) ? this.variants : this.variants.split('\n');
        if ((!this.val || !this.variantsLocal.includes(this.val)) && this.variantsLocal.length > 0) {
          // eslint-disable-next-line prefer-destructuring
          this.val = this.variantsLocal[0];
        }
      },
    },
  },
  methods: {
    changeValue(newVal) {
      this.$emit('modified', newVal);
    },
  },
};
</script>
