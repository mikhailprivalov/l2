<template>
  <div v-frag>
    <div class="panel panel-default panel-flt">
      <ul class="list-group">
        <li class="list-group-item">
          <div class="row">
            <div class="col-xs-12 col-md-3 col-lg-3">
              Вход выполнен как: {{ user_data.username }}<br />
              <a href="#" class="a-under" @click="modalPassword = true" v-if="changePassword">сменить пароль</a>
            </div>
            <div class="col-xs-12 col-md-6 col-lg-6 text-center text-left-xs">
              {{ fio_dep }}
            </div>
            <div class="col-xs-12 col-md-3 col-lg-3 text-right text-left-xs">
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
            <div class="alert-modal">
              В вашем профиле не настроен <strong>email адрес</strong>!.<br />
              Обратитесь к администратору для установки <strong>email адреса</strong>.<br />
              Тогда вы сможете сменить пароль!
            </div>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-6">
                <button @click="modalPassword = false" class="btn btn-blue-nb" :disabled="loading" type="button">
                  Отмена
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

@Component({
  components: { Modal },
  data() {
    return {
      modalPassword: false,
      loading: false,
    };
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

  loading: boolean;

  email: string | null;

  get system() {
    return this.$systemTitle();
  }

  async doChangePassword() {
    try {
      await this.$dialog.confirm('Вы действительно хотите сменить пароль и выйти из системы?');
    } catch (_) {
      return;
    }
    this.loading = true;
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
