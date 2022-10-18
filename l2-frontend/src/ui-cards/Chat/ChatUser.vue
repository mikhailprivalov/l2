<template>
  <div
    v-tippy="{followCursor: true, delay: [500, 0]}"
    class="chat-user-wrapper"
    title="Открыть диалог"
    @click="openDialog"
  >
    <div
      class="chat-user"
    >
      <div
        class="chat-user__name"
        :class="user.isOnline && 'chat-user__name-is-online'"
      >
        {{ user.name }}
      </div>
      <div
        v-if="!loading"
        class="chat-user__online"
        :class="user.isOnline && 'chat-user__is-online'"
      >
        <i
          class="fa"
          :class="user.isOnline ? 'fa-circle' : 'fa-circle-o'"
        />
      </div>
      <div
        v-if="loading"
        class="chat-user__online"
        :class="user.isOnline && 'chat-user__is-online'"
      >
        <i
          class="fa fa-circle-o-notch fa-spin"
        />
      </div>
    </div>

    <div
      v-if="!user.isOnline && user.lastOnline"
      class="chat-user__last-online"
    >
      Последняя активность: {{ user.lastOnline | unixTimestampToRelativeTime }}
    </div>
    <div
      v-else-if="user.isOnline"
      class="chat-user__last-online"
    >
      Пользователь в сети
    </div>
    <div
      v-if="user.position || user.speciality"
      class="chat-user__position-and-speciality"
    >
      <template v-if="user.position">
        {{ `${user.position}${user.speciality ? ', ': ''}` }}
      </template>
      <template v-if="user.speciality">
        {{ user.speciality }}
      </template>
    </div>
  </div>
</template>

<script lang="ts">
import * as actions from '@/store/action-types';

export default {
  name: 'ChatUser',
  props: {
    user: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
    };
  },
  methods: {
    async openDialog() {
      if (this.loading) {
        return;
      }
      this.loading = true;
      await this.$store.dispatch(actions.CHATS_OPEN_DIALOG, this.user.id);
      this.loading = false;
    },
  },
};
</script>

<style scoped lang="scss">
.chat-user {
  display: flex;
  align-items: center;
  justify-content: space-between;

  &-wrapper {
    padding: 5px 8px;
    cursor: pointer;

    &:hover {
      background-color: #eeeeee;
    }
  }

  &__name {
    font-size: 14px;

    &-is-online {
      font-weight: 700;
    }
  }

  &__online {
    font-size: 14px;
    padding-left: 3px;
  }

  &__is-online {
    color: #4caf50;
  }

  &__last-online {
    font-size: 12px;
    color: #9e9e9e;
  }

  &__position-and-speciality {
    font-size: 12px;
    color: #9e9e9e;
  }
}
</style>
