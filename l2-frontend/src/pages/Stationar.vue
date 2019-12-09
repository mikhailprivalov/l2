<template>
  <div ref="root" class="root">
    <div class="sidebar">
      <div class="sidebar-top">
        <input type="text" class="form-control" v-model="pk" @keyup.enter="load" autofocus
               placeholder="Номер истории"/>
        <button class="btn btn-blue-nb" @click="load">Загрузить</button>
      </div>
        <div class="sidebar-content">
          <div class="inner">

          </div>
      </div>
    </div>
    <div class="content">

    </div>
  </div>
</template>

<script>
    import {mapGetters} from 'vuex'

    export default {
        components: {},
        data() {
            return {
                pk: '',
            }
        },
        methods: {
            load() {},
        },
        computed: {
            ...mapGetters({
                user_data: 'user_data',
                researches: 'researches',
            }),
        }
    }
</script>

<style scoped lang="scss">
  .root {
    display: flex;
    align-items: stretch;
    flex-direction: row;
    flex-wrap: nowrap;
    align-content: stretch;

    & > div {
      align-self: stretch;
    }
  }

  .sidebar {
    width: 304px;
    border-right: 1px solid #b1b1b1;
    display: flex;
    flex-direction: column;
  }

  .content {
    display: flex;
    flex-direction: column;
    width: calc(100% - 304px);
  }

  .sidebar-top {
    flex: 0 0 34px;
    display: flex;
    flex-direction: row;
    align-items: stretch;
    flex-wrap: nowrap;
    justify-content: stretch;

    input, button {
      align-self: stretch;
      border: none;
      border-radius: 0;
    }

    input {
      border-bottom: 1px solid #b1b1b1;
      width: 199px !important;
      flex: 2 199px;
    }

    button {
      flex: 3 94px;
      width: 94px
    }
  }

  .sidebar-content {
    position: relative;
    height: calc(100% - 34px);
  }
</style>
