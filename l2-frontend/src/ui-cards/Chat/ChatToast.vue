<template>
  <div
    class="message-toast"
  >
    <div class="message-toast__content">
      <div class="message-toast__content__title">
        Сообщение от {{ author }}
      </div>
      <div
        class="message-toast__content__text"
      >
        {{ text }}
      </div>
    </div>
    <div class="message-toast__buttons">
      <div
        v-tippy
        class="message-toast__button toast__button--open-dialog"
        title="Открыть диалог"
        @click="$emit('openDialog'); $emit('close-toast')"
      >
        <i class="fa fa-comments" />
      </div>
      <div
        class="message-toast__button toast__button--close"
        @click="$emit('close-toast')"
      >
        <i class="fa fa-times" />
      </div>
    </div>
  </div>
</template>

<script lang="ts">
export default {
  name: 'ChatToast',
  props: {
    author: {
      type: String,
      required: true,
    },
    text: {
      type: String,
      required: true,
    },
  },
};
</script>

<style scoped lang="scss">
.message-toast {
  background-color: rgba(0, 0, 0, 0.88);
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
  border-radius: 5px;
  padding: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #fff;
  cursor: pointer;

  &__content {
    flex: 1;
    width: 280px;

    &__title {
      font-weight: bold;
      margin-bottom: 10px;
    }

    &__text {
      margin-right: 10px;
      overflow: hidden;
      text-overflow: ellipsis;
      max-height: 100px;
    }
  }

  &__buttons {
    display: flex;
    align-items: center;
  }

  &__button {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background-color: #f5f5f5;
    margin-left: 5px;
    cursor: pointer;
    color: #000;

    &:hover {
      background-color: #e5e5e5;
    }

    &:active {
      background-color: #d5d5d5;
    }
  }
}
</style>
