<template>
  <div class="root">
    <div class="left">

    </div>
    <div class="right">
      <div class="right-wrapper">

      </div>
    </div>
  </div>
</template>

<script>
  import users_point from './api/user-point'
  import * as action_types from './store/action-types'
  import ResearchesPicker from './ResearchesPicker'
  import SelectedResearches from './SelectedResearches'
  import l from 'lodash'

  let toTranslit = function (text) {
    return text.replace(/([а-яё])|([\s_-])|([^a-z\d])/gi,
      function (all, ch, space, words, i) {
        if (space || words) {
          return space ? '-' : ''
        }
        let code = ch.charCodeAt(0),
          index = code === 1025 || code === 1105 ? 0 :
            code > 1071 ? code - 1071 : code - 1039,
          t = ['yo', 'a', 'b', 'v', 'g', 'd', 'e', 'zh',
            'z', 'i', 'y', 'k', 'l', 'm', 'n', 'o', 'p',
            'r', 's', 't', 'u', 'f', 'h', 'c', 'ch', 'sh',
            'shch', '', 'y', '', 'e', 'yu', 'ya'
          ]
        return t[index]
      })
  }

  function str_rand(l = 8, v = 1) {
    let result = ''
    const words = v === 1 ? '0123456789-qwertyuiopasdfghjklzxcvbnm01234567890123456789' : '000000000000123456789'
    const max_position = words.length - 1
    for (let i = 0; i < l; ++i) {
      let position = Math.floor(Math.random() * max_position)
      result += words.substring(position, position + 1)
    }
    return result
  }

  export default {
    components: {ResearchesPicker, SelectedResearches},
    name: 'employee-jobs',
    data() {
      return {
        filter: '',
        departments: [],
        user: {
          username: '',
          rmis_location: '',
        },
        open_pk: -2,
      }
    },
    created() {
      // this.load_users()
    },
    watch: {
      'user.fio': function () {
        this.user.fio = this.user.fio.replace(/\s\s+/g, ' ').split(' ')
          .map((s) => s.split('-').map(x => x.charAt(0).toUpperCase() + x.substring(1).toLowerCase()).join('-'))
          .join(' ')
        if (this.open_pk === -1) {
          this.deb_gu()
        }
      },
    },
    methods: {
      deb_gu: l.debounce(function (e) {
        this.gen_username()
      }, 500),
      gen_username() {
        let v = this.user.fio.toLowerCase()
        let ls = v.split(' ')
        if (ls.length > 3) {
          ls = [ls[0], ls.slice(1, ls.length - 2).join(' '), ls[ls.length - 1] || '']
        }
        while (ls.length <= 2) {
          ls.push(' ')
        }
        v = ls[0] + (ls[1][0] || '') + (ls[2][0] || '')
        v = toTranslit(v.replace(/\s/g, '')) + str_rand(3, 2)
        this.user.username = v
        okmessage('Имя пользователя сгенерировано')
      },
      gen_passwd() {
        this.user.password = str_rand()
      },
      async load_users(prev_clr=false) {
        this.$store.dispatch(action_types.INC_LOADING).then()
        if (!prev_clr) {
          this.departments = [];
        }
        const {departments} = await users_point.loadUsers()
        this.departments = departments
        this.$store.dispatch(action_types.DEC_LOADING).then()
      },
      async open(pk, dep = null) {
        if ((pk === this.open_pk && pk !== -1) || (this.open_pk === -1 && pk === -1 && dep === this.user.department)) {
          return
        }
        this.close()
        this.$store.dispatch(action_types.INC_LOADING).then()
        const {user} = await users_point.loadUser(pk)
        this.user = user
        if (pk === -1) {
          this.user.department = dep
          this.gen_passwd()
        }
        this.$store.dispatch(action_types.DEC_LOADING).then()
        this.open_pk = pk
      },
      async save() {
        this.$store.dispatch(action_types.INC_LOADING).then()
        const {ok, npk, message} = await users_point.saveUser(this.open_pk, this.user)
        if (ok) {
          okmessage('Пользователь сохранён', `${this.user.fio} – ${this.user.username}`)
          this.open_pk = npk
          this.load_users(true);
        } else {
          errmessage('Ошибка', message)
        }
        this.$store.dispatch(action_types.DEC_LOADING).then()
      },
      async close() {
        this.open_pk = -2
        this.user = {
          fio: '',
          groups: [],
          groups_list: [],
          restricted_to_direct: [],
          users_services: [],
          username: '',
          password: '',
          department: null,
        }
      },
    },
    computed: {
      rmis_queue() {
        return this.$store.getters.modules.l2_rmis_queue;
      },
      department_filter() {
        const r = []
        for (let x of this.departments) {
          r.push({
            ...x, users: x.users.filter(y => y.fio.toLowerCase().startsWith(this.filter.toLowerCase())
              || y.username.toLowerCase().startsWith(this.filter.toLowerCase()))
          })
        }
        return r
      },
      valid() {
        let p = (this.open_pk > -1 && (this.user.password.length === 0 || this.user.password.length >= 3)
          || (this.open_pk === -1 && this.user.password.length >= 3))
        return p && this.user.username !== '' && this.user.fio !== ''
      },
    },
  }
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
    height: calc(100% - 34px);
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

      .col-xs-6 {
        border-bottom: 1px solid #eaeaea;
      }
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
