<template>
  <div v-frag>
    <div :class="chatsEnabled && 'menu-wrapper'">
      <div :class="chatsEnabled && 'menu-left'">
        <div class="panel panel-default panel-flt">
          <ul class="list-group">
            <li class="list-group-item">
              <div class="row">
                <div class="col-xs-12 col-md-6 col-lg-6">
                  Вход выполнен как: {{ user_data.username }}
                  <a
                    v-if="changePassword"
                    href="#"
                    class="a-under"
                    @click="modalPassword = true"
                  >сменить&nbsp;пароль</a>
                  <template v-if="changePassword">
                    <br>
                    Email:
                    <a
                      v-if="email"
                      v-tippy
                      href="#"
                      class="a-under-reversed"
                      title="Редактировать адрес"
                      @click="modalEmail = true"
                    >
                      <span class="a-internal">{{ email }}</span> <i class="fa fa-pencil" />
                    </a>
                    <a
                      v-else
                      href="#"
                      class="a-under"
                      @click="modalEmail = true"
                    >установить email</a>
                  </template>
                  <br>
                  Двухфакторная аутентификация:
                  <a
                    href="#"
                    class="a-under-reversed"
                    @click="modalTwoFactor = true"
                  >{{ hasTOTP ? 'активирована' : 'не активна' }} <i class="fa fa-pencil" /></a>
                </div>
                <div class="col-xs-12 col-md-6 col-lg-6 text-right text-left-xs">
                  {{ fio_dep }}
                  <br>
                  <a
                    href="/logout"
                    class="btn btn-blue-nb"
                  >Выход</a>
                </div>
              </div>
            </li>
            <li class="list-group-item">
              Ваши права доступа и группы:
              <div class="row dash-buttons groups-btns">
                <div
                  v-for="g in user_data.groups"
                  :key="g"
                  class="col-xs-12 col-sm-6 col-md-4 col-lg-3 mb5"
                >
                  <div
                    class="label label-default bw100 btn-ell"
                    :title="g"
                  >
                    {{ g }}
                  </div>
                </div>
              </div>
            </li>
            <li
              v-if="user_data.specialities && user_data.specialities.length > 0"
              class="list-group-item"
            >
              Специальности:
              <div
                v-for="s in user_data.specialities"
                :key="s"
                class="row dash-buttons groups-btns"
              >
                <div class="col-xs-12 col-sm-6 col-md-4 col-lg-3 mb5">
                  <div
                    class="label label-default bw100 btn-ell"
                    :title="s"
                  >
                    {{ s }}
                  </div>
                </div>
              </div>
            </li>
          </ul>
        </div>
        <div class="row menu dash-buttons text-center">
          <div
            v-for="b in buttons"
            :key="b.title"
            class="col-xs-12 col-sm-6 col-md-4 col-lg-3 mb10 dash-btn"
          >
            <router-link
              :to="b.url"
              class="panel-body"
              :target="b.nt && '_blank'"
            >
              <span>{{ b.title }}</span>
            </router-link>
          </div><div
            v-if="forms_url"
            class="col-xs-12 col-sm-6 col-md-4 col-lg-3 mb10 dash-btn"
          >
            <router-link
              :to="forms_url"
              class="panel-body"
              target="_blank"
            >
              <span><i class="fas fa-comment" /> Оставить отзыв</span>
            </router-link>
          </div>
        </div>
        <hr>
        <div class="row dash-buttons text-center">
          <div class="col-xs-12 col-sm-6 col-md-6 col-lg-6 mb10 dash-btn dash-info">
            <div class="panel-body">
              <span>
                <span>{{ system }}</span>
                <br>
                <span>{{ menu.version }}</span>
              </span>
            </div>
          </div>
          <div
            v-if="menu.region === '38'"
            class="col-xs-12 col-sm-6 col-md-6 col-lg-6 mb10 dash-btn dash-info"
          >
            <a
              href="http://l2-irk.ru"
              target="_blank"
              class="panel-body"
            >
              <span>l2-irk.ru</span>
            </a>
          </div>
          <div
            v-else-if="menu.region === 'DEMO'"
            class="col-xs-12 col-sm-6 col-md-4 col-lg-4 mb10 dash-btn dash-info"
          >
            <div class="panel-body">
              <span>
                <span>DEMO</span>
              </span>
            </div>
          </div>
        </div>
      </div>
      <div
        v-if="chatsEnabled"
        class="menu-right"
      >
        <ChatsBody />
      </div>
    </div>
    <MountingPortal
      mount-to="#portal-place-modal"
      name="ChangePassword"
      append
    >
      <transition name="fade">
        <Modal
          v-if="modalPassword"
          show-footer="true"
          white-bg="true"
          max-width="710px"
          width="100%"
          margin-left-right="auto"
          :no-close="!!loading"
          @close="modalPassword = false"
        >
          <span slot="header">Смена пароля</span>
          <div
            v-if="email"
            slot="body"
            class="popup-body"
          >
            Ваш email: <strong>{{ email }}</strong>
            <br>
            Новый пароль будет отправлен вам на почту!<br>
            После получения пароля войдите в систему заново.<br>
            Все активные сессии будут прекращены (включая текущую).
            <br><br>
            <button
              class="btn btn-blue-nb"
              :disabled="loading"
              type="button"
              @click="doChangePassword"
            >
              Сменить пароль
            </button>
          </div>
          <div
            v-else
            slot="body"
            class="popup-body"
          >
            <div class="alert-modal">
              В вашем профиле не настроен <strong>email адрес</strong>!
            </div>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-12 text-right">
                <button
                  class="btn btn-blue-nb"
                  :disabled="loading"
                  type="button"
                  @click="modalPassword = false"
                >
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        </Modal>
      </transition>
    </MountingPortal>
    <MountingPortal
      mount-to="#portal-place-modal"
      name="TOTP"
      append
    >
      <transition name="fade">
        <Modal
          v-if="modalTwoFactor"
          show-footer="true"
          white-bg="true"
          max-width="710px"
          width="100%"
          margin-left-right="auto"
          :no-close="!!loading"
          @close="modalTwoFactor = false"
        >
          <span slot="header">Двухфакторная аутентификация</span>
          <div
            v-if="!hasTOTP"
            slot="body"
            class="popup-body"
          >
            <div class="alert-modal">
              Двухфакторная аутентификация не настроена!
            </div>
            <div class="alert-modal">
              Для настройки двухфакторной аутентификации вам необходимо установить приложение<br>
              <strong>TOTP совместимое приложение</strong> на ваш мобильный телефон<br>
              или воспользоваться специальными сервисами.
            </div>
            <div>
              <img
                :src="secretQRBase64"
                alt="qr-code"
                class="qr-code"
              >
              <input
                :value="secretCode"
                type="text"
                class="form-control mb10"
                readonly
              >
              <input
                v-model="checkCode"
                type="text"
                class="form-control mb10"
                placeholder="Введите код из приложения"
              >
              <button
                class="btn btn-blue-nb"
                :disabled="loading"
                type="button"
                @click="doCheckCode"
              >
                Проверить код
              </button>
            </div>
          </div>
          <div
            v-else
            slot="body"
            class="popup-body"
          >
            <div class="alert-modal">
              Двухфакторная аутентификация настроена!
            </div>
            <div class="alert-modal">
              Для отключения двухфакторной аутентификации вам необходимо ввести код из приложения.
            </div>
            <div>
              <input
                v-model="checkCode"
                type="text"
                class="form-control mb10"
                placeholder="Введите код из приложения"
              >
              <button
                class="btn btn-blue-nb"
                :disabled="loading"
                type="button"
                @click="doCheckCodeDisable"
              >
                Проверить код и отключить двухфакторную аутентификацию
              </button>
            </div>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-12 text-right">
                <button
                  class="btn btn-blue-nb"
                  :disabled="loading"
                  type="button"
                  @click="modalTwoFactor = false"
                >
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        </Modal>
      </transition>
    </MountingPortal>
    <MountingPortal
      mount-to="#portal-place-modal"
      name="Email"
      append
    >
      <transition name="fade">
        <Modal
          v-if="modalEmail"
          show-footer="true"
          white-bg="true"
          max-width="710px"
          width="100%"
          margin-left-right="auto"
          :no-close="!!loading"
          @close="modalEmail = false"
        >
          <span slot="header">Установка email</span>
          <div
            v-if="!hasNewCodeRequest"
            slot="body"
            class="popup-body"
          >
            Ваш текущий email: <strong>{{ email || 'не установлен' }}</strong>
            <br>
            <div
              v-if="email && !hasCodeRequest"
              class="alert-modal"
            >
              Для установки нового адреса запросите код на предыдущий.<br>
              Если у вас нет доступа к {{ email }}, то обратитесь к администратору.
            </div>
            <button
              v-if="needCodeRequest"
              class="btn btn-blue-nb"
              :disabled="loading"
              type="button"
              @click="requestCode"
            >
              Запросить код
            </button>

            <input
              v-else-if="email"
              v-model.trim="confirmationCode"
              type="text"
              class="form-control"
              style="margin-bottom: 10px;"
              :placeholder="`Код с ${email}`"
              :readonly="loading"
            >

            <template v-if="!needCodeRequest">
              <input
                v-model.trim="newEmail"
                type="email"
                class="form-control"
                placeholder="Новый адрес"
                style="margin-bottom: 5px;"
                :readonly="loading"
              >
              <div v-if="newEmailIsNotValid">
                {{ newEmailIsNotValid }}
              </div>

              <button
                class="btn btn-blue-nb"
                style="margin-top: 5px;"
                :disabled="loading || !!newEmailIsNotValid || (!confirmationCode && !!email)"
                type="button"
                @click="setNewEmail"
              >
                Установить email
              </button>
            </template>
          </div>
          <div
            v-else
            slot="body"
            class="popup-body"
          >
            <a
              class="a-under"
              :style="loading ? 'opacity: 0' : ''"
              href="#"
              @click.prevent="hasNewCodeRequest = loading"
            >
              вернуться назад
            </a>
            <br>
            Подтвердите
            <span v-if="email">
              смену адреса с <strong>{{ email }}</strong> на
            </span>
            <span v-else>установку адреса</span>
            <strong>{{ newEmail }}</strong>
            <br>
            Вам был отправлен код на новый адрес.
            <br>

            <input
              v-model.trim="newConfirmationCode"
              type="text"
              class="form-control"
              style="margin-bottom: 5px;"
              :placeholder="`Код с ${newEmail}`"
              :readonly="loading"
            >

            <button
              class="btn btn-blue-nb"
              :disabled="!newConfirmationCode || loading"
              type="button"
              @click="confirmNewEmail"
            >
              Подтвердить
            </button>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-12 text-right">
                <button
                  class="btn btn-blue-nb"
                  :disabled="loading"
                  type="button"
                  @click="modalEmail = false"
                >
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

