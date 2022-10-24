<template>
  <div
    v-if="!forceOpened || filteredUsers.length"
    class="department"
    :class="opened && 'department-opened'"
  >
    <div
      class="department-title"
      :class="unreadMessages > 0 && 'department-title-unread'"
      @click="toggle"
    >
      <div class="department-title__name">
        <div
          v-if="unreadMessages > 0 && !forceOpened && !forSelect"
          class="badge badge-danger"
        >
          {{ unreadMessages }}
        </div>
        <div
          v-else-if="forSelect"
          class="department-title__checker"
          @click.stop="selectTotalDepartment"
        >
          <i
            v-if="isTotalDepartmentSelected"
            class="fa fa-check-square"
          />
          <i
            v-else
            class="fa fa-square-o"
          />
        </div>
        {{ department.title }} <template v-if="!forceOpened && department.id !== -100">
          ({{ onlineUsers }}/{{ totalUsers }})
        </template>
      </div>
      <div class="department-title__expand">
        <i
          class="fa"
          :class="opened ? 'fa-angle-up' : 'fa-angle-down'"
        />
      </div>
    </div>
    <div
      v-if="opened || forSelect"
      v-show="opened"
      class="department-body"
    >
      <ChatUser
        v-for="user in filteredUsers"
        :key="user.id"
        :for-select="forSelect"
        :user="user"
        @select="selectUser"
      />
    </div>
  </div>
</template>

<script lang="ts">
import ChatUser from '@/ui-cards/Chat/ChatUser.vue';

export default {
  name: 'ChatDepartment',
  components: { ChatUser },
  props: {
    forSelect: {
      type: Boolean,
      default: false,
    },
    department: {
      type: Object,
      required: true,
    },
    forceOpened: {
      type: Boolean,
      default: false,
    },
    search: {
      type: String,
      default: '',
    },
  },
  data() {
    return {
      open: false,
      selectedUsers: [],
    };
  },
  computed: {
    userDepartment() {
      return this.$store.getters.user_data?.department?.pk;
    },
    filteredUsers() {
      return this.department.users.filter((user) => {
        const search = this.search.toLowerCase();
        return user.name.toLowerCase().includes(search);
      });
    },
    onlineUsers() {
      if (this.department.id === -100) {
        return 0;
      }
      return this.department.usersOnline;
    },
    totalUsers() {
      return this.department.users.length;
    },
    opened() {
      return this.forceOpened || this.open;
    },
    unreadMessages() {
      if (this.forSelect) {
        return 0;
      }

      if (this.department.id === -100) {
        return this.$store.getters.chatsUnreadMessages;
      }

      return this.department.users.reduce((a, u) => {
        if (this.$store.getters.chatsUnreadDialogs[u.id]) {
          return a + this.$store.getters.chatsUnreadDialogs[u.id];
        }
        return a;
      }, 0);
    },
    isTotalDepartmentSelected() {
      return this.selectedUsers.length === this.department.users.length;
    },
  },
  watch: {
    selectedUsers: {
      handler() {
        this.$emit('select', this.selectedUsers);
      },
      deep: true,
      immediate: true,
    },
  },
  mounted() {
    this.open = this.department.id === this.userDepartment && !this.forSelect;
  },
  methods: {
    toggle() {
      this.open = !this.open;
    },
    selectUser(userId, selected) {
      if (selected) {
        this.selectedUsers.push(userId);
      } else {
        this.selectedUsers = this.selectedUsers.filter((id) => id !== userId);
      }
    },
    selectTotalDepartment() {
      this.$root.$emit('chat-department-set-selected', this.department.id, !this.isTotalDepartmentSelected);
    },
  },
};
</script>

<style scoped lang="scss">
.department {
  width: 100%;
  padding: 3px 0;
  border-bottom: 1px solid #e5e5e5;
  transition: background 0.2s ease;

  &:hover:not(&-opened) {
    background: #f5f5f5;
  }

  &-opened {
    background: #f9f9f9;
  }

  &-title {
    display: flex;
    align-items: center;
    justify-content: space-between;
    cursor: pointer;

    &__checker {
      margin-right: 5px;
      cursor: pointer;
      display: inline-block;
    }

    &-unread &__name {
      font-weight: bold;
    }

    &__name {
      font-weight: 500;
      padding-left: 3px;

      .badge {
        font-size: 10px;
        padding: 2px 4px;
      }
    }

    &__expand {
      font-size: 16px;
      padding-right: 3px;
    }
  }

  &-body {
    padding: 5px 0;
    border-top: 1px solid #e5e5e5;
  }
}
</style>
