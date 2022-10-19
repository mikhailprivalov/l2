<template>
  <MountingPortal
    mount-to="#portal-place-modal"
    :name="`chat-dialog-${dialogId}`"
    append
  >
    <div
      ref="dialog"
      class="chat-dialog"
      :class="isDragging && 'chat-dialog-dragging'"
      :style="{
        '--topPx': topPx,
        '--leftPx': leftPx,
        zIndex: focused ? 1001 : 1000,
      }"
      @mousedown="unfocusOther"
    >
      <div
        class="chat-dialog__header"
        @mousedown="startDrag"
      >
        <div
          class="chat-dialog__header-title"
        >
          {{ dialogUserObj.name }}
          <template v-if="loaded">
            <div
              v-if="messagesLoading === 0"
              class="chat-dialog__header-online"
              :class="userIsOnline && 'chat-dialog__header-is-online'"
            >
              <i
                class="fa"
                :class="userIsOnline ? 'fa-circle' : 'fa-circle-o'"
              />
            </div>
            <div
              v-else
              class="chat-dialog__header-online"
              :class="userIsOnline && 'chat-dialog__header-is-online'"
            >
              <i class="fa fa-circle-o-notch fa-spin" />
            </div>
          </template>
        </div>
        <div
          v-if="dialogDepartmentTitle"
          class="chat-dialog__header-subheader-1"
        >
          {{ dialogDepartmentTitle }}
        </div>
        <div
          class="chat-dialog__header-subheader-2"
        >
          <div
            v-if="dialogUserObj.position || dialogUserObj.speciality"
            class="chat-dialog__header-position-and-speciality"
          >
            <template v-if="dialogUserObj.position">
              {{ `${dialogUserObj.position}${dialogUserObj.speciality ? ', ': ''}` }}
            </template>
            <template v-if="dialogUserObj.speciality">
              {{ dialogUserObj.speciality }}
            </template>
          </div>
          <div
            v-if="!userIsOnline && dialogUserObj.lastOnline"
            class="chat-dialog__header-last-online"
          >
            {{ dialogUserObj.lastOnline | unixTimestampToRelativeTime }} в сети
          </div>
          <div
            v-else-if="userIsOnline"
            class="chat-dialog__header-last-online"
          >
            сейчас в сети
          </div>
        </div>
        <div
          class="chat-dialog__header-close"
          @click="closeDialog"
        >
          <i class="fa fa-times" />
        </div>
      </div>
      <div class="chat-dialog__body">
        <div
          ref="messages"
          class="chat-dialog__body-messages"
          @scroll="onScroll"
        >
          <div
            v-if="messages.length && !noMoreMessages && !forceHideLoadMore"
            class="chat-dialog__body-messages-load-more"
            @click="loadMoreMessages()"
          >
            Загрузить ещё
          </div>
          <div
            v-for="message in messages"
            :key="message.id"
            class="chat-dialog__body-message"
            :class="newMessages.includes(message.id) && 'chat-dialog__body-message-new'"
          >
            <div
              class="chat-dialog__body-message-author"
              :class="message.author === currentUserPk && 'chat-dialog__body-message-author-current-user'"
            >
              {{ message.author === currentUserPk ? 'Вы' : dialogUserObj.name }}
            </div>
            <div
              class="chat-dialog__body-message-text"
              v-text="message.text"
            />
            <div
              class="chat-dialog__body-message-time"
            >
              <i
                v-if="message.read"
                class="fa fa-check-double chat-dialog__body-message-time-read"
              />
              <i
                v-else
                class="fa fa-check chat-dialog__body-message-time-unread"
              />
              {{ message.time | unixTimestampToLocalFormattedTime }}
            </div>
          </div>
          <div
            class="typing"
            :class="isWriting && 'typing--active'"
          >
            <div class="typing__text">
              Собеседник печатает
            </div>
            <div class="typing__dot" />
            <div class="typing__dot" />
            <div class="typing__dot" />
          </div>
        </div>
        <div
          class="chat-dialog__body-input"
        >
          <textarea
            ref="input"
            v-model.trim="text"
            class="chat-dialog__body-input-textarea"
            :placeholder="
              currentUserPk === dialogUser.id
                ? 'Введите сообщение для отправки себе'
                : 'Введите сообщение (Ctrl+Enter для отправки)'
            "
            :readonly="isSending"
            maxlength="500"
            @keydown.ctrl.enter="sendMessage"
            @keyup="updateWritingStatusDebounced"
          />
          <div
            class="chat-dialog__body-input-send"
            @click="sendMessage"
          >
            <i
              v-if="isSending"
              class="fa fa-spinner"
            />
            <i
              v-else
              class="fa fa-paper-plane"
            />
            <div
              v-if="textSymbolsLeft < 100"
              class="chat-dialog__body-input-send-symbols-left"
            >
              {{ textSymbolsLeft }}
            </div>
          </div>
        </div>
        <div
          v-if="scrollFromBottom > 25"
          class="chat-dialog__body-messages-to-bottom"
          @click="scrollToBottom"
        >
          <i class="fa fa-angle-down" />
        </div>
      </div>
    </div>
  </MountingPortal>
