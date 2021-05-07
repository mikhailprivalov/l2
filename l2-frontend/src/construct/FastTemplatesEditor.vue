<template>
  <modal ref="modal" @close="hide_modal" show-footer="true" white-bg="true" min-width="85%" margin-top>
    <span slot="header">Настройка шаблонов быстрого ввода ({{title}})</span>
    <div slot="body" style="min-height: 200px" class="directions-manage" v-if="loaded">
      <div class="directions-sidebar">
        <div class="inner">
          <div @click="select_template(d.pk)" class="direction" :class="{active: d.pk === selected_template, ishidden: d.hide}"
               :key="d.pk" v-for="d in rows">
            <div>{{d.title}}</div>
            <a href="#" @click.prevent.stop="copy_template(d.pk)"><i class="fa fa-copy"></i></a>
          </div>
        </div>
        <button class="btn btn-blue-nb" @click="add"><i class="fa fa-plus"></i> добавить</button>
      </div>
      <div class="directions-content" v-if="selected_template === -2"
           style="line-height: 200px;text-align: center;color:grey">
        Шаблон не выбран
      </div>
      <div class="directions-content" v-else>
        <div class="direction-data">
          <div class="results-top">
            <div>
              <label>
                Название: <input v-model="template_data.title" placeholder="Название" :readonly="template_data.readonly" />
              </label>
              <strong v-if="selected_template === -1">(новый шаблон)</strong>
            </div>
            <div>
              <label>Скрыть: <input v-model="template_data.hide" :disabled="template_data.readonly" type="checkbox" /></label>
            </div>
          </div>
          <div class="results-editor">
            <div class="ft-group" :key="`${group.pk}_${group.title}_${jg}`"
                 v-for="(group, jg) in groups">
              <div class="ft-group-title" v-if="group.title !== ''">{{group.title}}</div>
              <div class="ft-fields">
                <div class="ft-field" :key="`${field.pk}_${field.title}_${field.field_type}_${jf}`"
                     v-for="(field, jf) in group.fields"
                     :class="{disabled: template_data.readonly, required: field.required}">
                  <div v-if="field.title !== ''" class="ft-field-title">
                    {{field.title}}
                  </div>
                  <div class="ft-field-value" v-if="field.field_type === 0">
                    <textarea v-model="template_data.fields[field.pk]" :rows="field.lines" class="form-control"
                              v-if="field.lines > 1" :readonly="template_data.readonly"></textarea>
                    <input v-model="template_data.fields[field.pk]" class="form-control"
                           :readonly="template_data.readonly" v-else/>
                  </div>
                  <div class="ft-field-value mkb10" v-else-if="field.field_type === 2 && !template_data.readonly">
                    <m-k-b-field v-model="template_data.fields[field.pk]" :short="false" />
                  </div>
                  <div class="ft-field-value" v-else-if="field.field_type === 2 && template_data.readonly">
                    <input v-model="template_data.fields[field.pk]" readonly class="form-control" />
                  </div>
                  <div v-else>не доступно для заполнения</div>
                </div>
              </div>
            </div>
          </div>
          <div class="center" v-if="!template_data.readonly">
            <button class="btn btn-blue-nb" @click="save()" :disabled="(template_data.title || '').length === 0">
              Сохранить
            </button>
          </div>
        </div>
      </div>
    </div>
    <div slot="body" style="line-height: 200px;text-align: center" v-else>
      Загрузка данных...
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-8">
        </div>
        <div class="col-xs-4">
          <button type="button" @click="hide_modal" class="btn btn-primary-nb btn-blue-nb">
            Закрыть
          </button>
        </div>
      </div>
    </div>
  </modal>
</template>

<script>
import Modal from '../ui-cards/Modal.vue';
import MKBField from '../fields/MKBField.vue';
import researchesPoint from '../api/researches-point';
import * as actions from '../store/action-types';

