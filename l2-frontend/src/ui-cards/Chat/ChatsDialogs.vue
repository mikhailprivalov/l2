<template>
  <div v-frag>
    <ChatDialog
      v-for="dialog in dialogs"
      :key="dialog"
      :dialog-id="dialog"
    />
  </div>
</template>

<script lang="ts">
import ChatDialog from '@/ui-cards/Chat/ChatDialog.vue';

export default {
  name: 'ChatsDialogs',
  components: { ChatDialog },
  computed: {
    dialogs() {
      return this.$store.getters.chatsDialogsOpened;
    },
  },
};
</script>
