<template>
  <div v-frag>
    <textarea
      :readonly="confirmed"
      :rows="lines"
      class="form-control"
      v-if="lines > 1"
      v-model="content"
      @focus="changeFocused(true)"
      @blur="changeFocused(false)"
      ref="t"
    ></textarea>
    <input
      :readonly="confirmed"
      class="form-control"
      v-else
      v-model="content"
      @focus="changeFocused(true)"
      @blur="changeFocused(false)"
      ref="t"
    />
    <div v-if="focused && suggests.length > 0 && !confirmed" class="text-suggests">
      <div class="suggestion-template" v-for="s in suggests" @click.capture="selectSuggestion(s)" v-html="s" :key="s" />
      <div class="suggests-header">
        Предложения по вашим шаблонам <span>(<a href="#" class="a-under" @click.prevent="templatesOpen">настроить</a>)</span>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { debounce } from 'lodash/function';

export default {
  name: 'TextFieldWithTemplates',
  props: {
    value: String,
    fieldPk: Number,
    lines: Number,
    confirmed: Boolean,
  },
  data() {
    return {
      content: this.value,
      focused: false,
      suggests: [],
      focusTimeout: null,
    };
  },
  watch: {
    value() {
      this.content = this.value;
    },
    content() {
      this.suggests = [];
      this.$emit('modified', this.content);
      this.loadSuggestsDebounced();
    },
  },
  model: {
    event: 'modified',
  },
  methods: {
    templatesOpen() {
      this.$root.$emit(`templates-open:${this.fieldPk}`);
    },
    changeFocused(f) {
      if (this.focusTimeout) {
        clearTimeout(this.focusTimeout);
      }
      if (f) {
        this.focused = true;
      } else {
        this.focusTimeout = setTimeout(() => {
          this.focused = false;
        }, 120);
      }
    },
    async loadSuggests() {
      this.suggests = [];
      if (!this.focused || this.confirmed || !this.content) {
        return;
      }

      const { rows, value } = await this.$api('/input-templates/suggests', { pk: this.fieldPk, value: this.content });
      if (this.content === value) {
        this.suggests = rows;
      }
    },
    loadSuggestsDebounced: debounce(function () {
      this.suggests = [];
      this.loadSuggests();
    }, 300),
    selectSuggestion(s) {
      this.content = s;
      if (this.$refs.t) {
        window.$(this.$refs.t).focus();
      }
    },
  },
};
</script>

<style lang="scss" scoped>
.text-suggests {
  position: absolute;
  top: 100%;
  left: 5px;
  right: 5px;
  background: #fff;
  padding: 5px;
  border-radius: 0 0 5px 5px;
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.16), 0 3px 6px rgba(0, 0, 0, 0.23);
  z-index: 5;
}

.suggestion-template {
  padding: 5px;
  background-color: rgba(0, 0, 0, 6%);
  border-radius: 4px;
  cursor: pointer;
  white-space: pre-line;

  &:hover {
    background-color: rgba(0, 0, 0, 14%);
  }

  & + & {
    margin-top: 5px;
  }
}

.suggests-header {
  font-weight: bold;
  margin-top: 5px;
  font-size: 12px;

  span {
    font-weight: normal;
  }
}
</style>