export default {
  name: 'fast-templates-editor',
  components: { Modal, MKBField },
  props: {
    research_pk: {
      type: Number,
      required: true,
    },
    title: {
      type: String,
      required: true,
    },
    groups: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      rows: [],
      loaded: false,
      checked: false,
      selected_template: -2,
      template_data: {},
    };
  },
  created() {
    this.load_data();
  },
  watch: {
    selected_template() {
      if (this.selected_template !== -2) {
        for (const g of this.groups) {
          for (const f of g.fields) {
            if (!this.template_data.fields[f.pk] && this.template_data.fields[f.pk] !== '') {
              this.template_data.fields[f.pk] = f.default;
            }
          }
        }
        this.checked = true;
      }
    },
  },
  methods: {
    hide_modal() {
      this.$root.$emit('hide_fte');
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
    },
    clear() {
      this.checked = false;
      this.template_data = {};
      this.selected_template = -2;
    },
    add() {
      this.clear();
      this.template_data = {
        title: '',
        hide: false,
        readonly: false,
        fields: {},
      };
      this.selected_template = -1;
    },
    load_data(select_after) {
      this.loaded = false;
      this.clear();
      this.$store.dispatch(actions.INC_LOADING);
      researchesPoint.getFastTemplates({ pk: this.research_pk, all: true }).then(({ data }) => {
        this.rows = data;
        if (select_after) {
          this.select_template(select_after);
        }
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
        this.loaded = true;
      });
    },
    select_template(pk) {
      if (pk === this.selected_template) return;
      this.clear();
      this.$store.dispatch(actions.INC_LOADING);
      researchesPoint.getTemplateData({ pk }).then(({ data }) => {
        this.template_data = data;
        this.selected_template = pk;
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
      });
    },
    copy_template(pk) {
      this.clear();
      this.$store.dispatch(actions.INC_LOADING);
      researchesPoint.getTemplateData({ pk }).then(({ data }) => {
        this.template_data = {
          ...data, title: '', hide: false, readonly: false,
        };
        this.selected_template = -1;
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
      });
    },
    save() {
      this.loaded = false;
      this.$store.dispatch(actions.INC_LOADING);
      researchesPoint.saveFastTemplate({
        pk: this.selected_template,
        data: this.template_data,
        research_pk: this.research_pk,
      }).then(({ pk }) => {
        this.load_data(pk);
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
        this.loaded = true;
      });
    },
  },
};
</script>

