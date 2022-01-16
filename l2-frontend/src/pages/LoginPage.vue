<template>
  <div id="login-container">
    <form class="form-signin" @submit.prevent="auth">
      <div class="panel panel-flt">
        <div class="panel-body">
          <input
            type="text"
            id="input-username"
            class="form-control input-lg"
            name="username"
            v-model="username"
            placeholder="Логин или штрих-код"
            ref="username"
          />
          <input
            type="password"
            id="input-password"
            class="form-control input-lg"
            name="password"
            v-model="password"
            placeholder="Пароль"
          />
          <button class="btn btn-lg btn-primary-nb btn-block" type="submit">Вход</button>
          <button class="btn btn-reset btn-block" @click.prevent="clear">
            Очистить форму
          </button>
          <div v-if="changePassword" class="text-center password-reset-link">
            <a href="#" class="a-under" @click="loosePassword = true" v-if="changePassword">восстановить пароль по email</a>
          </div>
        </div>
      </div>
      <div class="version">Система {{ system }} {{ menu.version }}</div>
    </form>
    <MountingPortal mountTo="#portal-place-modal" name="ChangePassword" append>
      <transition name="fade">
        <Modal
          v-if="loosePassword"
          @close="loosePassword = false"
          show-footer="true"
          white-bg="true"
          max-width="710px"
          width="100%"
          marginLeftRight="auto"
          :noClose="!!loading"
        >
          <span slot="header">Восстановление пароля по email</span>
          <div slot="body" class="popup-body" v-if="!hasCodeSend">
            <div class="alert-modal">
              Если в вашем профиле был указан email — мы можем отправить вам новый пароль после подтверждения адреса.
            </div>
            <input
              type="email"
              v-model.trim="email"
              class="form-control"
              placeholder="Ваш адрес"
              style="margin-bottom: 5px;"
              :readonly="loading"
            />

            <button
              @click="sendEmail"
              class="btn btn-blue-nb"
              style="margin-top: 5px;"
              :disabled="loading || !!emailIsNotValid"
              type="button"
            >
              Отправить код для подтверждения
            </button>
          </div>
          <div slot="body" class="popup-body" v-else>
            <div class="alert-modal">
              Был отправлен код на введённый email.
              <br />
              Если код не был получен — проверьте правильность ввода адреса или обратитесь к администратору.
            </div>
            <input
              type="text"
              v-model.trim="code"
              class="form-control"
              style="margin-bottom: 5px;"
              :placeholder="`Код с ${email}`"
              :readonly="loading"
            />

            <button @click="sendCode" class="btn btn-blue-nb" style="margin-top: 5px;" :disabled="loading || !code" type="button">
              Получить новый пароль
            </button>

            <a
              @click.prevent="hasCodeSend = loading"
              class="a-under"
              :style="loading ? 'opacity: 0' : 'margin-left: 5px;line-height: 34px;vertical-align: bottom;'"
              href="#"
            >
              <i class="fa fa-arrow-left"></i> вернуться назад
            </a>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-12 text-right">
                <button @click="loosePassword = false" class="btn btn-blue-nb" :disabled="loading" type="button">
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        </Modal>
      </transition>
    </MountingPortal>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import { mapGetters } from 'vuex';
import { POSITION } from 'vue-toastification/src/ts/constants';
import * as actions from '@/store/action-types';
import { Menu } from '@/types/menu';
import { validateEmail } from '@/utils';
import Modal from '@/ui-cards/Modal.vue';

@Component({
  components: { Modal },
  computed: mapGetters(['authenticated', 'menu']),
  data() {
    return {
      username: '',
      password: '',
      email: '',
      loosePassword: false,
      loading: false,
      hasCodeSend: false,
      code: '',
    };
  },
  watch: {
    loosePassword() {
      this.hasCodeSend = false;
      this.email = '';
      this.code = '';
    },
    hasCodeSend() {
      this.code = '';
    },
  },
})
export default class LoginPage extends Vue {
  authenticated: boolean;

  menu: Menu;

  username: string;

  password: string;

  email: string;

  code: string;

  loosePassword: boolean;

  loading: boolean;

  hasCodeSend: boolean;

  get system() {
    return this.$systemTitle();
  }

  get changePassword() {
    return !!this.$store.getters.modules.change_password;
  }

  get emailIsNotValid() {
    if (!this.email) {
      return 'Введите email';
    }

    if (!validateEmail(this.email)) {
      return 'Некорректный email';
    }

    return false;
  }

  async sendEmail() {
    await this.$store.dispatch(actions.INC_LOADING);
    this.loading = true;
    await this.$api('/users/loose-password', this, ['email'], {
      step: 'request-code',
    });
    this.hasCodeSend = true;
    this.loading = false;
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  async sendCode() {
    await this.$store.dispatch(actions.INC_LOADING);
    this.loading = true;
    const { ok } = await this.$api('/users/loose-password', this, ['email', 'code'], {
      step: 'check-code',
    });
    if (ok) {
      this.loosePassword = false;
      this.$root.$emit('msg', 'ok', 'На ваш email отправлен новый пароль', 10000);
    } else {
      this.$root.$emit('msg', 'error', 'Некорректный код или email');
    }
    this.loading = false;
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  created() {
    if (this.authenticated) {
      this.afterOkAuth();
    }
  }

  mounted() {
    this.focusUsername();
  }

  clear() {
    this.username = '';
    this.password = '';
    this.focusUsername();
  }

  focusUsername() {
    if (this.$refs.username) {
      window.$(this.$refs.username).focus();
    }
  }

  async auth() {
    await this.$store.dispatch(actions.INC_LOADING);
    const { ok, message, fio } = await this.$api('users/auth', this, ['username', 'password']);
    await this.$store.dispatch(actions.DEC_LOADING);
    if (!ok) {
      this.$toast.error(message, {
        position: POSITION.BOTTOM_RIGHT,
        timeout: 8000,
        closeOnClick: true,
        pauseOnHover: true,
        icon: true,
      });
    } else {
      this.$toast.success(`Вы вошли как ${fio}`, {
        position: POSITION.BOTTOM_RIGHT,
        timeout: 6000,
        closeOnClick: true,
        pauseOnHover: true,
        icon: true,
      });
      this.afterOkAuth();
    }
  }

  afterOkAuth() {
    const urlParams = new URLSearchParams(window.location.search);
    const next = urlParams.get('next');
    this.$router.push(next || '/ui/menu');
  }
}
</script>

<style lang="scss" scoped>
#login-container {
  position: absolute;
  top: 36px;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.panel-body {
  border-radius: 4px;
}

.form-signin {
  align-self: center;
  width: 450px;
}

.form-signin .checkbox {
  font-weight: normal;
}

.form-signin .form-control {
  position: relative;
  height: auto;
  box-sizing: border-box;
  padding: 10px;
  font-size: 16px;
  border-radius: 5px 5px 0 0;
}

.form-signin .form-control:focus {
  z-index: 2;
}

#input-username {
  margin-bottom: -1px;
  border-bottom-right-radius: 0;
  border-bottom-left-radius: 0;
}

#input-password {
  margin-bottom: 10px;
  border-radius: 0 0 5px 5px;
}

@media (max-width: 450px) {
  .form-signin {
    width: 100%;
  }
}

.version {
  padding: 10px;
  text-align: center;
}

.password-reset-link {
  margin-top: 8px;
  margin-bottom: -3px;
}

.alert-modal {
  margin: 0 0 15px 0;
  padding: 10px;
  background-color: rgba(0, 0, 0, 8%);
  border-radius: 4px;
}
</style>
