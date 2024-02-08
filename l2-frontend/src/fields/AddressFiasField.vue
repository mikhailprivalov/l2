<template>
  <div v-frag>
    <div
      v-if="!disabled"
      class="input-group"
      :class="form && 'form-row'"
    >
      <button
        v-tippy
        title="Редактировать адрес"
        class="btn btn-blue-nb nbr btn-address"
        type="button"
        tabindex="-1"
        @click="edit = true"
      >
        <i class="fa fa-pencil" />
      </button>
      <div
        v-tippy
        class="form-control form-control-area cursor-pointer"
        title="Редактировать адрес"
        @click="edit = true"
      >
        {{ prevAddress || 'не заполнено' }}
      </div>
      <slot name="input-group-append" />
    </div>
    <div
      v-else-if="!hideIfEmpty || address"
      class="input-group"
      :class="[form && 'form-row', areaFull && 'input-group-flex']"
    >
      <slot name="input-group-disabled-prepend" />
      <div
        class="form-control form-control-area"
        :class="areaFull && 'form-control-area-full'"
      >
        {{ address }}
      </div>
      <slot name="input-group-disabled-append" />
    </div>
    <MountingPortal
      mount-to="#portal-place-modal"
      :name="`AddressFiasField_${editTitle}_${clientPk}`"
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
          >Редактирование адреса</span>
          <div
            slot="body"
            class="address-body mkb"
          >
            <div class="alert-address">
              Выберите из списка, если адрес найден
            </div>

            <div class="address-header">
              Новый адрес:
            </div>
            <TypeAhead
              v-model="address"
              classes="vtypeahed"
              src="/api/autocomplete?value=:keyword&type=fias-extended"
              :get-response="getResponse"
              :on-hit="onHit"
              placeholder="Адрес по ФИАС"
              no-result-text="Адрес не найден в ФИАС. Проверьте правильность ввода"
              maxlength="255"
              :delay-time="400"
              :min-chars="1"
              :render="items => items.map(i => i.unrestricted_value)"
              :limit="10"
              :highlighting="highlighting"
              :select-first="true"
              :name="name"
              :readonly="details.custom"
            />

            <div
              v-if="!details.custom && !fias && address"
              class="alert alert-warning alert-top"
            >
              Выберите адрес из списка или введите вручную в форму ниже, если адрес не найден
            </div>

            <div
              v-if="!details.custom"
              class="input-group nd f-row"
            >
              <span class="input-group-addon">Номер объекта в ФИАС</span>
              <input
                type="text"
                class="form-control form-control-forced-last form-group w-100"
                :class="!fias && 'has-error'"
                :value="fias || 'пусто, адрес не выбран из списка'"
                readonly
              >
            </div>

            <div
              v-if="details.custom"
              class="alert-address alert-top"
            >
              Обязательно выберите тип объекта. <br>
              Например для "ул. Ленина" выбрать <strong>ул.</strong> и в значение <strong>Ленина</strong>
            </div>

            <label class="nd"><input
              v-model="details.custom"
              type="checkbox"
            > Ввести адрес вручную</label>

            <div class="input-group treeselect-input-group input-multiple nd">
              <span class="input-group-addon form-group">Область</span>
              <input
                v-if="!details.custom"
                v-model="details.region_type"
                type="text"
                class="form-control form-control-forced-last"
                readonly
              >
              <treeselect
                v-else
                v-model="details.region_type"
                class="treeselect-wide"
                :class="details.custom && details.region && !details.region_type && 'has-error'"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="REGION_TYPES"
                placeholder="Тип области не выбран"
                :append-to-body="true"
                :clearable="true"
                :z-index="6000"
              />
              <input
                v-model="details.region"
                type="text"
                class="form-control form-control-forced-last"
                :class="details.custom && !details.region && 'has-error'"
                :readonly="!details.custom"
                :placeholder="details.custom && 'область'"
                autocomplete="new-password"
              >
            </div>

            <div class="input-group treeselect-input-group input-multiple nd">
              <span class="input-group-addon form-group">Район</span>
              <input
                v-if="!details.custom"
                v-model="details.area_type"
                type="text"
                class="form-control form-control-forced-last"
                readonly
              >
              <treeselect
                v-else
                v-model="details.area_type"
                class="treeselect-wide"
                :class="details.custom && details.area && !details.area_type && 'has-error'"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="AREA_TYPES"
                placeholder="Тип района не выбран"
                :append-to-body="true"
                :clearable="true"
                :z-index="6000"
              />
              <input
                v-model="details.area"
                type="text"
                class="form-control form-control-forced-last"
                :readonly="!details.custom"
                :placeholder="details.custom && 'район'"
                autocomplete="new-password"
              >
            </div>

            <div class="input-group treeselect-input-group input-multiple nd">
              <span class="input-group-addon form-group">Город</span>
              <input
                v-if="!details.custom"
                v-model="details.city_type"
                type="text"
                class="form-control form-control-forced-last"
                readonly
              >
              <treeselect
                v-else
                v-model="details.city_type"
                class="treeselect-wide"
                :class="details.custom && details.city && !details.city_type && 'has-error'"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="CITY_TYPES"
                placeholder="Тип города не выбран"
                :append-to-body="true"
                :clearable="true"
                :z-index="6000"
              />
              <input
                v-model="details.city"
                type="text"
                class="form-control form-control-forced-last"
                :readonly="!details.custom"
                :placeholder="details.custom && 'город'"
                autocomplete="new-password"
              >
            </div>

            <div class="input-group treeselect-input-group input-multiple nd">
              <span class="input-group-addon form-group">Населённый пункт</span>
              <input
                v-if="!details.custom"
                v-model="details.settlement_type"
                type="text"
                class="form-control form-control-forced-last"
                readonly
              >
              <treeselect
                v-else
                v-model="details.settlement_type"
                class="treeselect-wide"
                :class="details.custom && details.settlement && !details.settlement_type && 'has-error'"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="SETTLEMENT_TYPES"
                placeholder="Тип населённого пункта не выбран"
                :append-to-body="true"
                :clearable="true"
                :z-index="6000"
                autocomplete="new-password"
              />
              <input
                v-model="details.settlement"
                type="text"
                class="form-control form-control-forced-last"
                :readonly="!details.custom"
                :placeholder="details.custom && 'населённый пункт'"
              >
            </div>

            <div class="input-group treeselect-input-group input-multiple nd">
              <span class="input-group-addon form-group">Улица</span>
              <input
                v-if="!details.custom"
                v-model="details.street_type"
                type="text"
                class="form-control form-control-forced-last"
                readonly
              >
              <treeselect
                v-else
                v-model="details.street_type"
                class="treeselect-wide"
                :class="details.custom && details.street && !details.street_type && 'has-error'"
                :multiple="false"
                :disable-branch-nodes="true"
                :options="STREET_TYPES"
                placeholder="Тип улицы не выбран"
                :append-to-body="true"
                :clearable="true"
                :z-index="6000"
                autocomplete="new-password"
              />
              <input
                v-model="details.street"
                type="text"
                class="form-control form-control-forced-last"
                :readonly="!details.custom"
                :placeholder="details.custom && 'улица'"
              >
            </div>

            <div class="input-group input-multiple nd">
              <span class="input-group-addon form-group">Дом</span>
              <input
                v-model="details.house_type"
                type="text"
                class="form-control form-control-forced-last"
                :class="details.custom && details.house && !details.house_type && 'has-error'"
                :readonly="!details.custom"
                :placeholder="details.custom && 'Тип (напр д, с)'"
              >
              <input
                v-model="details.house"
                type="text"
                class="form-control form-control-forced-last"
                :readonly="!details.custom"
                :placeholder="details.custom && 'номер дома'"
                autocomplete="new-password"
              >
            </div>

            <div class="input-group input-multiple nd">
              <span class="input-group-addon form-group">Квартира</span>
              <input
                v-model="details.flat_type"
                type="text"
                class="form-control form-control-forced-last"
                :class="details.custom && details.flat && !details.flat_type && 'has-error'"
                :readonly="!details.custom"
                :placeholder="details.custom && 'Тип (напр кв, оф)'"
              >
              <input
                v-model="details.flat"
                type="text"
                class="form-control form-control-forced-last"
                :readonly="!details.custom"
                :placeholder="details.custom && 'значение'"
                autocomplete="new-password"
              >
            </div>

            <div class="input-group nd">
              <span class="input-group-addon form-group">Почтовый индекс</span>
              <input
                v-model="details.postal_code"
                type="text"
                class="form-control form-control-forced-last"
                :readonly="!details.custom"
                :maxlength="6"
                autocomplete="new-password"
              >
            </div>

            <div class="input-group nd">
              <span class="input-group-addon form-group">Предыдущий адрес</span>
              <div class="form-control form-control-area form-control-area-full form-control-forced-last">
                {{ prevAddress || 'пусто' }}
              </div>
            </div>

            <slot name="extended-edit" />

            <div class="row btn-row">
              <div class="col-xs-6 text-right">
                <button
                  v-tippy
                  class="btn btn-blue-nb"
                  type="button"
                  title="Оставить предыдущий адрес"
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
                  title="Применить адрес"
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

