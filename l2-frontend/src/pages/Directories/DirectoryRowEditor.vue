<template>
  <div v-frag>
    <MountingPortal
      mount-to="#portal-place-modal"
      name="DirectoryRowEditor"
      append
    >
      <transition name="fade">
        <Modal
          v-if="pk !== null"
          white-bg="true"
          show-footer="true"
          max-width="710px"
          width="100%"
          margin-left-right="auto"
          margin-top
          :z-index="5001"
          @close="cancel"
        >
          <span slot="header">{{ editTitle }}</span>
          <div
            slot="body"
            class="value-body"
          >
            <div v-if="!data">
              <i class="fa fa-spinner" /> загрузка
            </div>
            <div v-else>
              <div
                class="input-group"
                style="margin-bottom: 5px;"
              >
                <span class="input-group-addon">Название записи</span>
                <input
                  v-model.trim="data.recordParams.title"
                  type="text"
                  class="form-control"
                  placeholder="Название записи"
                >
              </div>
              <div
                class="input-group"
                style="margin-bottom: 5px;"
              >
                <span class="input-group-addon">Код записи</span>
                <input
                  v-model.trim="data.recordParams.code"
                  type="text"
                  class="form-control"
                  placeholder="Код записи"
                >
              </div>
              <label><input
                v-model="data.recordParams.hide"
                type="checkbox"
              > скрыть запись</label>
              <div
                v-for="(f, fpk) in data.fields"
                :key="fpk"
                class="input-group"
                style="margin-bottom: 5px;"
              >
                <span class="input-group-addon">{{ f.title }}</span>
                <DynamicDirectoryField
                  v-if="f.type === 4"
                  v-model="f.value"
                  :edit-title="f.title"
                  :directory="f.linkedDirectory"
                  id-mode
                />
                <textarea
                  v-else-if="f.type === 1"
                  v-model.trim="f.value"
                  class="form-control"
                  :placeholder="f.title"
                />
                <input
                  v-else-if="f.type === 2"
                  v-model="f.value"
                  type="number"
                  class="form-control"
                  :placeholder="f.title"
                >
                <input
                  v-else-if="f.type === 3"
                  v-model="f.value"
                  type="date"
                  class="form-control"
                  :placeholder="f.title"
                >
                <input
                  v-else
                  v-model.trim="f.value"
                  type="text"
                  class="form-control"
                  :placeholder="f.title"
                >
                <span
                  v-if="f.isRequired"
                  class="input-group-addon"
                >обязательное</span>
              </div>
              <div
                class="input-group"
                style="margin: 15px 0 5px 0;"
              >
                <span class="input-group-addon">Строковое значение</span>
                <input
                  :value="strValue"
                  readonly
                  type="text"
                  class="form-control"
                >
              </div>
            </div>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-4">
                <button
                  class="btn btn-blue-nb"
                  type="button"
                  @click="cancel"
                >
                  Отмена
                </button>
              </div>
              <div class="col-xs-8 text-right">
                <button
                  class="btn btn-blue-nb"
                  type="button"
                  :disabled="blockSave"
                  @click="save()"
                >
                  {{ saveTitle }}
                </button>
                <button
                  class="btn btn-blue-nb"
                  type="button"
                  :disabled="blockSave"
                  @click="save(true)"
                >
                  {{ saveTitle }} и закрыть
                </button>
              </div>
            </div>
          </div>
        </Modal>
      </transition>
    </MountingPortal>
  </div>
</template>

<script lang="ts">
import { debounce } from 'lodash/function';

import * as actions from '@/store/action-types';
import Modal from '@/ui-cards/Modal.vue';
import DynamicDirectoryField from '@/fields/DynamicDirectoryField.vue';

const FIELDS_RE = /({\d+})/g;

export default {
  name: 'DirectoryRowEditor',
  components: {
    Modal,
    DynamicDirectoryField,
  },
  props: {
    directory: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      pk: null,
      data: null,
      strValue: '',
    };
  },
  computed: {
    editTitle() {
      if (this.pk !== -1) {
        return 'Редактирование записи';
      }
      return 'Создание записи';
    },
    saveTitle() {
      if (this.pk !== -1) {
        return 'Сохранить изменения';
      }
      return 'Добавить запись';
    },
    blockSave() {
      if (!this.data) {
        return false;
      }

      if (!this.data.recordParams.title) {
        return true;
      }

      return Object.keys(this.data.fields).some(f => this.data.fields[f].isRequired && !this.data.fields[f].value);
    },
    strValueTemplate() {
      const { strValueTemplate } = this.data?.directoryData || {};
      return strValueTemplate || null;
    },
    strValueTemplateFields() {
      if (this.strValueTemplate) {
        const matches = this.strValueTemplate.match(FIELDS_RE) || [];

        return matches.map(m => m.replace('{', '').replace('}', ''));
      }
      return [];
    },
  },
  watch: {
    data: {
      deep: true,
      immediate: true,
      handler() {
        this.makeStrValueDebounced();
      },
    },
  },
  mounted() {
    this.$root.$on('directory-row-editor:open', pk => this.open(pk));
  },
  methods: {
    open(pk) {
      this.pk = pk;
      this.data = null;
      this.strValue = '';
      this.loadData();
    },
    cancel() {
      this.pk = null;
      this.data = null;
      this.strValue = '';
    },
    async save(withClose) {
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, version } = await this.$api('dynamic-directory/save-record', this, ['pk', 'directory'], this.data);
      if (ok) {
        this.data = { ...this.data };
        this.data.recordParams.lastVersion = version;
        this.$root.$emit('msg', 'ok', 'Запись сохранена');
        if (withClose) {
          this.cancel();
        }
      } else {
        this.$root.$emit('msg', 'error', 'Ошибка');
      }
      await this.$store.dispatch(actions.DEC_LOADING);
      this.$root.$emit('directory-row-editor:saved');
    },
    async loadData() {
      await this.$store.dispatch(actions.INC_LOADING);
      const data = await this.$api('dynamic-directory/record-for-edit', this, ['pk', 'directory']);
      this.data = data;
      if (!data) {
        this.cancel();
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    makeStrValue() {
      const { strValueTemplate } = this;
      if (!strValueTemplate) {
        return;
      }

      const fields = this.strValueTemplateFields;
      let v = strValueTemplate;

      for (const f of fields) {
        v = v.replace(new RegExp(`\\{${f}\\}`, 'g'), this.data.fields[f]?.value || '');
      }
      v = v.replace(/\{title\}/g, this.data.recordParams?.title || '');

      this.strValue = v;
    },
    makeStrValueDebounced: debounce(function () {
      this.makeStrValue();
    }, 100),
  },
};
</script>

<style lang="scss" scoped>
.value-body {
  padding: 10px;
}

.modal-mask {
  align-items: stretch !important;
  justify-content: stretch !important;
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
  height: calc(100% - 91px);
  min-height: 200px;
}

::v-deep .formulate-input .formulate-input-element {
  max-width: 1000px;
}
</style>
