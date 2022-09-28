<template>
  <div v-frag>
    <div
      v-if="directoryData"
      class="right"
    >
      <div class="sidebar-bottom-top">
        <span>Просмотр справочника {{ directoryData.title }}</span>
      </div>
      <div class="right-wrapper">
        <table class="table table-bordered">
          <tbody>
            <tr>
              <th>Код справочника</th>
              <td v-if="directoryData.code">
                {{ directoryData.code }}
              </td>
              <td
                v-else
                class="td-empty"
              >
                пусто
              </td>
            </tr>
            <tr>
              <th>Создан</th>
              <td>
                {{ directoryData.createdAt }}
              </td>
            </tr>
            <tr>
              <th>Обновлён</th>
              <td>
                {{ directoryData.updatedAt }}
              </td>
            </tr>
            <tr>
              <th>Записей</th>
              <td>
                {{ directoryData.rows }}
              </td>
            </tr>
          </tbody>
        </table>

        <button
          v-if="canEdit"
          class="btn btn-blue-nb btn-block"
          style="margin-bottom: 10px;"
          @click="$root.$emit('directory-row-editor:open', -1)"
        >
          <i class="glyphicon glyphicon-plus" />
          Создать запись
        </button>

        <DirectoryRows
          :pk="pk"
          :can-edit="canEdit"
        />

        <DirectoryRowEditor :directory="pk" />
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import * as actions from '@/store/action-types';

import DirectoryRows from './DirectoryRows.vue';
import DirectoryRowEditor from './DirectoryRowEditor.vue';

export default {
  name: 'Directory',
  components: {
    DirectoryRows,
    DirectoryRowEditor,
  },
  props: {
    pk: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      directoryData: null,
    };
  },
  computed: {
    canEdit() {
      return this.directoryData && this.$store.getters.hasAnyGroup(this.directoryData.editAccess);
    },
  },
  mounted() {
    this.openDirectory();
    this.$root.$on('directory-row-editor:saved', () => {
      this.openDirectory(true);
    });
  },
  methods: {
    async openDirectory(isReloading) {
      await this.$store.dispatch(actions.INC_LOADING);
      if (!isReloading) {
        this.directoryData = null;
        this.directoryRows = null;
        this.page = 1;
        this.pages = 1;
      }
      const directoryData = await this.$api('dynamic-directory/get', this, 'pk');
      this.directoryData = directoryData;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
};
</script>

<style lang="scss" scoped>
  .right {
    height: 100%;
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

  .td-empty {
    text-align: center;
    color: #999;
    font-style: italic;
  }

  .right-wrapper {
    background: #fff;
    position: absolute;
    top: 34px;
    right: 0;
    bottom: 0;
    left: 0;
    overflow-y: auto;
    padding: 5px;
  }
</style>
