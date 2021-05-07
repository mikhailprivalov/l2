<template>
  <div class="root">
    <div class="left">
      <div class="sidebar-bottom-top">
        <span>Новая запись</span>
        <date-field-nav :brn="false" :right="true" :val.sync="date" :def="date"/>
      </div>
      <div class="left-wrapper">
          <div class="form-group">
            <label>Исполнитель:
              <select v-model="executor" class="form-control">
                <option v-for="user in users" :value="user.pk" :key="user.pk">{{user.fio}} – {{user.username}}</option>
              </select>
            </label>
          </div>
          <div class="form-group">
            <label>Тип работ:
              <select v-model="type" class="form-control">
                <option v-for="t in types" :value="t.pk" :key="t.pk">{{t.title}}</option>
              </select>
            </label>
          </div>
          <div class="form-group">
            <label>Количество:
              <input type="number" min="1" v-model="count" class="form-control" />
            </label>
          </div>
          <button class="btn btn-primary-nb btn-blue-nb" @click="save">Создать запись</button>
      </div>
    </div>
    <div class="right">
      <div class="sidebar-bottom-top">
        <span>Просмотр записей за {{date}}</span>
      </div>
      <div class="right-wrapper">
        <table class="table table-bordered table-condensed table-striped">
          <colgroup>
            <col/>
            <col/>
            <col width="60"/>
            <col width="160"/>
            <col width="70"/>
          </colgroup>
          <thead>
          <tr>
            <th>Исполнитель</th>
            <th>Тип работ</th>
            <th>Количество</th>
            <th>Сохраненено</th>
            <th></th>
          </tr>
          </thead>
          <tbody>
            <tr v-for="row in rows" :class="{canceled: row.canceled}" :key="row.pk">
              <td>{{row.executor}}</td>
              <td>{{row.type}}</td>
              <td>{{row.count}}</td>
              <td>{{row.saved}}</td>
              <td>
                <button @click="cancel(row.pk, true)" v-if="!row.canceled" class="btn btn-default btn-blue2-nb">отмена</button>
                <button @click="cancel(row.pk, false)" v-else class="btn btn-default btn-blue2-nb">вернуть</button>
              </td>
            </tr>
            <tr v-if="rows.length === 0">
              <td colspan="5" style="text-align: center">нет данных</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import moment from 'moment';
import usersPoint from '../api/user-point';
import * as actions from '../store/action-types';
import DateFieldNav from '../fields/DateFieldNav.vue';

export default {
  name: 'employee-jobs',
  components: { DateFieldNav },
  data() {
    return {
      date: moment().format('DD.MM.YYYY'),
      users: [],
      types: [],
      rows: [],
      executor: null,
      type: null,
      count: 1,
    };
  },
  watch: {
    date() {
      this.loadRows();
    },
  },
  async created() {
    await this.$store.dispatch(actions.INC_LOADING);
    const { types, users } = await usersPoint.loadJobTypes();
    this.types = types;
    this.users = users;
    this.type = types[0].pk;
    this.executor = users[0].pk;
    await this.loadRows();
    await this.$store.dispatch(actions.DEC_LOADING);
  },
  methods: {
    async save() {
      await this.$store.dispatch(actions.INC_LOADING);
      await usersPoint.saveJob({
        date: this.date,
        type: this.type,
        executor: this.executor,
        count: this.count,
      });
      await this.loadRows();
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async loadRows() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { list } = await usersPoint.loadJobs(this, 'date');
      this.rows = list;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async cancel(pk, cancel) {
      await this.$store.dispatch(actions.INC_LOADING);
      await usersPoint.jobCancel({
        pk, cancel,
      });
      await this.loadRows();
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
};
</script>

<style lang="scss" scoped>
  .root {
    height: calc(100% - 36px);
    display: flex;
    margin-right: -11px;

    .btn:focus {
      background-color: #aab2bd;
    }
  }

  .left, .right {
    height: 100%;
  }

  .left {
    border-right: 1px solid #646d78;
    padding: 0;
    width: 320px;
    margin-left: -5px;

    .sidebar-bottom-top {
      height: 34px;
    }

    input, select, button {
      border-radius: 0;
      width: 100%;
    }

    label {
      width: 100%;
    }
  }

  .left-wrapper {
    height: calc(100% - 34px);
    padding: 5px;
    overflow-y: auto;
  }

  .right {
    width: calc(100% - 321px);
    overflow: hidden;
    position: relative;
    margin-right: -5px;

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

  .sidebar-bottom-top {
    background-color: #eaeaea;
    height: 34px;
    flex: 0 0 34px;
    display: flex;
    justify-content: flex-start;
    align-items: center;

    ::v-deep .form-control {
      border-radius: 0;
      border-top: none;
      border-left: none;
      border-right: none;
    }

    span {
      display: inline-block;
      white-space: nowrap;
      padding-left: 5px;
      width: 160px;
    }
  }

  .canceled:not(:hover) {
    text-decoration: line-through;
    color: #999;
  }
  .canceled:hover {
    color: #7a7a7a;
  }
</style>
