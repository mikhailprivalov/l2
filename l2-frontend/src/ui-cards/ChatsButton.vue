<template>
  <div v-frag>
    <li :class="(!isMenuPage && opened) && 'btn-menu-active'">
      <a
        href="#"
        class="chats-btn"
        @click.prevent="toggle"
      >
        <i class="fa fa-message" />
        <span
          v-if="unreadMessages"
          class="badge badge-danger"
        >
          {{ unreadMessages }}
        </span>
      </a>
    </li>
    <div
      v-if="!isMenuPage"
      v-click-outside="vcoConfig"
      class="right-side-drawer"
      :class="opened && 'open'"
    >
      <ChatsBody />
    </div>
  </div>
</template>

<script lang="ts">
import vClickOutside from 'v-click-outside';

import ChatsBody from '@/ui-cards/Chat/ChatsBody.vue';

export default {
  name: 'ChatsButton',
  components: { ChatsBody },
  directives: {
    clickOutside: vClickOutside.directive,
  },
  data() {
    return {
      opened: false,
    };
  },
  computed: {
    isMenuPage() {
      return this.$route.name === 'menu';
    },
    vcoConfig() {
      return {
        isActive: this.opened,
        handler: this.onClickOutside,
        middleware: this.middleware,
        events: ['dblclick', 'click', 'auxclick'],
      };
    },
    unreadMessages() {
      return this.$store.getters.chatsUnreadMessages;
    },
  },
  watch: {
    isMenuPage() {
      this.opened = false;
    },
  },
  methods: {
    toggle() {
      if (this.isMenuPage) {
        return;
      }
      this.opened = !this.opened;
    },
    onClickOutside() {
      this.opened = false;
    },
  },
};
</script>

<style lang="scss" scoped>
.right-side-drawer {
  position: fixed;
  top: 36px;
  right: 0;
  bottom: 0;
  width: 300px;
  border-left: 1px solid #A6B5AA;
  background: #E6E9ED;
  z-index: 1000;
  box-shadow: -2px 0 10px rgba(0, 0, 0, 0.15);
  transition: transform 0.2s ease;
  transform: translateX(100%);
  overflow-y: auto;

  &.open {
    transform: translateX(0);
  }
}

.chats-btn {
  position: relative;

  .badge {
    position: absolute;
    top: 2px;
    right: 2px;
    font-size: 10px;
    padding: 2px 4px;
  }
}

.btn-menu-active a {
  background-color: #049372 !important;
}

@media (max-width: 768px) {
  .right-side-drawer {
    width: 100%;
  }
}
</style>
