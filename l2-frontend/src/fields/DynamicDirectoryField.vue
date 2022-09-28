<template>
  <div v-frag>
    <div
      v-if="!disabled && !idMode"
      class="input-group"
      :class="form && 'form-row'"
    >
      <button
        v-tippy
        title="Редактировать значение"
        class="btn btn-blue-nb nbr btn-value"
        type="button"
        tabindex="-1"
        @click="edit = true"
      >
        <i class="fa fa-pencil" />
      </button>
      <div
        v-tippy
        class="form-control form-control-area cursor-pointer"
        title="Редактировать значение"
        @click="edit = true"
      >
        {{ prevString || 'не заполнено' }}
      </div>
    </div>
    <div
      v-if="idMode"
      v-frag
    >
      <div class="input-group-btn">
        <button
          v-tippy
          title="Редактировать значение"
          class="btn btn-blue-nb nbr btn-value"
          type="button"
          tabindex="-1"
          @click="edit = true"
        >
          <i class="fa fa-pencil" />
        </button>
      </div>
      <div
        v-tippy
        class="form-control form-control-area cursor-pointer"
        title="Редактировать значение"
        @click="edit = true"
      >
        {{ prevString || 'не заполнено' }}
      </div>
    </div>
    <MountingPortal
      mount-to="#portal-place-modal"
      :name="`DynamicDirectoryField_${editTitle}`"
      append
    >
      <transition name="fade">
        <Modal
          v-if="edit"
          white-bg="true"
          max-width="710px"
          width="100%"
          margin-left-right="auto"
          :z-index="5001"
          @close="cancel"
        >
          <span
            v-if="editTitle"
            slot="header"
          >{{ editTitle }} — редактирование</span>
          <span
            v-else
            slot="header"
          >Редактирование значения</span>
          <div
            slot="body"
            class="value-body mkb"
          >
            <div class="alert-value">
              Выберите значение из списка
            </div>

            <div class="value-header">
              Новое значение:
            </div>
            <TypeAhead
              v-model="string"
              classes="vtypeahed"
              :src="`/api/dynamic-directory/suggests?value=:keyword&pk=${directory}`"
              :get-response="getResponse"
              :on-hit="onHit"
              placeholder="Поиск значения"
              no-result-text="Значение не найдено. Проверьте правильность ввода"
              maxlength="255"
              :delay-time="400"
              :min-chars="1"
              :render="items => items.map(i => i.string)"
              :limit="10"
              :highlighting="highlighting"
              :select-first="true"
              :name="name"
            />

            <div
              class="input-group nd"
              style="margin-top: 10px;"
            >
              <span class="input-group-addon form-group">Предыдущее значение</span>
              <div class="form-control form-control-area form-control-area-full form-control-forced-last">
                {{ prevString || 'пусто' }}
              </div>
            </div>

            <slot name="extended-edit" />

            <div class="row btn-row">
              <div class="col-xs-6 text-right">
                <button
                  v-tippy
                  class="btn btn-blue-nb"
                  type="button"
                  title="Оставить предыдущее значение"
                  @click="cancel"
                >
                  Отмена
                </button>
              </div>
              <div class="col-xs-6">
                <button
                  v-tippy
                  class="btn btn-blue-nb"
                  type="button"
                  title="Применить значение"
                  :disabled="blockSave"
                  @click="confirm"
                >
                  Ок
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
import Vue from 'vue';
import Component from 'vue-class-component';
import TypeAhead from 'vue2-typeahead';
import _ from 'lodash';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import Modal from '@/ui-cards/Modal.vue';

const getDetails = (original = null) => {
  const details = original || {};

  return details;
};