<style scoped lang="scss">
  .modal-mask {
    align-items: stretch !important;
    justify-content: center !important;
  }

  ::v-deep .panel-flt {
    margin: 41px;
    align-self: stretch !important;
    width: 100%;
    display: flex;
    flex-direction: column;
  }

  ::v-deep .panel-body {
    flex: 1;
    padding: 0;
    height: calc(100% - 144px);
    min-height: 200px;
  }

  .directions-manage {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: stretch;
    flex-direction: row;
    flex-wrap: nowrap;
    align-content: stretch;
    & > div {
      align-self: stretch;
    }
  }

  .directions-sidebar {
    width: 300px;
    background: rgba(0, 0, 0, .04);
    border-right: 1px solid rgba(0, 0, 0, .16);
    position: relative;
    padding-bottom: 34px;
    .inner {
      height: 100%;
      width: 100%;
      overflow-y: auto;
      overflow-x: hidden;
    }
    .btn {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      border-radius: 0;
      width: 100%;
    }
  }

  .directions-content {
    display: flex;
    flex-direction: column;
    width: calc(100% - 300px);
  }

  .direction-data {
    flex: 1;
    padding: 5px 10px;
    overflow-y: auto;
  }

  .direction-control {
    height: 34px;
    display: flex;
    .btn {
      border-radius: 0;
      &:first-child {
        border-right: 1px solid #fff !important;
      }
    }
  }

  .direction {
    padding: 5px;
    margin: 5px;
    border-radius: 5px;
    border: 1px solid rgba(0, 0, 0, 0.14);
    background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);
    &.ishidden {
      opacity: .5;
      &:hover {
        opacity: 1;
      }
    }
    &:not(.active) {
      cursor: pointer;
      transition: all .2s cubic-bezier(.25, .8, .25, 1);
    }
    position: relative;

    &.active {
      background-image: linear-gradient(#6C7A89, #56616c);
      color: #fff;
    }

    hr {
      margin: 3px;
    }

    ol {
      padding-left: 25px;
      li {
        margin-bottom: 3px;
      }
    }

    &:not(.active):hover {
      box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
      z-index: 1;
      transform: scale(1.008);
    }

    a {
      position: absolute;
      display: inline-block;
      right: 2px;
      top: 2px;
      padding: 2px;
      &:hover {
        text-shadow: 0 1px 3px;
      }
    }

    &:not(.active) {
      padding-right: 14px;
    }
  }

  .direction-service {
    margin: 5px;
    border-radius: 5px;
    border: 1px solid rgba(0, 0, 0, 0.14);
    overflow: hidden;
    display: flex;
    background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);

    &.wrn {
      border: 1px solid #932a04;
      .s-code {
        background: #932a04;
      }
      .service-rmis {
        border-right: 1px solid #932a04;
      }
    }

    &.cancel {
      border: 1px solid rgba(0, 0, 0, 0.2);
      background: rgba(0, 0, 0, 0.2);
      .s-code {
        background: rgba(0, 0, 0, 0.2);
      }
      .service-rmis {
        border-right: 1px solid rgba(0, 0, 0, 0.2);
      }
    }

    .s-code {
      vertical-align: top;
      border-radius: 0;
      padding: 5px;
      display: block;
      text-align: left;
      font-size: 14px
    }

    .s-title {
      margin: 5px;
      display: block;
    }

    .service-rmis {
      border-right: 1px solid rgba(0, 0, 0, 0.14);
    }

    .service-l2 {
      padding: 5px;
    }

    .service-rmis, .service-l2 {
      flex: 1 50%;
    }
  }

  .service-department {
    display: inline-block;
    background: rgba(0, 0, 0, .08);
    padding: 2px;
    border-radius: 2px;
  }

  .no-attach {
    font-size: 12px;
    label {
      font-weight: 300;
    }
  }

  .fwn {
    font-weight: normal;
  }

  .l2-notice {
    color: #5e5e5e;
    font-weight: bold;
  }
  .results-root {
    display: flex;
    align-items: stretch;
    flex-direction: row;
    flex-wrap: nowrap;
    align-content: stretch;
    & > div {
      align-self: stretch;
    }
  }

  .results-sidebar {
    width: 294px;
    border-right: 1px solid #b1b1b1;
    display: flex;
    flex-direction: column;
  }

  .results-content {
    display: flex;
    flex-direction: column;
    width: calc(100% - 294px);
  }

  .results-top {
    border-bottom: 1px solid #b1b1b1;
    height: 59px;
    padding: 5px;
  }

  .results-top > div {
    font-family: "Courier New", Courier, monospace !important;
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
      border-radius: 0 !important;
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

  .research-title {
    position: sticky;
    top: 0;
    background-color: #ddd;
    text-align: center;
    padding: 5px;
    font-weight: bold;
    z-index: 2;
  }

  .results-editor {
    height: calc(100% - 96px);
    overflow-y: auto;
    overflow-x: hidden;
  }

  .ft-group {
    margin: 5px;
    border: 1px solid #c1c1c1;
  }

  .ft-group-title {
    background-color: #eaeaea;
    padding: 5px;
    font-weight: bold;
    position: sticky;
    top: 0;
    z-index: 1;
  }

  .sidebar-bottom-top {
    background-color: #eaeaea;
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
      width: 130px;
    }
  }

  .ft-fields {
    padding: 5px 5px 5px 10px;
  }

  .ft-field {
    display: flex;
    flex-direction: row;
    align-items: stretch;
    justify-content: stretch;
    & > div {
      align-self: stretch;
    }
    margin-top: 5px;
    margin-bottom: 5px;
    background-color: #fafafa;

    overflow: visible;

    &.open-field:not(.disabled) {
      background-color: #efefef;
      &.required {
        background-color: #e3e3e3;
      }
      .input-values {
        overflow: visible !important;
      }
      .input-values-wrap {
        z-index: 3;
      }
      .inner-wrap {
        background-color: #cfd9db;
        box-shadow: 0 3px 3px rgba(0, 0, 0, .4);
      }
      .form-control {
        border-color: #00a1cb;
      }
    }

    &.required {
      background-color: #e6e6e6;
      border-right: 3px solid #00a1cb;
    }
  }

  .ft-field-title {
    flex: 1 0 150px;
    padding-left: 5px;
    padding-top: 5px;
  }

  .ft-field-value {
    flex-basis: 100%;
    textarea {
      resize: none;
    }
    .form-control {
      width: 100%;
      border-radius: 0;
    }
  }

  .ft-field-inputs {
    flex: 1 0 250px;
    position: relative;
    overflow: visible;
  }

  .input-values-wrap {
    position: absolute;
    left: 0;
    top: 0;
    right: 0;
    bottom: 0;
    overflow: visible;
  }

  .input-values {
    width: 250px;
    height: 100%;
    overflow: hidden;
  }

  .inner-wrap {
    white-space: normal;
    padding: 3px;
    background-color: #ECF0F1;
  }

  .input-value {
    padding: 3px;
    background-color: #ECF0F1;
    border-radius: 2px;
    border: 1px solid #95A5A6;
    color: #656D78;
    display: inline-block;
    margin-bottom: 4px;
    margin-right: 4px;
    cursor: pointer;
    min-width: 20px;
    text-align: center;
    word-break: break-word;
  }

  .input-value:hover {
    background-color: #049372;
    border: 1px solid #03614b;
    color: #ffffff;
  }

  .control-row {
    height: 34px;
    background-color: #f3f3f3;
    display: flex;
    flex-direction: row;
    button {
      align-self: stretch;
      border-radius: 0;
    }
    div {
      align-self: stretch
    }
  }

  .res-title {
    padding: 5px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .status {
    padding: 5px;
    font-weight: bold;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .status-none {
    color: #CF3A24
  }

  .status-saved {
    color: #F4D03F
  }

  .status-confirmed {
    color: #049372
  }

  .direction {
    padding: 5px;
    margin: 5px;
    border-radius: 5px;
    border: 1px solid rgba(0, 0, 0, 0.14);
    background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);

    hr {
      margin: 3px;
    }
  }

  .text-ell {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .research-row {
    margin-top: 3px;
    margin-bottom: 3px;
    padding: 3px;
    background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);
  }

  .btn-field, .btn-field:focus {
    align-self: stretch;
    border-radius: 0;
    border-left: 0;
    border-right: 0;
    background: rgba(0, 0, 0, .06);
    border: none;
    margin-right: 5px;
    color: #000;
  }

  .btn-field:hover {
    background: rgba(0, 0, 0, .2);
    color: #fff;
  }

  .anamnesis {
    padding: 10px;
  }

  .status-list {
    display: flex;
  }

  .mkb10 {
    margin-right: -1px;
  }

  .mkb10 ::v-deep .input-group {
    border-radius: 0;
    width: 100%;
  }

  .mkb10 ::v-deep input {
    border-radius: 0!important;
  }

  .mkb10 ::v-deep ul {
    width: auto;
    right: -250px;
    font-size: 13px;
  }

  .mkb10 ::v-deep ul li {
    overflow: hidden;
    text-overflow: ellipsis;
    padding: 2px .25rem;
    margin: 0 .2rem;
    a {
      padding: 2px 10px;
    }
  }
</style>
