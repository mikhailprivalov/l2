<template>
  <div class="root">
    <div class="top-editor">
      <div
        class="input-group"
        style="width: 100%;"
      >
        <span class="input-group-addon">Название</span>
        <input
          v-model="title"
          type="text"
          class="form-control"
        >
        <label
          class="input-group-addon"
          style="height: 34px;text-align: left;"
        >
          <input
            v-model="global_template"
            type="checkbox"
          > {{ global_template ? 'Глобальный' : 'В поиске' }}
        </label>
      </div>
    </div>
    <div class="content-editor">
      <div class="row res-row">
        <div
          class="col-xs-6"
          style="height: 100%"
        >
          <ResearchesPicker
            v-if="researches !== null"
            v-model="researches"
            autoselect="none"
            :hidetemplates="true"
          />
        </div>
        <div
          class="col-xs-6"
          style="height: 100%"
        >
          <SelectedResearches
            :researches="researches || []"
            :simple="true"
          />
        </div>
      </div>
      <div style="padding: 5px;">
        <label style="margin-bottom: 5px"> <input
          v-model="showInResearchPicker"
          type="checkbox"
        > показывать как услугу </label>
        <template v-if="showInResearchPicker">
          <div
            class="input-group"
            style="width: 100%; margin-bottom: 5px;"
          >
            <span class="input-group-addon">Тип услуги</span>
            <select
              key="type"
              v-model="type"
              class="form-control"
            >
              <option
                v-for="t in TYPES"
                :key="t.id"
                :value="t.id"
              >
                {{ t.label }}
              </option>
            </select>
          </div>
          <div
            v-if="site_types_for_type.length > 0"
            class="input-group"
            style="width: 100%; margin-bottom: 5px"
          >
            <span class="input-group-addon">Место размещения</span>
            <select
              key="site_type"
              v-model="siteType"
              class="form-control"
            >
              <option
                v-for="t in site_types_for_type"
                :key="t.id"
                :value="t.id"
              >
                {{ t.label }}
              </option>
            </select>
          </div>
          <div
            v-if="type === 'lab'"
            class="input-group"
            style="width: 100%; margin-bottom: 5px"
          >
            <span class="input-group-addon">Лаборатория</span>
            <select
              key="lab"
              v-model="department"
              class="form-control"
            >
              <option
                v-for="t in departments"
                :key="t.id"
                :value="t.id"
              >
                {{ t.label }}
              </option>
            </select>
          </div>
          <div
            v-if="type === 'paraclinic'"
            class="input-group"
            style="width: 100%; margin-bottom: 5px"
          >
            <span class="input-group-addon">Подразделение</span>
            <select
              key="paraclinic"
              v-model="department"
              class="form-control"
            >
              <option
                v-for="t in departmentsParaclinic"
                :key="t.id"
                :value="t.id"
              >
                {{ t.label }}
              </option>
            </select>
          </div>
        </template>
      </div>
    </div>
    <div class="footer-editor">
      <button
        class="btn btn-blue-nb"
        @click="cancel"
      >
        Отмена
      </button>
      <button
        class="btn btn-blue-nb"
        :disabled="!valid"
        @click="save"
      >
        Сохранить
      </button>
    </div>
  </div>
</template>

<script lang="ts">
import ResearchesPicker from '../ui-cards/ResearchesPicker.vue';
import SelectedResearches from '../ui-cards/SelectedResearches.vue';
import construct_point from '../api/construct-point';
import * as actions from '../store/action-types';

const TYPES = [
  {
    label: 'Лаборатория',
    id: 'lab',
  },
  {
    label: 'Параклиника',
    id: 'paraclinic',
  },
  {
    label: 'Консультации',
    id: 'consult',
  },
  {
    label: 'Лечение',
    id: 'treatment',
  },
  {
    label: 'Стоматология',
    id: 'stom',
  },
  {
    label: 'Стационар',
    id: 'hospital',
  },
  {
    label: 'Микробиология',
    id: 'microbiology',
  },
  {
    label: 'Цитология',
    id: 'citology',
  },
  {
    label: 'Гистология',
    id: 'gistology',
  },
];

