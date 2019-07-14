<template>
  <div class="root">
    <div class="left">
      <div class="sidebar-bottom-top">
        <span>Новая запись</span>
        <date-field-nav :brn="false" :right="true" :val.sync="date" :def="date"/>
      </div>
      <div class="left-wrapper">

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
            <col width="80"/>
            <col width="60"/>
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
  import moment from 'moment'
  import users_point from './api/user-point'
  import * as action_types from './store/action-types'
  import DateFieldNav from './DateFieldNav'

  export default {
    name: 'employee-jobs',
    components: {DateFieldNav},
    data() {
      return {
        date: moment().format('DD.MM.YYYY'),
        types: [],
        rows: [],
      }
    },
    created() {
      (async() => {
        this.$store.dispatch(action_types.INC_LOADING).then()
        const {types} = await users_point.loadJobTypes()
        this.types = types
        this.$store.dispatch(action_types.DEC_LOADING).then()
      })().then();
    },
    methods: {
    },
  }
</script>

<style lang="scss" scoped>
  .root {
    height: calc(100% - 36px);
    display: flex;
    margin-right: -11px;
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

    input {
      border-radius: 0;
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

    /deep/ .form-control {
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
</style>