</template>

<script lang="ts">
import _ from 'lodash';

import * as actions from '@/store/action-types';

export default {
  name: 'ChatDialog',
  props: {
    dialogId: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      uniqInstance: _.uniqueId(`chat-dialog-${this.dialogId}-${Math.random()}-`),
      isSending: false,
      isDragging: false,
      loaded: false,
      loading: false,
      dialogUser: {},
      messages: [],
      text: '',
      top: 0,
      left: 0,
      scrollTop: 0,
      scrollFromBottom: 0,
      noMoreMessages: false,
      newMessages: [],
      messagesLoading: 0,
      forceHideLoadMore: false,
      readStatusesTimer: null,
      focused: false,
      isWriting: false,
      lsProperty: 'chat-dialog',
    };
  },
  computed: {
    currentUserPk() {
      return this.$store.getters.currentDocPk;
    },
    dialogDepartmentTitle() {
      return this.$store.getters.chatsGetUserDepartmentTitle(this.dialogUser.id);
    },
    dialogUserObj() {
      return this.$store.getters.chatsGetUser(this.dialogUser.id) || {};
    },
    userIsOnline() {
      return this.$store.getters.chatsGetUserIsOnline(this.dialogUser.id);
    },
    topPx() {
      return `${this.top}px`;
    },
    leftPx() {
      return `${this.left}px`;
    },
    unreadMessages() {
      if (!this.loaded || !this.dialogUser.id) {
        return [];
      }
      return this.messages.filter(
        (message) => (message.author !== this.currentUserPk || this.dialogUser.id === this.currentUserPk) && !message.read,
      ).map((message) => message.id);
    },
    unreadOtherUserMessages() {
      if (!this.loaded || !this.dialogUser.id) {
        return [];
      }
      return this.messages.filter(
        (message) => message.author === this.currentUserPk && this.dialogUser.id !== this.currentUserPk && !message.read,
      ).map((message) => message.id);
    },
    textSymbolsLeft() {
      return 500 - this.text.length;
    },
  },
  watch: {
    unreadMessages() {
      if (this.unreadMessages.length === 0) {
        return;
      }
      this.markMessagesAsRead(this.unreadMessages);
      this.messages = this.messages.map((message) => {
        if (this.unreadMessages.includes(message.id)) {
          return {
            ...message,
            read: true,
          };
        }
        return message;
      });
    },
    text() {
      if (this.textSymbolsLeft <= 0) {
        this.text = this.text.slice(0, 500);
      } else {
        this.updateWritingStatusDebounced();
      }
    },
  },
  mounted() {
    this.loadDialogData();
    this.top = Math.floor(Math.random() * (window.innerHeight / 2 - 200));
    this.left = Math.floor(Math.random() * (window.innerWidth / 2 - 200));
    this.$store.subscribeAction((action) => {
      if (action.type === actions.CHATS_NOTIFY && action.payload.dialogId === this.dialogId) {
        this.loadFeatureMessages();
        this.newMessages.push(action.payload.id);
        setTimeout(() => {
          this.newMessages = this.newMessages.filter((id) => id !== action.payload.id);
        }, 3000);
      }
    });
    this.$root.$on('chat-dialog-focus', dialogId => {
      this.focused = dialogId === this.dialogId;
    });
    window.addEventListener('storage', this.onStorageDialogEvent);
  },
  beforeDestroy() {
    clearTimeout(this.readStatusesTimer);
    window.removeEventListener('storage', this.onStorageDialogEvent);
  },
  methods: {
    onStorageDialogEvent(e) {
      if (!e.newValue) {
        return;
      }

      let payload: any = {};

      try {
        payload = JSON.parse(e.newValue);
      } catch (err) {
        console.error(err);
        return;
      }

      console.log(payload);

      if (
        payload?.dialogId
        && payload.instanceId
        && payload.instanceId !== this.uniqInstance
        && payload.dialogId === this.dialogId
      ) {
        this.loadFeatureMessages();
      }
    },
    onScroll() {
      this.scrollTop = this.$refs.messages.scrollTop;
      this.scrollFromBottom = this.$refs.messages.scrollHeight - this.$refs.messages.scrollTop - this.$refs.messages.clientHeight;
    },
    unfocusOther() {
      this.$root.$emit('chat-dialog-focus', this.dialogId);
    },
    async loadDialogData() {
      this.unfocusOther();
      this.loading = true;
      try {
        const { user, totalMessages } = await this.$api('chats/get-dialog-data', this, 'dialogId');
        this.dialogUser = user;
        this.totalMessages = totalMessages;
        this.loaded = true;
        this.messages = [];
        this.loading = false;
        const loadedMessages = await this.loadMoreMessages(true);
        this.$nextTick(() => {
          this.$refs.input.focus();
        });
        if (loadedMessages === totalMessages) {
          this.forceHideLoadMore = true;
        }
        await this.loadReadStatuses();
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error(e);
        this.loading = false;
      }
    },
    scrollToBottom() {
      setTimeout(() => {
        this.$refs.messages.scrollTop = this.$refs.messages.scrollHeight;
      }, 0);
    },
    closeDialog() {
      this.$store.dispatch(actions.CHATS_CLOSE_DIALOG, this.dialogId);
    },
    startDrag(e: MouseEvent) {
      e.preventDefault();
      this.isDragging = true;
      const { top, left } = this.$refs.dialog.getBoundingClientRect();
      const offsetX = e.clientX - left;
      const offsetY = e.clientY - top;

      const mouseMove = (e2: MouseEvent) => {
        e2.preventDefault();
        window.requestAnimationFrame(() => {
          this.top = e2.clientY - offsetY;
          if (this.top < 0) {
            this.top = 0;
          }
          if (this.top > window.innerHeight - 400) {
            this.top = window.innerHeight - 400;
          }
          this.left = e2.clientX - offsetX;
          if (this.left < 0) {
            this.left = 0;
          }
          if (this.left > document.documentElement.clientWidth - 400) {
            this.left = document.documentElement.clientWidth - 400;
          }
        });
      };
      const mouseUp = () => {
        this.isDragging = false;
        document.removeEventListener('mousemove', mouseMove);
        document.removeEventListener('mouseup', mouseUp);
      };
      document.addEventListener('mousemove', mouseMove);
      document.addEventListener('mouseup', mouseUp);
    },
    async sendMessage() {
      if (!this.text || this.isSending) {
        return;
      }
      this.isSending = true;
      try {
        const { message, ok } = await this.$api('chats/send-message', this, ['dialogId', 'text']);
        if (ok) {
          this.messages.push({ ...message, addedFromClient: true });
          this.text = '';
          this.$nextTick(() => {
            this.scrollToBottom();
            this.$refs.input.focus();
          });

          const dataToStore = {
            dialogId: this.dialogId,
            instanceId: this.uniqInstance,
          };
          window.localStorage[this.lsProperty] = JSON.stringify(dataToStore);
          setTimeout(() => {
            delete window.localStorage[this.lsProperty];
          }, 100);
        } else {
          this.$root.$emit('msg', 'error', 'Ошибка отправки сообщения');
        }
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error(e);
        this.$root.$emit('msg', 'error', 'Ошибка отправки сообщения');
      }
      this.isSending = false;
    },
    async loadMoreMessages(scrollToBottom) {
      this.messagesLoading++;
      const scrollHeightOrig = this.$refs.messages.scrollHeight;

      const lastMessageId = this.messages.length ? this.messages[0].id : -1;

      const { messages } = await this.$api('chats/get-messages', this, 'dialogId', { lastMessageId });

      if (messages.length === 0) {
        this.noMoreMessages = true;
        this.messagesLoading--;
        return 0;
      }

      this.messages.unshift(...messages);

      this.$nextTick(() => {
        setTimeout(() => {
          if (scrollToBottom) {
            this.$refs.messages.scrollTop = this.$refs.messages.scrollHeight - this.$refs.messages.clientHeight;
          } else {
            const scrollHeightNew = this.$refs.messages.scrollHeight;
            this.$refs.messages.scrollTop += scrollHeightNew - scrollHeightOrig;
          }
        }, 0);
      });
      this.messagesLoading--;

      return messages.length;
    },
    async loadFeatureMessages() {
      this.messagesLoading++;
      if (this.$refs.messages) {
        const isAtBottom = this.$refs.messages.scrollHeight
          - this.$refs.messages.scrollTop
          - this.$refs.messages.clientHeight < 20;

        const messages = this.messages.filter((m) => !m.addedFromClient);

        if (messages.length === 0) {
          this.messagesLoading--;
          return;
        }
        const lastMessageId = messages[messages.length - 1].id;

        const { messages: ms } = await this.$api('chats/get-messages-feature', this, 'dialogId', { lastMessageId });

        this.messages = [
          ...messages,
          ...ms,
        ];

        if (isAtBottom) {
          this.$nextTick(() => {
            setTimeout(() => {
              this.$refs.messages.scrollTop = this.$refs.messages.scrollHeight - this.$refs.messages.clientHeight;
            }, 0);
          });
        }
      }
      this.messagesLoading--;
    },
    async markMessagesAsRead(messageIds) {
      this.messagesLoading++;
      try {
        await this.$api('chats/read-messages', this, 'dialogId', {
          messageIds,
        });
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error(e);
      }
      this.messagesLoading--;
    },
    async loadReadStatuses() {
      try {
        const { statuses, isWriting } = await this.$api('chats/get-read-statuses', this, 'dialogId', {
          messageIds: this.unreadOtherUserMessages,
        });

        if (statuses.length !== 0) {
          this.messages = this.messages.map((m) => {
            const status = statuses.find((s) => s === m.id);
            if (status) {
              return {
                ...m,
                read: true,
              };
            }
            return m;
          });
        }

        this.isWriting = isWriting;
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error(e);
        this.isWriting = false;
      }

      this.readStatusesTimer = setTimeout(() => {
        this.loadReadStatuses();
      }, this.userIsOnline ? 3500 : 30000);
    },
    updateWritingStatus() {
      try {
        this.$api('chats/update-is-writing', this, 'dialogId');
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error(e);
      }
    },
    updateWritingStatusDebounced: _.debounce(function () {
      this.updateWritingStatus();
    }, 400, { leading: true, trailing: true }),
  },
};
</script>