import {
  AREA_TYPES, CITY_TYPES, REGION_TYPES, SETTLEMENT_TYPES, STREET_TYPES,
} from '@/fias';
import directionsPoint from '@/api/directions-point';
import Modal from '@/ui-cards/Modal.vue';

const getDetails = (original = null) => {
  const details = original || {};

  return {
    region: details.region || '',
    region_type: details.region_type || '',
    subject_code: (details.region_kladr_id || '').slice(0, 2),
    area: details.area || '',
    area_type: details.area_type || '',
    city: details.city || '',
    city_type: details.city_type || '',
    settlement: details.settlement || '',
    settlement_type: details.settlement_type || '',
    street: details.street || '',
    street_type: details.street_type || '',
    house: details.house || '',
    house_type: details.house_type || '',
    flat: details.flat || '',
    flat_type: details.flat_type || '',
    postal_code: details.postal_code || '',
    geo_lat: details.geo_lat || '',
    geo_lon: details.geo_lon || '',
    custom: details.custom || false,
  };
};

const validateDetails = (details, strict) => Boolean(details?.region && (!strict || (details.city && details.house)));

const prependStr = (v, s) => {
  if (s) {
    return `${v || ''} ${s}`;
  }

  return v || '';
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
    strict: {
      type: Boolean,
      required: false,
      default: true,
    },
    clientPk: {
      type: Number,
      required: false,
    },
  },
  components: {
    TypeAhead,
    Modal,
    Treeselect,
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
      REGION_TYPES,
      AREA_TYPES,
      CITY_TYPES,
      SETTLEMENT_TYPES,
      STREET_TYPES,
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

        for (const k of Object.keys(this.details)) {
          if (this.details[k] === null || typeof this.details[k] === 'undefined') {
            this.details[k] = '';
          }
        }

        const region = prependStr(this.details.region, this.details.region_type);
        const area = prependStr(this.details.area, this.details.area_type);
        const city = prependStr(this.details.city_type, this.details.city);
        const street = prependStr(this.details.street_type, this.details.street);
        const settlement = prependStr(this.details.settlement_type, this.details.settlement);
        const house = prependStr(this.details.house_type, this.details.house);
        const flat = prependStr(this.details.flat_type, this.details.flat);

        const parts = [this.details.postal_code, region, area, city, settlement, street, house, flat];

        this.address = parts.filter(Boolean).join(', ');

        this.details.postal_code = this.details.postal_code.replace(/\D/g, '');
      },
    },
  },
  mounted() {
    this.$root.$on('address-copy', addressJSON => {
      if (!this.receiveCopy) {
        return;
      }
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

    this.$root.$on('address-copy-fast', addressJSON => {
      if (!this.receiveCopy) {
        return;
      }
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

      this.confirm();
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

  strict: boolean;

  clientPk: number | null;

  clearFiasTimer: any;

  editTitle: string | null;

  details: any;

  prevDetails: any;

  REGION_TYPES: typeof REGION_TYPES;

  AREA_TYPES: typeof AREA_TYPES;

  CITY_TYPES: typeof CITY_TYPES;

  SETTLEMENT_TYPES: typeof SETTLEMENT_TYPES;

  STREET_TYPES: typeof STREET_TYPES;

  get isValidDetails() {
    return validateDetails(this.details, this.strict);
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
      data: { fias_id: fias, ...details },
      unrestricted_value: address,
    } = item;

    this.address = address;
    this.details = getDetails(details);
    this.fias = fias;
    clearTimeout(this.clearFiasTimer);
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
      details: this.details,
    });
    this.prevAddress = this.address;
    this.prevFias = this.fias;
    this.prevDetails = this.details;
    this.$emit('modified', v);
  }

  async loadData() {
    this.loadedData = true;
    if (!this.address?.startsWith('%')) {
      return;
    }

    const { result } = await directionsPoint.lastFieldResult(this, 'clientPk', { fieldPk: this.address });

    try {
      const v = JSON.parse(result.value);
      if (validateDetails(v.details, this.strict)) {
        this.details = getDetails(v.details);
        this.address = v.address;
        this.fias = v.fias;
      } else {
        this.address = '';
      }
    } catch (e) {
      // eslint-disable-next-line no-console
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
