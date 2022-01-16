<template>
  <div v-frag>
    <div class="panel panel-default panel-flt">
      <ul class="list-group">
        <li class="list-group-item">
          <div class="row">
            <div class="col-xs-12 col-md-6 col-lg-6">
              Вход выполнен как: {{ user_data.username }}
              <a href="#" class="a-under" @click="modalPassword = true" v-if="changePassword">сменить&nbsp;пароль</a>
              <template v-if="changePassword">
                <br />
                Email: {{ email || '' }}
                <a href="#" class="a-under" @click="modalEmail = true">{{ email ? 'ред.' : 'установить email' }}</a>
              </template>
            </div>
            <div class="col-xs-12 col-md-6 col-lg-6 text-right text-left-xs">
              {{ fio_dep }}
              <br />
              <a href="/logout" class="btn btn-blue-nb">Выход</a>
            </div>
          </div>
        </li>
        <li class="list-group-item">
          Ваши права доступа и группы:
          <div class="row dash-buttons groups-btns">
            <div class="col-xs-12 col-sm-6 col-md-4 col-lg-3 mb5" v-for="g in user_data.groups" :key="g">
              <div class="label label-default bw100 btn-ell" :title="g">{{ g }}</div>
            </div>
          </div>
        </li>
        <li class="list-group-item" v-if="user_data.specialities && user_data.specialities.length > 0">
          Специальности:
          <div class="row dash-buttons groups-btns" v-for="s in user_data.specialities" :key="s">
            <div class="col-xs-12 col-sm-6 col-md-4 col-lg-3 mb5">
              <div class="label label-default bw100 btn-ell" :title="s">{{ s }}</div>
            </div>
          </div>
        </li>
      </ul>
    </div>
    <div class="row menu dash-buttons text-center">
      <div class="col-xs-12 col-sm-6 col-md-4 col-lg-3 mb10 dash-btn" v-for="b in buttons" :key="b.title">
        <router-link :to="b.url" class="panel-body" :target="b.nt && '_blank'">
          <span>{{ b.title }}</span>
        </router-link>
      </div>
    </div>
    <hr />
    <div class="row dash-buttons text-center">
      <div class="col-xs-12 col-sm-6 col-md-6 col-lg-6 mb10 dash-btn dash-info">
        <div class="panel-body">
          <span>
            <span>{{ system }}</span>
            <br />
            <span>{{ menu.version }}</span>
          </span>
        </div>
      </div>
      <div class="col-xs-12 col-sm-6 col-md-6 col-lg-6 mb10 dash-btn dash-info" v-if="menu.region === '38'">
        <a href="http://l2-irk.ru" target="_blank" class="panel-body">
          <span>l2-irk.ru</span>
        </a>
      </div>
      <div class="col-xs-12 col-sm-6 col-md-4 col-lg-4 mb10 dash-btn dash-info" v-else-if="menu.region === 'DEMO'">
        <div class="panel-body">
          <span>
            <span>DEMO</span>
          </span>
        </div>
      </div>
    </div>
    <MountingPortal mountTo="#portal-place-modal" name="ChangePassword" append>
      <transition name="fade">
        <Modal
          v-if="modalPassword"
          @close="modalPassword = false"
          show-footer="true"
          white-bg="true"
          max-width="710px"
          width="100%"
          marginLeftRight="auto"
          :noClose="!!loading"
        >
          <span slot="header">Смена пароля</span>
          <div slot="body" class="popup-body" v-if="email">
            Ваш email: <strong>{{ email }}</strong>
            <br />
            Новый пароль будет отправлен вам на почту!<br />
            После получения пароля войдите в систему заново.<br />
            Все активные сессии будут прекращены (включая текущую).
            <br /><br />
            <button @click="doChangePassword" class="btn btn-blue-nb" :disabled="loading" type="button">
              Сменить пароль
            </button>
          </div>
          <div slot="body" class="popup-body" v-else>
            <div class="alert-modal">В вашем профиле не настроен <strong>email адрес</strong>!</div>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-12 text-right">
                <button @click="modalPassword = false" class="btn btn-blue-nb" :disabled="loading" type="button">
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        </Modal>
      </transition>
    </MountingPortal>
    <MountingPortal mountTo="#portal-place-modal" name="Email" append>
      <transition name="fade">
        <Modal
          v-if="modalEmail"
          @close="modalEmail = false"
          show-footer="true"
          white-bg="true"
          max-width="710px"
          width="100%"
          marginLeftRight="auto"
          :noClose="!!loading"
        >
          <span slot="header">Установка email</span>
          <div slot="body" class="popup-body" v-if="!hasNewCodeRequest">
            Ваш текущий email: <strong>{{ email || 'не установлен' }}</strong>
            <br />
            <div v-if="email && !hasCodeRequest" class="alert-modal">
              Для установки нового адреса запросите код на предыдущий.<br />
              Если у вас нет доступа к {{ email }}, то обратитесь к администратору.
            </div>
            <button @click="requestCode" class="btn btn-blue-nb" :disabled="loading" v-if="needCodeRequest" type="button">
              Запросить код
            </button>

            <input
              v-else-if="email"
              type="text"
              v-model.trim="confirmationCode"
              class="form-control"
              style="margin-bottom: 10px;"
              :placeholder="`Код с ${email}`"
              :readonly="loading"
            />

            <template v-if="!needCodeRequest">
              <input
                type="email"
                v-model.trim="newEmail"
                class="form-control"
                placeholder="Новый адрес"
                style="margin-bottom: 5px;"
                :readonly="loading"
              />
              <div v-if="newEmailIsNotValid">{{ newEmailIsNotValid }}</div>

              <button
                @click="setNewEmail"
                class="btn btn-blue-nb"
                style="margin-top: 5px;"
                :disabled="loading || !!newEmailIsNotValid || (!confirmationCode && !!email)"
                type="button"
              >
                Установить email
              </button>
            </template>
          </div>
          <div slot="body" class="popup-body" v-else>
            <a @click.prevent="hasNewCodeRequest = loading" class="a-under" :style="loading ? 'opacity: 0' : ''" href="#">
              вернуться назад
            </a>
            <br />
            Подтвердите
            <span v-if="email">
              смену адреса с <strong>{{ email }}</strong> на
            </span>
            <span v-else>установку адреса</span>
            <strong>{{ newEmail }}</strong>
            <br />
            Вам был отправлен код на новый адрес.
            <br />

            <input
              type="text"
              v-model.trim="newConfirmationCode"
              class="form-control"
              style="margin-bottom: 5px;"
              :placeholder="`Код с ${newEmail}`"
              :readonly="loading"
            />

            <button @click="confirmNewEmail" class="btn btn-blue-nb" :disabled="!newConfirmationCode || loading" type="button">
              Подтвердить
            </button>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-12 text-right">
                <button @click="modalEmail = false" class="btn btn-blue-nb" :disabled="loading" type="button">
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
import { Menu, Button } from '@/types/menu';
import { validateEmail } from '@/utils';

@Component({
  components: { Modal },
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
  },
  computed: {
    ...mapGetters(['menu', 'user_data']),
    buttons() {
      if (!this.menu || !this.menu.buttons) {
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
    changePassword() {
      return this.$store.getters.modules.change_password;
    },
  },
})
export default class MenuPage extends Vue {
  menu: Menu;

  buttons: Button[];

  fio_dep: string;

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
}
</script>

<style lang="scss" scoped>
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
</style>