import Modal from '@/ui-cards/Modal.vue';
import { Button, Menu } from '@/types/menu';
import { validateEmail } from '@/utils';
import ChatsBody from '@/ui-cards/Chat/ChatsBody.vue';

@Component({
  components: { ChatsBody, Modal },
  data() {
    return {
      modalPassword: false,
      modalEmail: false,
      loading: false,
      newEmail: '',
      newEmailCode: '',
      hasCodeRequest: false,
      hasNewCodeRequest: false,
      confirmationCode: '',
      newConfirmationCode: '',
      modalTwoFactor: false,
      secretQRBase64: null,
      secretCode: null,
      checkCode: '',
    };
  },
  watch: {
    modalEmail() {
      this.hasCodeRequest = false;
      this.hasNewCodeRequest = false;
      this.newEmail = '';
      this.confirmationCode = '';
      this.newConfirmationCode = '';
      this.loading = false;
    },
    hasNewCodeRequest() {
      this.newConfirmationCode = '';
    },
    async modalTwoFactor() {
      if (this.modalTwoFactor) {
        if (!this.hasTOTP) {
          this.loading = true;
          const {
            qrCode = null, secretCode = null, ok, message,
          } = await this.$api('users/generate-totp-code');
          if (!ok) {
            this.$root.$emit('msg', 'error', message);
            this.modalTwoFactor = false;
          }
          this.loading = false;
          this.secretQRBase64 = qrCode;
          this.secretCode = secretCode;
        }
      } else {
        this.secretQRBase64 = null;
        this.secretCode = null;
      }
      this.checkCode = '';
    },
  },
  computed: {
    ...mapGetters(['menu', 'user_data']),
    buttons() {
      if (!this.menu?.buttons) {
        return [];
      }

      return this.menu.buttons.filter(b => !b.not_show_home && !b.hr);
    },
    fio_dep() {
      return [this.user_data?.fio, this.user_data?.department.title].filter(Boolean).join(', ');
    },
    email() {
      return this.user_data?.email;
    },
    hasTOTP() {
      return this.user_data?.hasTOTP;
    },
    forms_url() {
      return this.user_data?.modules.forms_url;
    },
    changePassword() {
      return this.$store.getters.modules.change_password;
    },
  },
})
export default class MenuPage extends Vue {
  menu: Menu;

