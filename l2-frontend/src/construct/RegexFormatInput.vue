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
      const newContent = this.content.replace(this.rules, '');
      if (newContent === this.content) {
        this.$emit('input', this.content);
      } else {
        this.content = newContent;
      }
    },
  },
};
</script>
