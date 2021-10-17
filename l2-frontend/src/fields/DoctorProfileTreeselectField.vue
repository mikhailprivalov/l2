<template>
  <Treeselect
    :multiple="false"
    :disable-branch-nodes="true"
    class="treeselect-wide treeselect-34px"
    :async="true"
    :append-to-body="true"
    :clearable="true"
    :disabled="disabled"
    :value="content"
    :zIndex="5001"
    placeholder="Профиль врача"
    :load-options="loadOptions"
    @select="selectValue"
    loadingText="Загрузка"
    noResultsText="Не найдено"
    searchPromptText="Начните писать для поиска"
    :cache-options="false"
    openDirection="top"
    :openOnFocus="true"
    @input="input"
  >
    <div slot="value-label" slot-scope="{ node }">{{ node.raw.label || node.raw.id }}</div>
  </Treeselect>
</template>

<script lang="ts">
import Treeselect, { ASYNC_SEARCH } from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

export default {
  props: {
    value: String,
    json: {
      type: Boolean,
      default: false,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  components: {
    Treeselect,
  },
  data() {
    return {
      content: '',
      detailsData: {},
    };
  },
  watch: {
    value: {
      immediate: true,
      handler() {
        let data: any = {};
        try {
          data = JSON.parse(this.value);
          this.content = data.fio;
        } catch (e) {
          if (this.value && !this.value.includes('{')) {
            this.content = this.value;
          }
        }
        this.detailsData = data;
      },
    },
    detailsData: {
      deep: true,
      handler() {
        this.emit();
      },
    },
  },
  model: {
    event: 'input',
  },
  methods: {
    emit() {
      const v = Object.keys(this.detailsData).length > 0 ? JSON.stringify(this.detailsData) : '';
      this.$emit('input', v || '');
    },
    async loadOptions({ action, searchQuery, callback }) {
      if (action === ASYNC_SEARCH) {
        const { data } = await this.$api(`/doctorprofile-search?query=${searchQuery}`);
        callback(
          null,
          data.map(d => ({ ...d, label: d.fio })),
        );
      }
    },
    selectValue(node) {
      const { label, ...nodeRest } = node;
      this.content = node.label;
      this.detailsData = nodeRest;
    },
    input(v) {
      if (!v) {
        this.content = '';
        this.detailsData = {};
      }
    },
  },
};
</script>
