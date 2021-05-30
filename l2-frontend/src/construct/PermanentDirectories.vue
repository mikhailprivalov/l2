<template>
    <treeselect v-if="row.field_type === 10" :multiple="false" :disable-branch-nodes="true"
                :options="permanent_directories_keys"  placeholder="Справочник не выбран" @select="saveDirectories"/>
</template>

<script>
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

export default {
  name: 'PermanentDirectories',
  components: { Treeselect },
  props: {
    row: {},
    permanent_directories_keys: {
      type: Array,
      required: false,
    },
    permanent_directories: {
      type: Object,
      required: false,
    },
  },
  data() {
    return {
      result: [],
      title: '',
    };
  },
  watch: {
    result: {
      deep: true,
      handler() {
        this.row.values_to_input = this.result;
        this.row.title = this.title;
      },
    },
  },
  methods: {
    saveDirectories(node) {
      this.result = this.permanent_directories[node.label];
      this.title = node.label;
    },
  },
};
</script>
