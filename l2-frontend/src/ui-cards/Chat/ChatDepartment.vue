<template>
  <div
    v-if="!forceOpened || filteredUsers.length"
    class="department"
    :class="opened && 'department-opened'"
  >
    <div
      class="department-title"
      @click="toggle"
    >
      <div class="department-title__name">
        {{ department.title }} <template v-if="!forceOpened">
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
      v-if="opened"
      class="department-body"
    >
      <ChatUser
        v-for="user in filteredUsers"
        :key="user.pk"
        :user="user"
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
      return this.department.usersOnline;
    },
    totalUsers() {
      return this.department.users.length;
    },
    opened() {
      return this.forceOpened || this.open;
    },
  },
  mounted() {
    this.open = this.department.pk === this.userDepartment;
  },
  methods: {
    toggle() {
      this.open = !this.open;
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

    &__name {
      font-weight: 500;
      padding-left: 3px;
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
