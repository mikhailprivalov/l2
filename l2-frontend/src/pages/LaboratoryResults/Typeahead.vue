<template>
  <input
    :id="id"
    ref="input"
    v-bind="$attrs"
    :value="value"
    :placeholder="placeholder"
    @input="updateValue($event.target.value)"
    @change="updateValue($event.target.value)"
    @focus="updateValue($event.target.value); focus();"
    @blur="formatValue(); blur();"
    @keyup.enter="keyupEnter"
  >
</template>

<script lang="ts">
import Vue from 'vue';
import Bloodhound from 'typeahead.js';

export default {
  props: {
    value: {
      type: String,
      default: '',
    },
    displayKey: {
      type: String,
      default: '',
    },
    suggestionTemplate: {
      type: String,
      default: '',
    },
    name: {
      type: String,
      default: 'Vue Auto Complete',
    },
    prefetch: {
      type: String,
      default: '',
    },
    defaultSuggestion: {
      type: Boolean,
      default: false,
    },
    remote: {
      type: String,
      default: '',
    },
    placeholder: {
      type: String,
      default: '',
    },
    local: {
      type: Array,
      default() {
        return [];
      },
    },
    responseWrapper: {
      type: String,
      default: '',
    },
    keyupEnter: {
      type: Function,
      required: false,
    },
    hide: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      id: this.$attrs.id || `typeahead-suggestion${Math.floor(Math.random() * 100000)}`,
      defaultSuggestions: [],
      query: '',
      forceOpenAfterHide: false,
    };
  },
  watch: {
    local(newVal) {
      if (this.defaultSuggestion) {
        this.defaultSuggestions = [...newVal];
      }
      this.resetTypeahead();
    },
    value(val) {
      window.$(`#${this.id}`).typeahead('val', val);
    },
    hide() {
      if (this.hide) {
        window.$(`#${this.id}`).typeahead('close');
      } else if (this.forceOpenAfterHide) {
        window.$(`#${this.id}`).typeahead('open');
      }
    },
    id: {
      handler() {
        this.$emit('set-id', this.id);
      },
      immediate: true,
    },
  },
  mounted() {
    this.initTypeahead();
    if (this.local.length) {
      this.defaultSuggestions = [...this.local];
    }
  },
  methods: {
    updateValue(value) {
      this.$emit('input', value);
    },
    formatValue() {
      this.$refs.input.value = this.value;
    },
    focus() {
      this.forceOpenAfterHide = true;
    },
    blur() {
      this.forceOpenAfterHide = false;
    },
    transformer(responseOrig) {
      let response = responseOrig;
      if (this.responseWrapper) {
        response = response[this.responseWrapper];
      }
      if (this.defaultSuggestion && this.local.length === 0) {
        this.defaultSuggestions = response.splice(0, 5);
      }
      return response;
    },
    bloodhoundOption() {
      let bloodhoundConfig = {};
      if (this.prefetch) {
        let prefetch = {
          cache: false,
          url: this.prefetch,
          transform: null,
        };
        if (this.defaultSuggestion) {
          prefetch = { ...prefetch, transform: this.transformer };
        }
        bloodhoundConfig = { prefetch };
      }
      if (this.local) {
        bloodhoundConfig = {
          local: this.local,
          ...bloodhoundConfig,
        };
      }
      if (this.remote) {
        bloodhoundConfig = {
          remote: {
            url: this.remote,
            wildcard: '%QUERY',
            transform: this.transformer,
          },
          ...bloodhoundConfig,
        };
      }
      return bloodhoundConfig;
    },
    parseTemplate(data) {
      const res = Vue.compile(this.suggestionTemplate);
      const vm = new Vue({
        data,
        render: res.render,
        staticRenderFns: res.staticRenderFns,
      }).$mount();
      return vm.$el;
    },
    getSource() {
      const bloodhoundConfig = this.bloodhoundOption();
      const datumTokenizer = this.displayKey ? Bloodhound.tokenizers.obj.whitespace(this.displayKey)
        : Bloodhound.tokenizers.whitespace;
      const engine = new Bloodhound({
        datumTokenizer,
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        ...bloodhoundConfig,
      });
      const source = (q, sync, a) => {
        if (q === '' && this.defaultSuggestions.length > 0 && this.defaultSuggestion) {
          sync(this.defaultSuggestions);
        } else {
          engine.search(q, sync, a);
        }
      };
      return this.defaultSuggestion ? source : engine;
    },
    resetTypeahead() {
      window.$(`#${this.id}`).typeahead('destroy');
      this.initTypeahead();
    },
    initTypeahead() {
      let templates = {};
      if (this.suggestionTemplate) {
        templates = { suggestion: this.parseTemplate };
      }
      const dataset = {
        name: 'Typeahead-Suggestion',
        display: this.displayKey,
        source: this.getSource(),
        limit: Infinity,
        templates,
      };
      window.$(`#${this.id}`).typeahead({
        minLength: 0,
        highlight: true,
      }, dataset)
        .on('typeahead:select', (event, suggession) => {
          this.$emit('input', this.displayKey ? suggession[this.displayKey] : suggession);
          this.$emit('selected', suggession);
        });
    },
  },
};
</script>

<style scoped lang="scss">
.tt-hint {
  opacity: 0 !important;
}
</style>