export default {
  name: 'TemplateEditor',
  components: {
    ResearchesPicker,
    SelectedResearches,
  },
  props: {
    pk: {
      type: Number,
      required: true,
    },
    global_template_p: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      title: '',
      cancel_do: false,
      loaded_pk: -2,
      researches: null,
      has_unsaved: false,
      global_template: false,
      TYPES,
      showInResearchPicker: false,
      type: TYPES[0].id,
      department: null,
      departments: [],
      departmentsParaclinic: [],
      siteType: null,
      siteTypes: {},
    };
  },
  computed: {
    valid() {
      return this.norm_title.length > 0 && this.researches && this.researches.length > 0;
    },
    norm_title() {
      return this.title.trim();
    },
    site_types_for_type() {
      return this.siteTypes[this.type] || [];
    },
  },
  watch: {
    pk() {
      this.load();
    },
    loaded_pk() {
      this.has_unsaved = false;
    },
    groups: {
      handler(n, o) {
        if (o && o.length > 0) {
          this.has_unsaved = true;
        }
      },
      deep: true,
    },
    site_types_for_type() {
      if (!this.site_types_for_type.find(t => t.id === this.siteType)) {
        if (this.siteType && this.site_types_for_type.length === 0) {
          this.siteType = null;
        } else if (this.site_types_for_type.length > 0) {
          this.siteType = this.site_types_for_type[0].id;
        } else {
          this.siteType = null;
        }
      }
    },
    type() {
      if (this.type === 'lab' && this.departments.length > 0) {
        if (!this.department || !this.departments.find(d => d.id === this.department)) {
          this.department = this.departments[0].id;
        }
      } else if (this.type === 'paraclinic' && this.departmentsParaclinic.length > 0) {
        if (!this.department || !this.departmentsParaclinic.find(d => d.id === this.department)) {
          this.department = this.departmentsParaclinic[0].id;
        }
      } else {
        this.department = null;
      }
    },
    showInResearchPicker() {
      if (this.type === 'unknown' && this.showInResearchPicker) {
        this.type = 'lab';
      }
    },
  },
  created() {
    this.load();
  },
  mounted() {
    window.$(window).on('beforeunload', () => {
      if (this.has_unsaved && this.loaded_pk > -2 && !this.cancel_do) {
        return 'Изменения, возможно, не сохранены. Вы уверены, что хотите покинуть страницу?';
      }

      return undefined;
    });
  },
  methods: {
    load() {
      this.title = '';
      this.researches = null;
      this.global_template = this.global_template_p === 1;
      if (this.pk >= 0) {
        this.$store.dispatch(actions.INC_LOADING);
        fetch(`/api/get-template?pk=${this.pk}`)
          .then(r => r.json())
          .then(data => {
            this.title = data.title;
            this.researches = data.researches;
            this.global_template = data.global_template;
            this.showInResearchPicker = data.showInResearchPicker;
            this.type = data.type || TYPES[0].id;
            this.department = data.department || null;
            this.siteType = data.siteType || null;
            this.departments = data.departments || [];
            this.departmentsParaclinic = data.departmentsParaclinic || [];
            this.siteTypes = data.siteTypes || {};
          })
          .finally(() => {
            this.$store.dispatch(actions.DEC_LOADING);
          });
      } else {
        this.researches = [];
      }
    },
    cancel() {
      // eslint-disable-next-line no-restricted-globals,no-alert
      if (this.has_unsaved && !confirm('Изменения, возможно, не сохранены. Вы уверены, что хотите отменить редактирование?')) {
        return;
      }
      this.cancel_do = true;
      this.$root.$emit('research-editor:cancel');
    },
    save() {
      this.$store.dispatch(actions.INC_LOADING);
      construct_point
        .updateTemplate(this, [
          'pk',
          'title',
          'researches',
          'global_template',
          'showInResearchPicker',
          'type',
          'department',
          'siteType',
        ])
        .then(() => {
          this.has_unsaved = false;
          this.$root.$emit('msg', 'ok', 'Сохранено');
          this.cancel();
        })
        .finally(() => {
          this.$store.dispatch(actions.DEC_LOADING);
        });
    },
  },
};
</script>

<style>
body {
  overflow-x: hidden;
}
</style>

<style scoped lang="scss">
.top-editor {
  flex: 0 0 34px;

  .left,
  .right {
    flex: 0 0 50%;
  }

  .left {
    border-right: 1px solid #96a0ad;
  }

  .input-group-addon {
    border-top: none;
    border-left: none;
    border-radius: 0;
  }

  .form-control {
    border-top: none;
    border-radius: 0;
  }

  .input-group > .form-control:last-child {
    border-right: none;
  }
}

.content-editor {
  height: 100%;
}

.footer-editor {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 34px;
  display: flex;
  justify-content: flex-end;
  background-color: #f4f4f4;

  .btn {
    border-radius: 0;
  }
}

.top-editor,
.content-editor {
  align-self: stretch;
}

.root {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  align-content: stretch;
}

.group {
  padding: 5px;
  margin: 5px;
  border-radius: 5px;
  background: #f0f0f0;
}

.field {
  padding: 5px;
  margin: 5px;
  border-radius: 5px;
  background: #fff;
  color: #000;
}

.field-inner {
  display: flex;
  flex-direction: row;
  align-items: stretch;
}

.field-inner > div {
  align-self: stretch;
  textarea {
    resize: none;
  }

  &:nth-child(1) {
    flex: 0 0 35px;
    padding-right: 5px;
  }
  &:nth-child(2) {
    width: 100%;
  }
  &:nth-child(3) {
    width: 140px;
    padding-left: 5px;
    padding-right: 5px;
    white-space: nowrap;
    label {
      display: block;
      margin-bottom: 2px;
      width: 100%;
      input[type='number'] {
        width: 100%;
      }
    }
  }
}

.lob {
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
}

.nob {
  border-radius: 0;
}

::v-deep .v-collapse-content-end {
  max-height: 10000px !important;
}

.res-row {
  height: 300px;
  border-bottom: 1px solid #aaa;
}
</style>
