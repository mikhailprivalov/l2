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
        {{ prevAddress || 'не заполнено' }}
      </div>
    </div>
    <div class="input-group" :class="[form && 'form-row', areaFull && 'input-group-flex']" v-else-if="!hideIfEmpty || address">
      <slot name="input-group-disabled-prepend"></slot>
      <div class="form-control form-control-area" :class="areaFull && 'form-control-area-full'">
        {{ address }}
      </div>
      <slot name="input-group-disabled-append"></slot>
    </div>
    <MountingPortal mountTo="#portal-place-modal" :name="`AddressFiasField_${editTitle}_${clientPk}`" append>
      <transition name="fade">
        <Modal @close="cancel" white-bg="true" max-width="710px" width="100%" marginLeftRight="auto" :zIndex="5001" v-if="edit">
          <span slot="header" v-if="editTitle">{{ editTitle }} — редактирование</span>
          <span slot="header" v-else>Редактирование адреса</span>
          <div slot="body" class="address-body mkb">
            <div class="alert-address">
              Выберите из списка, если адрес найден
            </div>

            <div class="address-header">Новый адрес:</div>
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
              :minChars="1"
              :render="items => items.map(i => i.unrestricted_value)"
              :limit="10"
              :highlighting="highlighting"
              :selectFirst="true"
              :name="name"
              :readonly="details.custom"
            />

            <div v-if="!details.custom && !fias && address" class="alert alert-warning alert-top">
              Выберите адрес из списка или введите вручную в форму ниже, если адрес не найден
            </div>

            <div class="input-group nd f-row" v-if="!details.custom">
              <span class="input-group-addon">Номер объекта в ФИАС</span>
              <input
                type="text"
                class="form-control form-control-forced-last form-group"
                :class="!fias && 'has-error'"
                :value="fias || 'пусто, адрес не выбран из списка'"
                readonly
              />
            </div>

            <label class="nd"><input type="checkbox" v-model="details.custom" /> Ввести адрес вручную</label>

            <div class="input-group nd">
              <span class="input-group-addon form-group">Область</span>
              <input
                type="text"
                class="form-control form-control-forced-last"
                :class="!details.custom && !details.region && 'has-error'"
                v-model="details.region"
                :readonly="!details.custom"
              />
            </div>

            <div class="input-group nd">
              <span class="input-group-addon form-group">Район</span>
              <input
                type="text"
                class="form-control form-control-forced-last"
                v-model="details.area"
                :readonly="!details.custom"
              />
            </div>

            <div class="input-group nd">
              <span class="input-group-addon form-group">Населённый пункт</span>
              <input
                type="text"
                class="form-control form-control-forced-last"
                :class="!details.custom && !details.city && 'has-error'"
                v-model="details.city"
                :readonly="!details.custom"
              />
            </div>

            <div class="input-group nd">
              <span class="input-group-addon form-group">Улица</span>
              <input
                type="text"
                class="form-control form-control-forced-last"
                v-model="details.street"
                :readonly="!details.custom"
              />
            </div>

            <div class="input-group nd">
              <span class="input-group-addon form-group">Дом</span>
              <input
                type="text"
                class="form-control form-control-forced-last"
                :class="!details.custom && !details.house && 'has-error'"
                v-model="details.house"
                :readonly="!details.custom"
              />
            </div>

            <div class="input-group nd">
              <span class="input-group-addon form-group">Квартира</span>
              <input
                type="text"
                class="form-control form-control-forced-last"
                v-model="details.flat"
                :readonly="!details.custom"
              />
            </div>

            <div class="input-group nd">
              <span class="input-group-addon form-group">Почтовый индекс</span>
              <input
                type="text"
                class="form-control form-control-forced-last"
                v-model="details.postal_code"
                :readonly="!details.custom"
              />
            </div>

            <div class="input-group nd">
              <span class="input-group-addon form-group">Предыдущий адрес</span>
              <div class="form-control form-control-area form-control-area-full form-control-forced-last">
                {{ prevAddress || 'пусто' }}
              </div>
            </div>

            <slot name="extended-edit"></slot>

            <div class="row btn-row">
              <div class="col-xs-6 text-right">
                <button @click="cancel" class="btn btn-blue-nb" type="button" title="Оставить предыдущий адрес" v-tippy>
                  Отмена
                </button>
              </div>
              <div class="col-xs-6">
                <button @click="confirm" class="btn btn-blue-nb" type="button" title="Применить адрес" v-tippy>
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

import directionsPoint from '@/api/directions-point';
import Modal from '@/ui-cards/Modal.vue';

