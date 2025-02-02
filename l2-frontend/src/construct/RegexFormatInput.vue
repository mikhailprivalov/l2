<template>
  <input
    v-model="content"
  >
</template>

<script>
export default {
  name: 'RegexFormatInput',
  props: {
    value: {
      type: String,
    },
    rules: {
      type: RegExp,
      required: true,
    },
    reverseMode: {
      type: Boolean,
      reqired: false,
    },
  },
  data() {
    return {
      content: '',
    };
  },
  watch: {
    value: {
      handler() {
        this.content = this.value;
      },
      immediate: true,
    },
    content() {
      if (!this.reverseMode) {
        const newContent = this.content.replace(this.rules, '');
        if (newContent === this.content) {
          this.$emit('input', this.content);
        } else {
          this.content = newContent;
        }
      } else {
        const newContentValid = this.rules.test(this.content);
        if (!newContentValid) {
          this.content = this.content.slice(0, -1);
        } else {
          this.$emit('input', this.content);
        }
      }
    },
  },
};
</script>
