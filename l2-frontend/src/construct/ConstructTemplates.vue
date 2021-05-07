<template>
  <div ref="root" class="construct-root">
    <div class="construct-sidebar" v-show="opened_id === -2">
      <div class="sidebar-select">
        <select-picker-m style="height: 34px;" :options="types" v-model="type"/>
      </div>
      <div class="sidebar-content" :class="{fcenter: templates_list.length === 0}">
        <div v-if="templates_list.length === 0">Не найдено</div>
        <div class="research" :class="{rhide: row.hide}"
             :key="row.pk" v-for="row in rows"
             @click="open_editor(row.pk)">
          <div class="t-t">{{row.title}}</div>
          <div v-for="res in row.researches" :key="res.pk" class="t-r">
            {{res.title}}
          </div>
        </div>
      </div>
      <button class="btn btn-blue-nb sidebar-footer" @click="open_editor(-1)">
        <i class="glyphicon glyphicon-plus"></i>
        Добавить
      </button>
    </div>
    <div class="construct-content">
      <template-editor style="position: absolute;top: 0;right: 0;bottom: 0;left: 0;" v-if="opened_id > -2" :pk="opened_id"
                       :global_template_p="parseInt(type, 10)" />
    </div>
  </div>
</template>

<script>
import SelectPickerM from '../fields/SelectPickerM.vue';
import TemplateEditor from './TemplateEditor.vue';
import * as actions from '../store/action-types';

export default {
  components: {
    SelectPickerM,
    TemplateEditor,
  },
  name: 'construct-templates',
  data() {
    return {
      type: 1,
      templates_list: [],
      opened_id: -2,
      inLoading: true,
    };
  },
  created() {
    this.$parent.$on('research-editor:cancel', this.cancel_edit);

    this.$store.dispatch(actions.INC_LOADING);
    this.$store.dispatch(actions.GET_RESEARCHES).finally(() => {
      this.$store.dispatch(actions.DEC_LOADING);
    });

    this.$store.watch((state) => state.researches, () => {
      this.load_templates();
    });
  },
  methods: {
    load_templates() {
      this.templates_list = [];
      fetch(`/api/load-templates?type=${this.type}`).then((r) => r.json()).then((data) => {
        this.templates_list = data.result;
      });
    },
    open_editor(pk) {
      this.opened_id = pk;
    },
    cancel_edit() {
      this.opened_id = -2;
      this.load_templates();
    },
  },
  watch: {
    type() {
      this.load_templates();
    },
  },
  computed: {
    types() {
      return [
        { value: 1, label: 'Global' },
        { value: 2, label: 'Searchable' },
      ];
    },
    rows() {
      return this.templates_list.map(
        (r) => ({ ...r, researches: r.researches.map((rpk) => this.$store.getters.researches_obj[rpk]).filter(Boolean) }),
      );
    },
  },
};
</script>

<style scoped lang="scss">
  .construct-root {
    display: flex;
    align-items: stretch;
    flex-direction: row;
    flex-wrap: nowrap;
    align-content: stretch;
    & > div {
      align-self: stretch;
    }
  }

  .construct-sidebar {
    width: 350px;
    border-right: 1px solid #b1b1b1;
    display: flex;
    flex-direction: column;

    .form-control {
      border-radius: 0;
      border-top: none;
      border-left: none;
      border-right: none;
    }
  }

  .construct-content {
    width: 100%;
    position: relative;
  }

  .sidebar-select ::v-deep .btn {
    border-radius: 0;
    border-top: none;
    border-left: none;
    border-right: none;
    border-top: 1px solid #fff;
  }

  .sidebar-select, .sidebar-filter, .sidebar-footer {
    flex: 0 0 34px;
  }

  .sidebar-content {
    height: 100%;
    overflow-y: auto;
    background-color: hsla(30, 3%, 97%, 1);
  }

  .sidebar-content:not(.fcenter) {
    padding-bottom: 10px;
  }

  .sidebar-footer {
    border-radius: 0;
    margin: 0;
  }

  .fcenter {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .research {
    background-color: #fff;
    padding: 5px;
    margin: 10px;
    border-radius: 4px;
    cursor: pointer;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
    transition: all .2s cubic-bezier(.25, .8, .25, 1);
    position: relative;

    &.rhide {
      background-image: linear-gradient(#6C7A89, #56616c);
      color: #fff;
    }

    hr {

    }

    &:hover {
      box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
      z-index: 1;
      transform: scale(1.008);
    }
  }

  .research:not(:first-child) {
    margin-top: 0;
  }

  .research:last-child {
    margin-bottom: 0;
  }

  .t-t {
    font-weight: bold;
  }

  .t-r {
    font-size: 80%;
    padding-left: 5px;
  }
</style>
