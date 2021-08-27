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
        </div>
      </div>
      <div class="version">L2 {{ menu.version }}</div>
    </form>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import { mapGetters } from 'vuex';
import { POSITION } from 'vue-toastification/src/ts/constants';
import * as actions from '@/store/action-types';
import { Menu } from '@/types/menu';

@Component({
  computed: mapGetters(['authenticated', 'menu']),
  data() {
    return {
      username: '',
      password: '',
    };
  },
})
export default class LoginPage extends Vue {
  authenticated: boolean;

  menu: Menu;

  username: string;

  password: string;

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
</style>
