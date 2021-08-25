<template>
  <div v-frag>
    <div class="input-group" :class="form && 'form-row'" v-if="!disabled">
      <button
        title="Редактировать адрес"
        class="btn btn-blue-nb nbr btn-address"
        type="button"
        v-tippy
        tabindex="-1"
        @click="edit = true"
      >
        <i class="fa fa-pencil"></i>
      </button>
      <div class="form-control form-control-area cursor-pointer" title="Редактировать адрес" v-tippy @click="edit = true">
        {{ prevAddress }}
      </div>
    </div>
    <div class="input-group" :class="form && 'form-row'" v-else>
      <div class="form-control form-control-area">
        {{ address }}
      </div>
    </div>
    <transition name="fade">
      <Modal @close="cancel" white-bg="true" max-width="710px" width="100%" marginLeftRight="auto" :zIndex="5001" v-if="edit">
        <span slot="header" v-if="editTitle">{{ editTitle }} — редактирование</span>
        <span slot="header" v-else>Редактирование адреса</span>
        <div slot="body" class="address-body mkb">
          <div class="alert-address">
            Выберите из списка, если адрес найден
          </div>
          <TypeAhead
            classes="vtypeahed"
            src="/api/autocomplete?value=:keyword&type=fias-extended"
            :getResponse="getResponse"
            :onHit="onHit"
            placeholder="Адрес по ФИАС"
            NoResultText="Адрес не найден в ФИАС. Проверьте правильность ввода"
            v-model="address"
            maxlength="255"
            :delayTime="400"
            :minChars="3"
            :render="items => items.map(i => i.unrestricted_value)"
            :limit="10"
            :highlighting="highlighting"
            :selectFirst="true"
            :name="name"
          />

          <div class="row btn-row">
            <div class="col-xs-6 text-right">
              <button @click="cancel" class="btn btn-blue-nb" type="button">
                Отмена
              </button>
            </div>
            <div class="col-xs-6">
              <button @click="confirm" class="btn btn-blue-nb" type="button">
                Подтвердить
              </button>
            </div>
          </div>
        </div>
      </Modal>
    </transition>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import TypeAhead from 'vue2-typeahead';
import _ from 'lodash';

import directionsPoint from '@/api/directions-point';
import Modal from '@/ui-cards/Modal.vue';

@Component({
  props: {
    editTitle: {
      type: String,
      required: false,
      default: null,
    },
    value: {
      type: String,
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
    form: {
      type: Boolean,
      required: false,
      default: false,
    },
    clientPk: {
      type: Number,
      required: false,
    },
  },
  components: {
    TypeAhead,
    Modal,
  },
  data() {
    return {
      address: '',
      prevAddress: '',
      fias: null,
      loadedData: false,
      clearFiasTimer: null,
      edit: false,
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
    address() {
      this.clearFiasTimer = setTimeout(() => {
        this.fias = null;
      }, 50);
    },
    fias() {
      clearTimeout(this.clearFiasTimer);
    },
  },
})
export default class AddressFiasField extends Vue {
  value: string;

  address: string;

  prevAddress: string;

  name: string | null;

  fias: string | null;

  disabled: boolean;

  form: boolean;

  loadedData: boolean;

  edit: boolean;

  clientPk: number | null;

  clearFiasTimer: any;

  editTitle: string | null;

  get addressValue() {
    if (!this.edit) {
      return this.address;
    }

    return this.prevAddress;
  }

  setDataFromValue(forced = false) {
    let data;
    try {
      data = JSON.parse(this.value);
    } catch (e) {
      data = {};
      if (this.value && !this.value.includes('{')) {
        data.address = this.value;
      }
    }

    if (_.has(data, 'address') || forced) {
      this.address = data.address || '';
      this.prevAddress = data.address || '';
    }

    if (_.has(data, 'fias') || forced) {
      this.fias = data.fias || null;
    } else {
      this.fias = null;
    }

    if (!this.loadedData) {
      setTimeout(() => this.loadData(), 15);
    }
  }

  onHit(itm, vue, index) {
    const item = vue.data[index];
    const {
      data: { fias_id, fias_level },
      unrestricted_value,
    } = item;

    this.address = unrestricted_value;
    if (Number(fias_level) > 7) {
      this.fias = fias_id;
    } else {
      this.fias = null;
    }
  }

  // eslint-disable-next-line class-methods-use-this
  getResponse(resp) {
    return resp.data.data;
  }

  highlighting(item) {
    return item.toString().replace(this.address, `<b>${this.address}</b>`);
  }

  changeValue() {
    const v = JSON.stringify({
      address: this.address,
      fias: this.fias,
    });
    this.prevAddress = this.address;
    this.$emit('modified', v);
  }

  async loadData() {
    this.loadedData = true;
    if (!this.address || !this.address.startsWith('%')) {
      return;
    }

    const { result } = await directionsPoint.lastFieldResult(this, 'clientPk', { fieldPk: this.address });

    try {
      const v = JSON.parse(result.value);
      this.address = v.address;
      this.prevAddress = v.address;
      this.fias = v.fias;
    } catch (e) {
      console.error(e);
      this.address = '';
      this.fias = null;
    }
  }

  cancel() {
    this.setDataFromValue(true);
    this.edit = false;
  }

  confirm() {
    this.changeValue();
    this.$root.$emit('msg', 'ok', 'Адрес применён');
    this.edit = false;
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

.address-body {
  padding: 10px;
}

.alert-address {
  margin: 5px 0 15px 0;
  padding: 10px;
  font-weight: bold;
  background-color: rgba(0, 0, 0, 8%);
  border-radius: 4px;
}

.btn-row {
  margin-top: 25px;
}
</style>
