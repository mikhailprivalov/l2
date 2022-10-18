<template>
  <div class="chats-body">
    <div class="chats-body__header">
      <div
        v-if="!search"
        class="chats-body__header-title"
      >
        L2.Сообщения
        <div
          class="chats-body__header-search"
          @click="openSearch"
        >
          <i class="fa fa-search" />
        </div>
      </div>
      <div
        v-else
        class="chats-body__header-search-input"
      >
        <input
          ref="searchInput"
          v-model.trim="q"
          type="text"
          placeholder="Поиск"
          @keyup.escape="search = false"
        >
        <div
          class="chats-body__header-search-input-cancel"
          @click="search = false"
        >
          <i class="fa fa-times" />
        </div>
      </div>
      <div class="chats-body__header-loading">
        <div
          v-if="chatsLoading"
          class="chats-body__header-loading-indicator"
        >
          <i class="fa fa-spinner fa-spin" />
        </div>
      </div>
    </div>
    <div class="chats-scroll">
      <ChatDepartment
        v-for="department in chatsDepartments"
        :key="department.pk"
        :department="department"
        :force-opened="search"
        :search="q"
      />
    </div>
  </div>
</template>

<script lang="ts">
import ChatDepartment from '@/ui-cards/Chat/ChatDepartment.vue';

export default {
  name: 'ChatsBody',
  components: { ChatDepartment },
  data() {
    return {
      search: false,
      q: '',
    };
  },
  computed: {
    chatsDepartments() {
      return this.$store.getters.chatsDepartments || [];
    },
    chatsLoading() {
      return this.$store.getters.chatsLoading;
    },
  },
  methods: {
    openSearch() {
      this.search = true;
      this.$nextTick(() => {
        this.$refs.searchInput.focus();
      });
    },
  },
};
</script>

<style scoped lang="scss">
.chats-body {
  width: 100%;
  height: 100%;
  overflow: hidden;

  &__header {
    width: 100%;
    height: 30px;
    border-bottom: 1px solid #d0d0d0;
    display: flex;
    align-items: center;
    padding: 0 10px;

    &-title {
      font-size: 16px;
      font-weight: 500;
      color: #333;
    }

    &-search {
      display: inline-block;
      margin-left: 10px;
      cursor: pointer;
      color: #999;
      transition: color 0.2s ease;

      &:hover {
        color: #333;
      }
    }

    &-search-input {
      width: 100%;
      height: 100%;
      margin-right: 20px;
      margin-left: -10px;
      display: flex;
      align-items: center;
      padding: 0 10px;
      background: #f5f5f5;
      border-radius: 0;

      input {
        width: 100%;
        height: 100%;
        border: none;
        outline: none;
        background: transparent;
        font-size: 14px;
        color: #333;
      }

      &-cancel {
        margin-left: 10px;
        cursor: pointer;
        color: #999;
        transition: color 0.2s ease;

        &:hover {
          color: #333;
        }
      }
    }

    &-loading {
      margin-left: auto;

      &-indicator {
        font-size: 16px;
        color: #999;
      }
    }
  }
}

.chats-scroll {
  width: 100%;
  height: calc(100% - 30px);
  overflow-y: auto;
}
</style>