const getDetails = (original = null) => {
  const details = original || {};
  return {
    region: details.region_with_type || details.region || '',
    area: details.area_with_type || details.area || '',
    city: details.city_with_type || details.city || '',
    street: details.street_with_type || details.street || '',
    house: (details.house && details.house_type ? `${details.house_type} ` : '') + (details.house || ''),
    flat: (details.flat && details.flat_type ? `${details.flat_type} ` : '') + (details.flat || ''),
    postal_code: details.postal_code || '',
    custom: details.custom || false,
  };
};

const validateDetails = details => Boolean(details?.region && details.city && details.house);

const nRe = /^\d+$/;

function isNumeric(str) {
  return nRe.test(str);
}

const prependStrIfNumeric = (v, s) => {
  if (isNumeric(v)) {
    return `${s} ${v}`;
  }

  return v;
};

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
    areaFull: {
      type: Boolean,
      required: false,
      default: false,
    },
    receiveCopy: {
      type: Boolean,
      required: false,
      default: false,
    },
    hideIfEmpty: {
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
      prevFias: null,
      loadedData: false,
      clearFiasTimer: null,
      edit: false,
      details: getDetails(),
      prevDetails: getDetails(),
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
    details: {
      deep: true,
      handler() {
        if (!this.details.custom) {
          return;
        }

        const house = prependStrIfNumeric(this.details.house, 'д');
        const flat = prependStrIfNumeric(this.details.flat, 'кв');

        const parts = [
          this.details.postal_code,
          this.details.region,
          this.details.area,
          this.details.city,
          this.details.street,
          house,
          flat,
        ];

        this.address = parts.filter(Boolean).join(', ');
      },
    },
  },
  mounted() {
    this.$root.$on('address-copy', addressJSON => {
      let data;
      try {
        data = JSON.parse(addressJSON);
      } catch (e) {
        data = {};
        if (addressJSON && !addressJSON.includes('{')) {
          data.address = addressJSON;
        }
      }

      this.address = data.address || '';
      this.fias = data.fias || null;
      this.details = getDetails(data.details);
    });
  },
})
export default class AddressFiasField extends Vue {
  value: string;

  address: string;

  prevAddress: string;

  name: string | null;

  fias: string | null;

  prevFias: string | null;

  disabled: boolean;

  form: boolean;

  loadedData: boolean;

  areaFull: boolean;

  receiveCopy: boolean;

  hideIfEmpty: boolean;

  edit: boolean;

  clientPk: number | null;

  clearFiasTimer: any;

  editTitle: string | null;

  details: any;

  prevDetails: any;

  get isValidDetails() {
    return validateDetails(this.details);
  }

  get isValid() {
    if (this.details.custom) {
      return this.isValidDetails;
    }

    return Boolean(this.fias) && this.isValidDetails;
  }

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
    }

    if (_.has(data, 'fias') || forced) {
      this.fias = data.fias || null;
    } else {
      this.fias = null;
    }

    this.details = getDetails(data.details);

    this.prevAddress = this.address;
    this.prevFias = this.fias;
    this.prevDetails = this.details;

    if (!this.loadedData) {
      setTimeout(() => this.loadData(), 15);
    }
  }

  onHit(itm, vue, index) {
    const item = vue.data[index];
    const {
      data: { fias_id, fias_level, ...details },
      unrestricted_value,
    } = item;

    this.address = unrestricted_value;
    this.details = getDetails(details);
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
    this.details.house = prependStrIfNumeric(this.details.house, 'д');
    this.details.flat = prependStrIfNumeric(this.details.flat, 'кв');

    const v = JSON.stringify({
      address: this.address,
      fias: this.fias,
      details: this.details,
    });
    this.prevAddress = this.address;
    this.prevFias = this.fias;
    this.prevDetails = this.details;
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
      if (validateDetails(v.details)) {
        this.details = getDetails(v.details);
        this.address = v.address;
        this.fias = v.fias;
      } else {
        this.address = '';
      }
    } catch (e) {
      console.error(e);
      this.address = '';
      this.fias = null;
      this.details = getDetails();
    }
    this.prevAddress = this.address;
    this.prevFias = this.fias;
    this.prevDetails = this.details;
    this.changeValue();
  }

  cancel() {
    this.setDataFromValue(true);
    this.edit = false;
  }

  async confirm() {
    this.changeValue();
    this.$root.$emit('msg', 'ok', 'Адрес применён', 2000);
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

.form-control-forced-last {
  width: 100% !important;
  border-radius: 0 4px 4px 0 !important;
  box-shadow: inset 0 1px 1px rgba(0, 0, 0, 8%) !important;
  border: 1px solid #aab2bd;
  min-height: 34px;
  padding: 6px 12px;

  &.has-error {
    border-color: #f00;
  }
}

.address-body {
  padding: 10px;
}

.alert-address {
  margin: 0 0 15px 0;
  padding: 10px;
  background-color: rgba(0, 0, 0, 8%);
  border-radius: 4px;
}

.address-header {
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
</style>
