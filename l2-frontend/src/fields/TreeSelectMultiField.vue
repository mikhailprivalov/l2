<template>
  <Treeselect
    v-model="val"
    :multiple="true"
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
      val: [],
      variantsLocal: [],
    };
  },
  computed: {
    variantsTree() {
      return this.variantsLocal.map(v => ({ id: v, label: v }));
    },
  },
  watch: {
    val: {
      deep: true,
      handler() {
        this.changeValue(this.val);
      },
    },
    value: {
      immediate: true,
      handler() {
        try {
          this.val = JSON.parse(this.value);

          if (!Array.isArray(this.val)) {
            this.val = [];
          }
        } catch (e) {
          this.val = [];
        }
      },
    },
    variants: {
      immediate: true,
      handler() {
        this.variantsLocal = Array.isArray(this.variants) ? this.variants : this.variants.split('\n');
        this.val = this.val.filter(v => this.variantsLocal.includes(v));
      },
    },
  },
  methods: {
    changeValue(newVal) {
      this.$emit('modified', JSON.stringify(newVal));
    },
  },
};
</script>
