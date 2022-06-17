<template>
  <div class="root">
    <div class="left">
      <div class="sidebar-bottom-top">
        <input
          v-model.trim="q"
          type="text"
          class="form-control"
          placeholder="Поиск справочника"
        >
      </div>
      <div
        v-if="!loading"
        class="left-wrapper"
      >
        <div
          v-for="d in rows"
          :key="d.pk"
          class="directory"
          :class="d.pk === openedDirectoryPk && 'active'"
          @click="openDirectory(d.pk)"
        >
          <div class="directory-param">
            <strong>{{ d.title }}</strong>
          </div>
          <div
            v-if="d.code"
            class="directory-param"
          >
            {{ d.code }}
          </div>
          <div class="directory-param">
            Создан: {{ d.createdAt }}
          </div>
          <div class="directory-param">
            Обновлён: {{ d.updatedAt }}
          </div>
          <div class="directory-param">
            Записей: {{ d.rows }}
          </div>
        </div>
        <!-- <button
          class="btn btn-primary-nb btn-blue-nb"
        >
          Добавить справочник
        </button> -->
      </div>
      <div
        v-else
        class="left-wrapper loading"
      >
        <i class="fa fa-spinner" />
      </div>
    </div>
    <Directory
      v-if="openedDirectoryPk !== -1"
      :key="openedDirectoryPk"
      :pk="openedDirectoryPk"
    />
  </div>
</template>

<script lang="ts">
import { debounce } from 'lodash/function';

import Directory from './Directory.vue';

export default {
  name: 'Directories',
  components: {
    Directory,
  },
  data() {
    return {
      q: '',
      rows: [],
      loading: false,
      actualReq: 0,
      openedDirectoryPk: -1,
    };
  },
  watch: {
    q() {
      this.debouncedSearch();
    },
  },
  mounted() {
    this.search();
    this.$root.$on('directory-row-editor:saved', () => {
      this.search();
    });
  },
  methods: {
    async search() {
      this.loading = true;
      this.actualReq += 1;
      const currentReq = this.actualReq;
      const { rows } = await this.$api('dynamic-directory/list', { q: this.q });
      if (this.actualReq !== currentReq) {
        return;
      }
      this.rows = rows;
      this.loading = false;
    },
    debouncedSearch: debounce(function () {
      this.search();
    }, 300),
    openDirectory(pk) {
      this.openedDirectoryPk = pk;
    },
  },
};
</script>

<style lang="scss" scoped>
  .root {
    position: absolute;
    top: 36px;
    right: 0;
    bottom: 0;
    left: 0;
    display: flex;

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

    &.loading {
      text-align: center;
    }
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

  .directory {
    margin-bottom: 10px;
    padding: 5px;
    border: 1px solid #aaa;
    border-radius: 5px;
    background: #fff;
    cursor: pointer;

    &:hover {
      background: #eaeaea;
    }

    &.active {
      background: #efefef;
    }

    &-param {
      & + & {
        border-top: 1px solid #bbb;
        margin-top: 3px;
      }
    }
  }
</style>
