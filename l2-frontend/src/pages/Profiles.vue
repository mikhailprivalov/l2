<template>
  <div class="root">
    <div class="left">
      <treeselect :multiple="false" :disable-branch-nodes="true"
                  :options="can_edit_any_organization ? hospitals : own_hospital"
                  placeholder="Больница не выбрана" v-model="selected_hospital"
                  :append-to-body="true"
                  :disabled="open_pk !== -2"
                  :clearable="false" />
      <input class="form-control" placeholder="Фильтр" v-model="filter" style="margin-top: 5px;"/>
      <div class="left-wrapper">
        <ul>
          <li v-for="d in departmentFiltered" :key="d.pk">
            <strong>{{d.title}}</strong>
            <ul>
              <li :class="{selected: x.pk === open_pk}" v-for="x in d.users" :key="x.pk">
                <a @click.prevent="open(x.pk)" class="user-link" href="#">{{x.username}} – {{x.fio}}</a>
              </li>
              <li :class="{selected: open_pk === -1 && user.department === d.pk}">
                <a @click.prevent="open(-1, d.pk)" href="#">
                  <i class="fa fa-plus"></i> добавить пользователя</a>
              </li>
            </ul>
          </li>
        </ul>
      </div>
    </div>
    <div class="right" v-if="open_pk > -2">
      <div class="right-wrapper">
        <div class="main-data">
          <div class="row">
            <div class="col-xs-6" style="padding-right: 0">
              <div class="input-group">
                <span class="input-group-addon">ФИО</span>
                <input class="form-control" style="margin-right: -1px;" type="text" v-model="user.fio"/>
              </div>
            </div>
            <div class="col-xs-6" style="padding-left: 0">
              <div class="input-group" style="margin-right: -1px;">
                <span class="input-group-addon">Имя пользователя</span>
                <input class="form-control" type="text" v-model="user.username"/>
                <div class="input-group-btn">
                  <button @click="gen_username"
                          class="btn btn-blue-nb btn-ell dropdown-toggle nbr"
                          title="Генерация имени пользователя на основе ФИО"
                          type="button"
                          v-tippy="{ placement : 'bottom', arrow: true }">
                    <i class="fa fa-dot-circle-o"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div class="row">
            <div class="col-xs-6" style="padding-right: 0">
              <div class="input-group">
                <span class="input-group-addon">Пароль</span>
                <input :placeholder="'Минимальная длина пароля – 6 символов. '
                   + (open_pk === -1 ? '' : 'Для смены пароля введите новый')"
                       class="form-control"
                       type="text"
                       v-model="user.password"/>
                <div class="input-group-btn">
                  <button @click="gen_passwd"
                          class="btn btn-blue-nb btn-ell dropdown-toggle nbr"
                          title="Генерация пароля"
                          type="button"
                          v-tippy="{ placement : 'bottom', arrow: true }">
                    <i class="fa fa-dot-circle-o"></i>
                  </button>
                </div>
                <div class="input-group-btn" v-if="user.doc_pk > -1">
                  <a :href="`/barcodes/login?pk=${user.doc_pk}`"
                     target="_blank"
                     class="btn btn-blue-nb btn-ell dropdown-toggle nbr"
                     title="Штрих-код для входа"
                     type="button"
                     style="border-radius: 0"
                     v-tippy="{ placement : 'bottom', arrow: true }">
                    <i class="fa fa-barcode"></i>
                  </a>
                </div>
              </div>
            </div>
            <div class="col-xs-6" style="padding-left: 0">
              <div class="input-group">
                <span class="input-group-addon">Подразделение</span>
                <select class="form-control" v-model="user.department">
                  <option :value="d.pk" v-for="d in departments" :key="d.pk">
                    {{d.title}}
                  </option>
                </select>
              </div>
            </div>
          </div>
        </div>
        <div class="more-data">
          <div class="row" v-if="l2_user_data.rmis_enabled">
            <div class="col-xs-4" style="padding-right: 0">
              <div class="input-group" style="width: 100%">
                <span class="input-group-addon">РМИС логин</span>
                <input class="form-control" v-model="user.rmis_login"/>
              </div>
            </div>
            <div class="col-xs-4" style="padding-left: 0; padding-right: 0;">
              <div class="input-group" style="width: 100%">
                <span class="input-group-addon">РМИС пароль</span>
                <input class="form-control" placeholder="Для замены введите значение" v-model="user.rmis_password"/>
              </div>
            </div>
            <div class="col-xs-4" style="padding-left: 0;">
              <div class="input-group" style="width: 100%">
                <span class="input-group-addon">ID ресурса РМИС</span>
                <input class="form-control" v-model="user.rmis_resource_id"/>
              </div>
            </div>
          </div>
          <div class="row" v-if="l2_user_data.rmis_enabled && modules.l2_rmis_queue">
            <div class="col-xs-4" style="padding-right: 0">
              <div class="input-group" style="width: 100%">
                <span class="input-group-addon">РМИС location</span>
                <input class="form-control" v-model="user.rmis_location"/>
              </div>
            </div>
            <div class="col-xs-4" style="padding-left: 0; padding-right: 0;">
              <div class="input-group" style="width: 100%">
                <span class="input-group-addon">РМИС employee</span>
                <input class="form-control" v-model="user.rmis_employee_id"/>
              </div>
            </div>
            <div class="col-xs-4" style="padding-left: 0">
              <div class="input-group" style="width: 100%">
                <span class="input-group-addon">РМИС service</span>
                <input class="form-control" v-model="user.rmis_service_id_time_table"/>
              </div>
            </div>
          </div>
          <div class="row">
            <div class="col-xs-6" style="padding-right: 0">
              <div class="input-group" style="width: 100%">
                <span class="input-group-addon">Код врача</span>
                <input class="form-control" v-model="user.personal_code"/>
              </div>
            </div>
            <div class="col-xs-6" style="padding-left: 0">
              <div class="input-group" style="width: 100%">
                <span class="input-group-addon">Специальность</span>
                <select class="form-control" v-model="user.speciality">
                  <option :value="d.pk" v-for="d in specialities" :key="d.pk">
                    {{d.title}}
                  </option>
                </select>
              </div>
            </div>
          </div>
          <div class="input-group" style="width: 100%">
            <span class="input-group-addon">Группы</span>
            <select class="form-control" multiple style="height: 136px;" v-model="user.groups">
              <option v-for="g in user.groups_list" :value="g.pk" :key="g.pk">{{ g.title }}</option>
            </select>
          </div>
          <div class="more-title">Запрет на создание направлений с назначениями:</div>
          <div class="row" style="margin-right: 0">
            <div class="col-xs-6"
                 style="height: 300px;border-right: 1px solid #eaeaea;padding-right: 0;">
              <researches-picker :hidetemplates="true"
                                 :just_search="true" v-model="user.restricted_to_direct"/>
            </div>
            <div class="col-xs-6" style="height: 300px;padding-left: 0;padding-right: 0;">
              <selected-researches :researches="user.restricted_to_direct" :simple="true"/>
            </div>
          </div>
          <div class="more-title" v-if="modules.l2_rmis_queue && user.rmis_location !== ''">Услуги, оказываемые
            пользователем:
          </div>
          <div class="row" style="margin-right: 0" v-if="modules.l2_rmis_queue && user.rmis_location !== ''">
            <div class="col-xs-6"
                 style="height: 300px;border-right: 1px solid #eaeaea;padding-right: 0;">
              <researches-picker :hidetemplates="true"
                                 :filter_types="[2]"
                                 :just_search="true" v-model="user.users_services"/>
            </div>
            <div class="col-xs-6" style="height: 300px;padding-left: 0;padding-right: 0;">
              <selected-researches :researches="user.users_services" :simple="true"/>
            </div>
          </div>
        </div>
      </div>
      <div class="right-bottom">
        <button @click="close" class="btn btn-blue-nb">Закрыть</button>
        <button :disabled="!valid" @click="save" class="btn btn-blue-nb">Сохранить</button>
      </div>
    </div>
  </div>