  buttons: Button[];

  fio_dep: string;

  forms_url: string;

  changePassword: boolean;

  modalPassword: boolean;

  modalEmail: boolean;

  loading: boolean;

  email: string | null;

  newEmail: string;

  newEmailCode: string;

  confirmationCode: string;

  newConfirmationCode: string;

  hasCodeRequest: boolean;

  hasNewCodeRequest: boolean;

  modalTwoFactor: boolean;

  secretQRBase64: string | null;

  secretCode: string | null;

  checkCode: string;

  get system() {
    return this.$systemTitle();
  }

  get newEmailIsNotValid() {
    if (!this.newEmail) {
      return 'Введите email';
    }

    if (!validateEmail(this.newEmail)) {
      return 'Некорректный email';
    }

    if (this.email === this.newEmail) {
      return 'Email совпадает с текущим';
    }

    return false;
  }

  get needCodeRequest() {
    return !this.hasCodeRequest && !!this.email;
  }

  async doChangePassword() {
    try {
      await this.$dialog.confirm('Вы действительно хотите сменить пароль и выйти из системы?');
    } catch (_) {
      return;
    }

    this.loading = true;

    try {
      const { ok, message } = await this.$api('/users/change-password');
      if (ok) {
        this.$root.$emit('msg', 'ok', 'Успешно. Проверьте почту и повторите вход в систему!', 15000);
        this.$router.push('login');
        return;
      }

      this.$root.$emit('msg', 'error', message || 'Что-то пошло не так');
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error(error);
    }
    this.loading = false;
  }

