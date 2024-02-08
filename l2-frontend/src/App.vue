<template>
  <div id="app">
    <Navbar v-if="!embedded && !hideHeaderWithoutLogin && !isEmptyLayout" />

    <div
      v-if="!isFullPageLayout"
      :class="[
        isNarrowLayout && 'container',
        isEmptyLayout && 'empty-layout',
        isWideNarrowLayout && 'wide-narrow-layout',
      ]"
    >
      <router-view />
    </div>
    <PageInnerLayout v-else>
      <router-view />
    </PageInnerLayout>

    <div
      v-if="inLoading"
      id="preloader"
    />

    <transition name="fade">
      <div
        v-if="fullPageLoader"
        id="full-page-loader"
      >
        <div class="loader-inner">
          <div class="rotated-circle" />
          <div
            v-if="asVI"
            class="fixed-loader-text"
          >
            {{ system }}
          </div>
          <div
            v-else
            class="fixed-loader-text"
          >
            L<span>2</span>
          </div>
        </div>
      </div>
    </transition>

    <CheckBackend />
    <ChatsDialogs v-if="chatsEnabled" />
    <ModalForm :key="`modal-form-${editId}`" />

    <audio
      ref="notifyAudioSrc"
      :src="notifyAudioSrc"
      preload="auto"
      type="audio/mpeg"
    />
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import { mapGetters } from 'vuex';
import _ from 'lodash';

import Navbar from '@/components/Navbar.vue';
import ModalForm from '@/components/ModalForm.vue';
import CheckBackend from '@/ui-cards/CheckBackend.vue';
import ChatsDialogs from '@/ui-cards/Chat/ChatsDialogs.vue';
import * as actions from '@/store/action-types';
import notifyAudioSrc from '@/assets/notify.mp3';
import PageInnerLayout from '@/layouts/PageInnerLayout.vue';

@Component({
  components: {
    PageInnerLayout,
    CheckBackend,
    Navbar,
    ChatsDialogs,
    ModalForm,
  },
  computed: mapGetters(['inLoading', 'fullPageLoader', 'authenticated', 'editId']),
  metaInfo() {
    return {
      title: `${this.$route?.meta?.title || this.$systemTitle()} — ${this.$orgTitle()}`,
    };
  },
  data() {
    return {
      embedded: false,
      notifyAudioSrc,
    };
  },
  watch: {
    $route() {
      this.embedded = this.$route.query.embedded === '1';
    },
    l2_chats() {
      this.loadChatsDebounced();
    },
    authenticated() {
      this.loadChatsDebounced();
    },
  },
  mounted() {
    this.$store.dispatch(actions.PRINT_QUEUE_INIT);
    const urlParams = new URLSearchParams(window.location.search);
    this.embedded = urlParams.get('embedded') === '1';
    if (!this.embedded && !this.hideHeaderWithoutLogin && !this.isEmptyLayout) {
      this.loadChatsDebounced();
      this.$store.subscribeAction((action) => {
        if (action.type === actions.CHATS_NOTIFY && this.alertsEnabled) {
          if (!this.$store.getters.chatsDialogsOpened.includes(action.payload.dialogId)) {
            let { text } = action.payload;

            if (text.length > 150) {
              text = `${text.substring(0, 150)}...`;
            }

            this.$root.$emit(
              'msg',
              'message',
              `Сообщение от ${action.payload.authorName}`,
              10000,
              {
                author: action.payload.authorName,
                text,
                dialogId: action.payload.dialogId,
              },
            );
          }
          this.playNotifySound();
        }
      });
    }
  },
})
export default class App extends Vue {
  inLoading: boolean;

  fullPageLoader: boolean;

  authenticated: boolean;

  embedded: boolean;

  notifyAudioSrc: string;

  get isEmptyLayout() {
    return !!this.$route?.meta?.emptyLayout;
  }

  get isNarrowLayout() {
    return Boolean(this?.$route?.meta?.narrowLayout);
  }

  get isFullPageLayout() {
    return Boolean(this?.$route?.meta?.fullPageLayout);
  }

