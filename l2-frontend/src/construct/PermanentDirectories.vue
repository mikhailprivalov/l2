<template>
  <div class="wrapper-component">
    <treeselect
      v-model="code"
      :multiple="false"
      :disable-branch-nodes="true"
      :options="permanent_directories_keys"
      placeholder="Справочник не выбран"
      @select="saveDirectory"
    />
    <a
      href="#"
      class="a-under"
      @click.prevent="open = !open"
    >
      Варианты (кол-во: {{ variantsCount }})
    </a>
    <ul v-if="open">
      <li
        v-for="(v, k) in variants"
        :key="k"
      >
        {{ k }} – {{ v }}
      </li>
    </ul>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

@Component({
  components: { Treeselect },
  props: {
    row: {
      type: Object,
      required: true,
    },
    permanent_directories_keys: {
      type: Array,
      required: true,
    },
    permanent_directories: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      code: -1,
      title: '',
      open: false,
    };
  },
  watch: {
    code() {
      this.row.values_to_input = [this.code];
    },
    title() {
      this.row.title = this.title;
    },
  },
  mounted() {
    // eslint-disable-next-line prefer-destructuring
    this.code = this.row.values_to_input[0];
    this.title = this.row.title;
    if (!this.permanent_directories_keys.find(k => k.id === this.code) && this.permanent_directories_keys.length > 0) {
      const { id, label } = this.permanent_directories_keys[0];
      this.code = id;
      this.title = label;
    }
  },
})
export default class PermanentDirectories extends Vue {
  row: any;

  permanent_directories_keys: any;

  permanent_directories: any;

  code: string | number;

  title: string;

  open: boolean;

  get variants() {
    return this.permanent_directories[this.code]?.values || {};
  }

  get variantsCount() {
    return Object.keys(this.variants).length;
  }

  saveDirectory(node: any) {
    this.code = node.id;
    this.title = node.label;
  }
}
</script>

<style scoped lang="scss">
.wrapper-component {
  margin-top: 5px;
}
</style>