@Component({
  props: {
    editTitle: {
      type: String,
      required: false,
      default: null,
    },
    value: {
      type: [Number, String],
      required: false,
    },
    directory: {
      type: Number,
      required: true,
    },
    name: {
      type: String,
      required: false,
    },
    disabled: {
      type: Boolean,
      required: false,
      default: false,
    },
    idMode: {
      type: Boolean,
      required: false,
      default: false,
    },
    form: {
      type: Boolean,
      required: false,
      default: false,
    },
    hideIfEmpty: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  components: {
    TypeAhead,
    Modal,
    Treeselect,
  },
  data() {
    return {
      string: '',
      prevString: '',
      edit: false,
      details: getDetails(),
      prevDetails: getDetails(),
      blockSave: false,
    };
  },
  model: {
    event: 'modified',
  },
  watch: {
    value: {
      handler() {
        this.setDataFromValue();
      },
      immediate: true,
    },
    string() {
      this.blockSave = true;
    },
    edit() {
      this.blockSave = false;
    },
  },
})
export default class DynamicDirectoryField extends Vue {
  value: string | number;

  string: string;

  prevString: string;

  name: string | null;

  directory: number;

  disabled: boolean;

  idMode: boolean;

  form: boolean;

  receiveCopy: boolean;

  hideIfEmpty: boolean;

  edit: boolean;

  blockSave: boolean;

  editTitle: string | null;

  details: any;

  prevDetails: any;

  async setDataFromValue(forced = false) {
    let data;

    if (!this.idMode) {
      try {
        data = JSON.parse(String(this.value));
      } catch (e) {
        data = {};
        if (this.value && !String(this.value).includes('{')) {
          data.string = this.value;
        }
      }
    } else if (this.value) {
      const { record } = await this.$api('dynamic-directory/one-row', this, 'directory', { versionPk: this.value });
      data = record;
    } else {
      data = {};
    }

    if (_.has(data, 'string') || forced) {
      this.string = data.string || '';
    }

    this.details = getDetails(data);

    this.prevString = this.string;
    this.prevDetails = this.details;
  }

  onHit(itm, vue, index) {
    const item = vue.data[index];
    const {
      string,
    } = item;

    this.string = string;
    this.details = getDetails(item);
    setTimeout(() => {
      this.blockSave = false;
    }, 10);
  }

  // eslint-disable-next-line class-methods-use-this
  getResponse(resp) {
    return resp.data.data;
  }

  highlighting(item) {
    return item.toString().replace(this.string, `<b>${this.string}</b>`);
  }

  changeValue() {
    const v = JSON.stringify({
      string: this.string,
      ...this.details,
    });
    this.prevString = this.string;
    this.prevDetails = this.details;
    if (!this.idMode) {
      this.$emit('modified', v);
    } else {
      this.$emit('modified', this.details.versionPk);
    }
    this.blockSave = false;
  }

  cancel() {
    this.setDataFromValue(true);
    this.edit = false;
    this.blockSave = false;
  }

  async confirm() {
    this.changeValue();
    this.$root.$emit('msg', 'ok', 'Значение применено', 2000);
    this.edit = false;
    this.blockSave = false;
  }
}
</script>

<style scoped lang="scss">
::v-deep .dropdown-menu > li > a {
  white-space: normal !important;
}

.form-row {
  border-bottom: none;
}

::v-deep .panel-flt {
  align-self: stretch !important;
}

::v-deep {
  .vtypeahed {
    width: 100%;

    .form-control {
      width: 100% !important;
      border-radius: 4px !important;
      box-shadow: inset 0 1px 1px rgba(0, 0, 0, 8%) !important;
    }
  }
}

.form-control-forced-last {
  border-radius: 0 4px 4px 0 !important;

  &:not(:last-child) {
    border-radius: 0 !important;
  }

  box-shadow: inset 0 1px 1px rgba(0, 0, 0, 8%) !important;
  border: 1px solid #aab2bd;
  min-height: 34px;
  padding: 6px 12px;
}

.has-error {
  border-color: #f00 !important;
}

.value-body {
  padding: 10px;
}

.alert-value {
  margin: 0 0 15px 0;
  padding: 10px;
  background-color: rgba(0, 0, 0, 8%);
  border-radius: 4px;
}

.value-header {
  font-weight: bold;
}

.btn-row {
  margin-top: 20px;
  margin-bottom: 20px;

  .btn {
    min-width: 85px;
  }
}

.f-row {
  margin-top: 10px;
}

.nd + .input-group,
.nd + .nd,
.alert-top {
  margin-top: 10px;
}

.form-group {
  width: 185px;
  text-align: left;
}

.input-multiple {
  .treeselect-wide,
  .form-control {
    display: table-cell;
    width: 237px;
  }

  .treeselect-wide {
    padding: 0;
  }
}
</style>