<style lang="scss" scoped>
.chat-dialog {
  position: fixed;
  top: var(--topPx);
  left: var(--leftPx);
  width: 400px;
  height: 400px;
  background-color: #fff;
  border: 1px solid #ccc;
  border-radius: 5px;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
  overflow: hidden;
  z-index: 1000;
  display: flex;
  flex-direction: column;

  &-dragging {
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.8);
  }

  &__header {
    position: relative;
    min-height: 40px;
    background-color: #eee;
    border-bottom: 1px solid #ccc;
    cursor: move;
    flex-shrink: 0;

    &-title {
      margin-top: 3px;
      margin-bottom: 3px;
      text-align: left;
      font-size: 14px;
      font-weight: bold;
      padding: 0 40px 0 10px;
    }

    &-subheader-1, &-subheader-2 {
      line-height: 12px;
      margin-bottom: 5px;
      display: flex;
      align-items: center;
      padding: 0 40px 0 10px;
      font-size: 12px;
      color: #999;
    }

    &-subheader-2 {
      top: 40px;
    }

    &-position-and-speciality {
      padding-right: 5px;
      color: #666;
    }

    &-online {
      display: inline-block;
      font-size: 14px;
      padding-left: 3px;
    }

    &-is-online {
      color: #4caf50;
    }
  }

  &__header-close {
    position: absolute;
    top: 0;
    right: 0;
    width: 40px;
    height: 100%;
    line-height: 40px;
    text-align: center;
    font-size: 14px;
    font-weight: bold;
    cursor: pointer;
  }

  &__body {
    position: relative;
    overflow: hidden;
    flex: 1;
    padding-bottom: 60px;
  }

  &__body-messages {
    position: absolute;
    top: 0;
    right: 0;
    bottom: 60px;
    left: 0;
    overflow-y: auto;
    display: flex;
    flex-direction: column;

    &-load-more {
      height: 40px;
      line-height: 40px;
      text-align: center;
      font-size: 14px;
      font-weight: bold;
      cursor: pointer;
      color: #999;

      &:hover {
        color: #666;
      }
    }

    &-to-bottom {
      position: absolute;
      bottom: 75px;
      right: 20px;
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background-color: #fff;
      border: 1px solid #ccc;
      box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      font-weight: bold;
      color: #999;
      opacity: 0.8;

      &:hover {
        color: #666;
        opacity: 1;
      }
    }
  }

  &__body-message {
    position: relative;
    padding: 5px 5px 11px 10px;
    border-top: 1px solid #ccc;

    &-new {
      background-color: #ecfdff;
    }
  }

  &__body-message-text {
    font-size: 14px;
    padding-left: 5px;
    white-space: pre-wrap;
  }

  &__body-message-author {
    font-weight: 700;
    color: #333333;
  }

  &__body-message-author-current-user {
    color: #888888;
  }

  &__body-message-time {
    position: absolute;
    bottom: 2px;
    right: 3px;
    font-size: 12px;

    &-read {
      color: #4caf50;
    }

    &-unread {
      color: #999;
    }
  }

  &__body-input {
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 60px;
    background-color: #eee;
    border-top: 1px solid #ccc;
  }

  &__body-input-textarea {
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

  &__body-input-send {
    position: absolute;
    top: 0;
    right: 0;
    width: 40px;
    height: 100%;
    line-height: 60px;
    text-align: center;
    font-size: 14px;
    font-weight: bold;
    cursor: pointer;

    &-symbols-left {
      color: #999;
      position: absolute;
      bottom: 2px;
      right: 3px;
      left: 3px;
      text-align: center;
      font-size: 10px;
      line-height: 1.1;
    }
  }

  &__body-input-send:hover {
    background-color: #ccc;

    i {
      color: #fff;
    }
  }

  &__body-input-send:active {
    background-color: #aaa;
  }

  &__body-input-send i {
    font-size: 20px;
  }
}

.typing {
  width: fit-content;
  height: 18px;
  position: relative;
  padding: 6px;
  margin: 5px;
  background: #e6e6e6;
  border-radius: 20px;
  font-size: 12px;
  overflow: visible;
  opacity: 0;
  transition: opacity 0.3s ease-in-out;

  &.typing--active {
    opacity: 1;
  }
}

.typing__text {
  float: left;
  color: #8d8c91;
  font-size: 10px;
  line-height: 18px;
  margin-right: 8px;
  margin-top: -7px;
}

.typing__dot {
  float: left;
  width: 6px;
  height: 6px;
  margin: 0 4px;
  background: #8d8c91;
  border-radius: 50%;
  opacity: 0;
  animation: loadingFade 1s infinite;
}

.typing__dot:nth-child(2) {
  animation-delay: 0s;
}

.typing__dot:nth-child(3) {
  animation-delay: 0.2s;
}

.typing__dot:nth-child(4) {
  animation-delay: 0.4s;
}

@keyframes loadingFade {
  0% {
    opacity: 0;
  }
  50% {
    opacity: 0.8;
  }
  100% {
    opacity: 0;
  }
}
</style>