  async requestCode() {
    this.loading = true;
    const { ok, message } = await this.$api('/users/set-new-email', {
      step: 'request-code',
    });
    if (ok) {
      this.hasCodeRequest = true;
    } else {
      this.$root.$emit('msg', 'error', message);
    }
    this.loading = false;
  }

  async setNewEmail() {
    this.loading = true;
    const { ok, message } = await this.$api('/users/set-new-email', this, ['newEmail', 'confirmationCode'], {
      step: 'set-new-email',
    });
    if (ok) {
      this.hasNewCodeRequest = true;
    } else {
      this.$root.$emit('msg', 'error', message);
    }
    this.loading = false;
  }

  async confirmNewEmail() {
    this.loading = true;
    const { ok, message } = await this.$api(
      '/users/set-new-email',
      this,
      ['newEmail', 'confirmationCode', 'newConfirmationCode'],
      {
        step: 'confirm-new-email',
      },
    );
    if (ok) {
      this.$root.$emit('msg', 'ok', 'Успешно. Страница будет перезагружена', 10000);
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    } else {
      this.$root.$emit('msg', 'error', message);
      this.loading = false;
    }
  }

  async doCheckCode() {
    this.loading = true;
    const { ok, message } = await this.$api('/users/set-totp', this, 'secretCode', {
      confirmationCode: this.checkCode,
    });
    if (ok) {
      this.$root.$emit('msg', 'ok', 'Двухфакторная аутентификация активирована');
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    } else {
      this.$root.$emit('msg', 'error', message);
      this.loading = false;
    }
  }

  async doCheckCodeDisable() {
    this.loading = true;
    const { ok, message } = await this.$api('/users/disable-totp', {
      confirmationCode: this.checkCode,
    });
    if (ok) {
      this.$root.$emit('msg', 'ok', 'Двухфакторная аутентификация отключена');
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    } else {
      this.$root.$emit('msg', 'error', message);
      this.loading = false;
    }
  }

  get chatsEnabled() {
    return this.$store.getters.chatsEnabled;
  }
}
</script>

<style lang="scss" scoped>
.qr-code {
  width: 100%;
  max-width: 200px;
  margin: 10px auto;
}

.groups-btns {
  padding: 0;
  margin-right: 0;
  margin-left: 0;
}

.mb5 {
  margin-bottom: 5px;
}

.mb10 {
  margin-bottom: 5px;
}

.menu.dash-buttons > div.mb10 {
  margin-right: 0;
}

.menu.row.dash-buttons {
  margin-right: -2px;
  margin-left: -2px;
}

.alert-modal {
  margin: 0 0 15px 0;
  padding: 10px;
  background-color: rgba(0, 0, 0, 8%);
  border-radius: 4px;
}

.a-under:not(:hover),
.a-under-reversed:not(:hover) {
  .a-internal {
    color: #000;
  }
}

.menu-wrapper {
  display: flex;
  flex-direction: row;
  position: relative;
}

.menu-left {
  flex: 1;
}

.menu-right {
  position: sticky;
  top: 20px;
  flex: 0 0 300px;
  margin-left: 20px;
  min-height: 500px;
  height: calc(100vh - 66px);
  border: 1px solid #A6B5AA;
  background: #E6E9ED;
  border-radius: 4px;
  overflow: hidden;
}

@media screen and (max-width: 768px) {
  .menu-wrapper {
    flex-direction: column;
  }

  .menu-left {
    flex: 0 0 100%;
  }

  .menu-right {
    position: relative;
    flex: 0 0 100%;
    margin-left: 0;
    margin-top: 20px;
    height: 500px;
  }
}
</style>
