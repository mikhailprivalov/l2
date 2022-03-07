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
    :z-index="5001"
    placeholder="Профиль врача"
    :load-options="loadOptions"
    loading-text="Загрузка"
    no-results-text="Не найдено"
    search-prompt-text="Начните писать для поиска"
    :cache-options="false"
    open-direction="top"
    :open-on-focus="true"
    @select="selectValue"
    @input="input"
  >
    <div
      slot="value-label"
      slot-scope="{ node }"
    >
      {{ node.raw.label || node.raw.id }}
    </div>
  </Treeselect>
</template>

<script lang="ts">
import Treeselect, { ASYNC_SEARCH } from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

export default {
  components: {
    Treeselect,
  },
  model: {
    event: 'input',
  },
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
    sign_org: {
      type: Boolean,
      default: false,
    },
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
  methods: {
    emit() {
      const v = Object.keys(this.detailsData).length > 0 ? JSON.stringify(this.detailsData) : '';
      this.$emit('input', v || '');
    },
    async loadOptions({ action, searchQuery, callback }) {
      if (action === ASYNC_SEARCH) {
        const { data } = await this.$api(`/doctorprofile-search?query=${searchQuery}&signOrg=${this.sign_org}`);
        callback(
          null,
          data.map((d) => ({ ...d, label: d.fio })),
        );
      }
    },
    selectValue(node) {
      const { label, ...nodeRest } = node;
      this.content = label;
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