  get hideHeaderWithoutLogin() {
    return Boolean(this?.$route?.meta?.hideHeaderWithoutLogin);
  }

  get isMenuPage() {
    return this?.$route?.name === 'menu';
  }

  get l2_chats() {
    return this.$store.getters.modules.l2_chats;
  }

  get isWideNarrowLayout() {
    return this.isNarrowLayout && this.isMenuPage && this.l2_chats;
  }

  get system() {
    return this.$systemTitle();
  }

  get asVI() {
    return this.$asVI();
  }

  get docPk() {
    return this.$store.getters.currentDocPk;
  }

  loadChats() {
    if (this.embedded || this.hideHeaderWithoutLogin || this.isEmptyLayout || !this.authenticated) {
      return;
    }
    this.$store.dispatch(actions.CHATS_LOAD_DEPARTMENTS);
    this.$store.dispatch(actions.CHATS_MESSAGES_COUNT);
    this.$store.dispatch(actions.CHATS_SET_DISABLE_ALERTS, {
      disableAlerts: localStorage.getItem(`chatsDisableAlerts:${this.docPk}`) === '1',
    });
  }

  loadChatsDebounced = _.debounce(this.loadChats, 100);

  chatsEnabled() {
    return this.$store.getters.chatsEnabled;
  }

  playNotifySound() {
    if (!this.$refs.notifyAudioSrc) {
      return;
    }
    const audio = this.$refs.notifyAudioSrc as HTMLAudioElement;
    audio.play().catch(() => {
      // ignore
    });
  }

  get alertsEnabled() {
    return !this.$store.getters.chatsDisableAlerts;
  }
}
</script>

<style lang="scss" scoped>
#preloader {
  opacity: 0;
  cursor: progress;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  position: fixed;
  height: 100%;
  width: 100%;
  background-color: rgba(0, 0, 0, 0.68);
  left: 0;
  top: 0;
  z-index: 100000;
  animation: fadeInFromNone 10s ease-out forwards;
}

@keyframes fadeInFromNone {
  0% {
    opacity: 0;
  }

  15% {
    opacity: 0;
  }

  100% {
    opacity: 1;
  }
}

#full-page-loader {
  position: fixed;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 100000;
  background: radial-gradient(#cecece, #fff);
  display: flex;
  justify-content: center;
  align-items: center;

  .loader-inner {
    width: 350px;
    height: 350px;
    border-radius: 100%;
    background: linear-gradient(
      165deg,
      rgba(240, 240, 240, 1) 0%,
      rgb(220, 220, 220) 60%,
      rgb(170, 170, 170) 99%,
      rgb(10, 10, 10) 100%
    );
    position: relative;

    .fixed-loader-text {
      position: absolute;
      top: 50%;
      left: 50%;
      text-align: center;
      width: 200px;
      transform: translateX(-50%) translateY(-50%);
      font-size: 50px;
      font-weight: 400;
      font-style: italic;
      color: #4c4c4c;

      span {
        font-size: 40px;
        position: relative;
        bottom: 0.8ex;
      }
    }

    .rotated-circle:before {
      position: absolute;
      content: '';
      width: 100%;
      height: 100%;
      border-radius: 100%;
      border-bottom: 0 solid #04937205;

      box-shadow: 0 -10px 20px 20px #04937240 inset, 0 -5px 15px 10px #04937250 inset, 0 -2px 5px #04937280 inset,
        0 -3px 2px #049372bb inset, 0 2px 0px #049372bb, 0 2px 3px #049372bb, 0 5px 5px #04937290, 0 10px 15px #04937260,
        0 10px 20px 20px #04937240;
      filter: blur(4px);
      animation: 3s rotate linear infinite;
    }
  }
}

@keyframes rotate {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

.empty-layout {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}
</style>

<style lang="scss">
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s;
}

.fade-enter,
.fade-leave-to {
  opacity: 0;
}

.wide-narrow-layout.container {
  @media (min-width: 1200px) {
    max-width: 1470px;
    min-width: 1170px;
    width: unset;
  }
}
</style>
