<template>
  <textarea
    ref="input"
    v-model="text"
    class="input-textarea"
    :placeholder="
      selfDialog
        ? 'Введите сообщение для отправки себе'
        : 'Введите сообщение (Ctrl+Enter для отправки)'
    "
    :readonly="disabled"
    maxlength="999"
    @keydown.ctrl.enter="send"
  />
</template>

<script lang="ts">
export default {
  name: 'ChatInput',
  props: {
    selfDialog: {
      type: Boolean,
      default: false,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      text: '',
    };
  },
  computed: {
    textSymbolsLeft() {
      return 999 - this.text.length;
    },
  },
  watch: {
    text() {
      if (this.text) {
        if (this.textSymbolsLeft <= 0) {
          this.text = this.text.slice(0, 999);
        } else {
          this.$emit('typing');
        }
      }
    },
  },
  methods: {
    send() {
      if (this.text) {
        this.$emit('send', this.text, this.onResult);
      }
    },
    onResult(result: boolean) {
      if (result) {
        this.text = '';
      }
      this.$nextTick(() => {
        this.focus();
      });
    },
    focus() {
      this.$refs.input.focus();
    },
  },
};
</script>

<style lang="scss" scoped>
.input-textarea {
  position: absolute;
  top: 0;
  left: 0;
  width: calc(100% - 40px);
  height: 100%;
  padding: 5px;
  border: none;
  outline: none;
  resize: none;
  font-size: 14px;
  line-height: 1.1;
}
</style>