</template>

<script>
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import { debounce } from 'lodash';
import { mapGetters } from 'vuex';
import usersPoint from '../api/user-point';
import * as actions from '../store/action-types';
import ResearchesPicker from '../ui-cards/ResearchesPicker.vue';
import SelectedResearches from '../ui-cards/SelectedResearches.vue';

const toTranslit = function (text) {
  return text.replace(/([а-яё])|([\s_-])|([^a-z\d])/gi,
    (all, ch, space, words) => {
      if (space || words) {
        return space ? '-' : '';
      }
      const code = ch.charCodeAt(0);
      let index;
      if (code === 1025 || code === 1105) {
        index = 0;
      } else {
        index = code > 1071 ? code - 1071 : code - 1039;
      }
      const t = ['yo', 'a', 'b', 'v', 'g', 'd', 'e', 'zh',
        'z', 'i', 'y', 'k', 'l', 'm', 'n', 'o', 'p',
        'r', 's', 't', 'u', 'f', 'h', 'c', 'ch', 'sh',
        'shch', '', 'y', '', 'e', 'yu', 'ya',
      ];
      return t[index];
    });
};

function str_rand(l = 8, v = 1) {
  let result = '';
  const words = v === 1 ? '0123456789-qwertyuiopasdfghjklzxcvbnm01234567890123456789' : '000000000000123456789';
  const max_position = words.length - 1;
  for (let i = 0; i < l; ++i) {
    const position = Math.floor(Math.random() * max_position);
    result += words.substring(position, position + 1);
  }
  return result;
}

