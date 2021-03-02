<template>
  <input ref="input"
         v-bind="$attrs"
         :id="id"
         :value="value"
         @input="updateValue($event.target.value)"
         @blur="formatValue"
         @keyup.enter="keyupEnter"
         :placeholder="placeholder"
  >
</template>
<script>
import Bloodhound from 'typeahead.js';

export default {
  data() {
    return {
      id: this.$attrs.id || `typeahead-suggestion${Math.floor(Math.random() * 100000)}`,
      defaultSuggestions: [],
      query: ''
    };
  },
  props: {
    value: {
      type: String,
      default: ''
    },
    displayKey: {
      type: String,
      default: ''
    },
    suggestionTemplate: {
      type: String,
      default: ''
    },
    name: {
      type: String,
      default: 'Vue Auto Complete'
    },
    prefetch: {
      type: String,
      default: ''
    },
    defaultSuggestion: {
      type: Boolean,
      default: false
    },
    remote: {
      type: String,
      default: ''
    },
    placeholder: {
      type: String,
      default: ''
    },
    local: {
      type: Array,
      default: function () {
        return []
      }
    },
    responseWrapper: {
      type: String,
      default: ''
    },
    keyupEnter: {
      type: Function,
      required: false,
    },
  },
  watch: {
    local(newVal) {
      if (this.defaultSuggestion) {
        this.defaultSuggestions = [...newVal];
      }
      this.resetTypeahead();
    }
  },
  mounted() {
    this.initTypeahead();
    if (this.local.length) {
      this.defaultSuggestions = [...this.local];
    }
  },
  methods: {
    updateValue(value) {
      this.$emit('input', value)
    },
    formatValue() {
      this.$refs.input.value = this.value;
    },
    transformer(response) {
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
          url: this.prefetch
        };
        if (this.defaultSuggestion) {
          prefetch = {...prefetch, transform: this.transformer};
        }
        bloodhoundConfig = {prefetch};
      }
      if (this.local) {
        bloodhoundConfig = {
          local: this.local,
          ...bloodhoundConfig
        }
      }
      if (this.remote) {
        bloodhoundConfig = {
          remote: {
            url: this.remote,
            wildcard: '%QUERY',
            transform: this.transformer
          },
          ...bloodhoundConfig
        }
      }
      return bloodhoundConfig;
    },
    parseTemplate(data) {
      const res = Vue.compile(this.suggestionTemplate);
      const vm = new Vue({
        data,
        render: res.render,
        staticRenderFns: res.staticRenderFns
      }).$mount();
      return vm.$el;
    },
    getSource() {
      const self = this;
      const bloodhoundConfig = this.bloodhoundOption();
      const datumTokenizer = this.displayKey ? Bloodhound.tokenizers.obj.whitespace(this.displayKey)
        : Bloodhound.tokenizers.whitespace;
      const engine = new Bloodhound({
        datumTokenizer,
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        ...bloodhoundConfig
      });
      const source = function (q, sync, async) {
        if (q === '' && self.defaultSuggestions.length > 0 && self.defaultSuggestion) {
          sync(self.defaultSuggestions);
        } else {
          engine.search(q, sync, async);
        }
      };
      return this.defaultSuggestion ? source : engine;
    },
    resetTypeahead() {
      $(document).find('#' + this.id).typeahead('destroy');
      this.initTypeahead();
    },
    initTypeahead() {
      const self = this;
      let templates = {};
      if (this.suggestionTemplate) {
        templates = {suggestion: self.parseTemplate}
      }
      const dataset = {
        name: 'Typeahead-Suggestion',
        display: this.displayKey,
        source: this.getSource(),
        limit: Infinity,
        templates
      };
      $(document).find('#' + self.id).typeahead({
        minLength: 0,
        highlight: true
      }, dataset)
        .on('typeahead:select', function (event, suggession) {
          self.$emit('input', self.displayKey ? suggession[self.displayKey] : suggession)
          self.$emit('selected', suggession);
        });
    }
  }
}
</script>
