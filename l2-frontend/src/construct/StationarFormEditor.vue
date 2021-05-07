<template>
  <div class="root">
    <div class="top-editor">
      <div class="left">
        <div class="input-group">
          <span class="input-group-addon">Стационарная услуга</span>
          <select-field-titled :variants="researches_list" v-model="main_service_pk"/>
        </div>
      </div>
      <div class="right">
        <div class="input-group">
          <label class="input-group-addon" style="height: 34px;text-align: left;">
            <input type="checkbox" v-model="hide"/> Скрытие
          </label>
        </div>
      </div>
    </div>
    <div class="content-editor">
      <paraclinic-research-editor style="position: absolute;top: 0;right: 0;bottom: 0;left: 0;" simple
                                  :main_service_pk="main_service_pk"
                                  :hs_pk="pk"
                                  :hide_main="hide"
                                  :pk="slave_service_pk" :department="department"/>
    </div>
  </div>
</template>

<script>
import ParaclinicResearchEditor from './ParaclinicResearchEditor.vue';
import * as actions from '../store/action-types';
import construct_point from '../api/construct-point';
import researchesPoint from '../api/researches-point';
import SelectFieldTitled from '../fields/SelectFieldTitled.vue';

export default {
  name: 'stationar-form-editor',
  components: { SelectFieldTitled, ParaclinicResearchEditor },
  props: {
    pk: {
      type: Number,
      required: true,
    },
    department: {
      type: Number,
      required: true,
    },
  },
  created() {
    this.load();
  },
  data() {
    return {
      hide: false,
      has_unsaved: false,
      loaded_pk: -2,
      main_service_pk: -1,
      slave_service_pk: -1,
      researches_list: [],
    };
  },
  watch: {
    pk() {
      this.load();
    },
    loaded_pk() {
      this.has_unsaved = false;
    },
  },
  methods: {
    async load() {
      this.hide = false;
      this.research = -1;
      this.main_service_pk = -1;
      this.slave_service_pk = -1;
      await this.$store.dispatch(actions.INC_LOADING);
      const { researches } = await researchesPoint.getResearchesByDepartment({ department: -5 });
      this.researches_list = researches;
      if (this.pk >= 0) {
        const data = await construct_point.hospServiceDetails(this, 'pk');

        this.main_service_pk = data.main_service_pk;
        this.slave_service_pk = data.slave_service_pk;
        this.hide = data.hide;
        this.loaded_pk = this.pk;
      }
      await this.$store.dispatch(actions.DEC_LOADING);
      if (this.main_service_pk === -1) {
        this.main_service_pk = this.researches_list[0].pk;
      }
    },
  },
};
</script>

<style scoped lang="scss">
  .top-editor {
    display: flex;
    width: 100%;
    flex: 0 0 34px;

    .left {
      flex: 0 0 calc(100% - 100px);
      ::v-deep .form-control {
        width: 100%;
      }
    }

    .right {
      flex: 0 0 100px
    }

    .input-group-addon {
      border-top: none;
      border-left: none;
      border-right: none;
      border-radius: 0;
    }

    ::v-deep .form-control {
      border-top: none;
      border-radius: 0;
    }
  }

  .content-editor {
    height: 100%;
    position: relative;
  }

  .top-editor, .content-editor{
    align-self: stretch;
  }

  .root {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    align-content: stretch;
  }

  .content-editor {
    overflow: visible;
  }
</style>