export default {
  components: { ResearchesPicker, SelectedResearches, Treeselect },
  name: 'profiles',
  data() {
    return {
      filter: '',
      departments: [],
      specialities: [],
      user: {
        username: '',
        rmis_location: '',
        rmis_login: '',
        rmis_password: '',
        doc_pk: -1,
        personal_code: -1,
        rmis_resource_id: '',
        rmis_employee_id: '',
        rmis_service_id_time_table: '',
      },
      selected_hospital: -1,
      open_pk: -2,
    };
  },
  created() {
    this.load_users();
  },
  watch: {
    'user.fio': function () {
      this.user.fio = this.user.fio.replace(/\s\s+/g, ' ').split(' ')
        .map((s) => s.split('-').map((x) => x.charAt(0).toUpperCase() + x.substring(1).toLowerCase()).join('-'))
        .join(' ');
      if (this.open_pk === -1) {
        this.deb_gu();
      }
    },
    user_hospital: {
      handler() {
        if (this.selected_hospital !== -1 || this.user_hospital === -1) {
          return;
        }
        this.selected_hospital = this.user_hospital;
      },
      immediate: true,
    },
    selected_hospital() {
      if (this.selected_hospital === -1) {
        return;
      }

      this.load_users();
    },
  },
  methods: {
    deb_gu: debounce(function () {
      this.gen_username();
    }, 500),
    gen_username() {
      let v = this.user.fio.toLowerCase();
      let ls = v.split(' ');
      if (ls.length > 3) {
        ls = [ls[0], ls.slice(1, ls.length - 2).join(' '), ls[ls.length - 1] || ''];
      }
      while (ls.length <= 2) {
        ls.push(' ');
      }
      v = ls[0] + (ls[1][0] || '') + (ls[2][0] || '');
      v = toTranslit(v.replace(/\s/g, '')) + str_rand(3, 2);
      this.user.username = v;
      window.okmessage('Имя пользователя сгенерировано');
    },
    gen_passwd() {
      this.user.password = str_rand();
    },
    async load_users(prev_clr = false) {
      await this.$store.dispatch(actions.INC_LOADING);
      if (!prev_clr) {
        this.departments = [];
      }
      const { departments, specialities } = await usersPoint.loadUsers(this, 'selected_hospital');
      this.departments = departments;
      this.specialities = specialities;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async open(pk, dep = null) {
      if ((pk === this.open_pk && pk !== -1) || (this.open_pk === -1 && pk === -1 && dep === this.user.department)) {
        return;
      }
      this.close();
      await this.$store.dispatch(actions.INC_LOADING);
      const { user } = await usersPoint.loadUser({ pk });
      this.user = user;
      if (pk === -1) {
        this.user.department = dep;
        this.gen_passwd();
      }
      await this.$store.dispatch(actions.DEC_LOADING);
      this.open_pk = pk;
    },
    async save() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, npk, message } = await usersPoint.saveUser({
        pk: this.open_pk,
        user_data: this.user,
        hospital_pk: this.selected_hospital,
      });
      if (ok) {
        window.okmessage('Пользователь сохранён', `${this.user.fio} – ${this.user.username}`);
        this.open_pk = npk;
        this.load_users(true);
      } else {
        window.errmessage('Ошибка', message);
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async close() {
      this.open_pk = -2;
      this.user = {
        fio: '',
        groups: [],
        groups_list: [],
        restricted_to_direct: [],
        users_services: [],
        username: '',
        password: '',
        department: null,
        rmis_resource_id: '',
      };
    },
  },
  computed: {
    departmentFiltered() {
      const r = [];
      for (const x of this.departments) {
        r.push({
          ...x,
          users: x.users.filter((y) => y.fio.toLowerCase().startsWith(this.filter.toLowerCase())
              || y.username.toLowerCase().startsWith(this.filter.toLowerCase())),
        });
      }
      return r.filter(d => this.filter === '' || d.users.length || d.title.toLowerCase().startsWith(this.filter.toLowerCase()));
    },
    valid() {
      const p = (this.open_pk > -1 && ((this.user.password.length === 0 || this.user.password.length >= 3)
          || (this.open_pk === -1 && this.user.password.length >= 3)));
      return p && this.user.username !== '' && this.user.fio !== '';
    },
    ...mapGetters({
      modules: 'modules',
      l2_user_data: 'user_data',
      hospitals: 'hospitals',
    }),
    can_edit_any_organization() {
      return this.l2_user_data.su || this.l2_user_data.all_hospitals_users_control;
    },
    user_hospital() {
      return this.l2_user_data.hospital || -1;
    },
    own_hospital() {
      return [this.hospitals.find(({ id }) => id === this.l2_user_data.hospital) || {}];
    },
  },
};
</script>

<style lang="scss" scoped>
  .root {
    height: calc(100% - 36px);
    display: flex;
  }

  .left, .right {
    height: 100%;
  }

  .left {
    background: #fff;
    border-right: 1px solid #646d78;
    padding-top: 5px;
    padding-left: 2px;
    padding-right: 5px;
    width: 320px;

    input {
      border-radius: 0;
      width: 100%;
    }
  }

  .left-wrapper {
    height: calc(100% - 73px);
    padding-top: 5px;
    overflow-y: auto;
  }

  .right {
    width: calc(100% - 321px);
    overflow: hidden;
    position: relative;

    .input-group-addon, input, select {
      border-radius: 0;
      border-top: none;
      border-right: none;
      border-left: none;
    }

    .input-group-addon {
      width: 155px;
      text-align: left;
    }
  }

  .right-wrapper {
    position: absolute;
    top: 0;
    left: 0;
    right: -5px;
    bottom: 34px;
  }

  .right-bottom {
    position: absolute;
    background-color: #eaeaea;
    left: 0;
    right: -5px;
    bottom: 0;
    height: 34px;
    display: flex;

    button {
      border-radius: 0;
    }
  }

  .user-link {
    color: #000;
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }

  .main-data {
    .input-group {
      width: 100%;
    }

    button {
      border-radius: 0;
      width: 50px;
      margin-right: -1px;
    }
  }

  ul {
    padding-left: 20px;
  }

  li > ul > li {
    list-style: none;

    &::before {
      color: #000;
      content: "\2022";
      font-size: 18px;
      line-height: 12px;
      padding-right: 8px;
      position: relative;
      top: 0;
    }

    &.selected::before {
      color: #26816a;
      text-shadow: 0 0 4px rgba(#26816a, .9);
    }
  }

  li.selected {
    a {
      font-weight: bold;

      &.user-link {
        text-shadow: 0 0 4px rgba(#26816a, .5);
      }

      &::before {
        content: "[";
        color: #26816a;
      }

      &::after {
        content: "]";
        color: #26816a;
      }
    }
  }

  .more {
    &-data {
      height: calc(100% - 68px);
      overflow-y: auto;
    }

    &-title {
      background: #eaeaea;
      padding: 5px;
      width: 100%;
    }
  }

  .rinp {
    width: 30%;
  }
</style>
