<template>
  <div v-frag>
    <div class="div-address" v-if="disabled">
      {{ address }}
    </div>
    <TypeAhead
      :classes="form ? 'field-form' : ''"
      src="/api/autocomplete?value=:keyword&type=fias-extended"
      :getResponse="getResponse"
      :onHit="onHit"
      placeholder="Адрес по ФИАС"
      NoResultText="Адрес не найден в ФИАС. Проверьте правильность ввода"
      v-model="address"
      maxlength="255"
      :delayTime="400"
      :minChars="4"
      :render="items => items.map(i => i.unrestricted_value)"
      :limit="10"
      :highlighting="highlighting"
      :selectFirst="true"
      :name="name"
      v-else
    />
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import TypeAhead from 'vue2-typeahead';
import _ from 'lodash';
import { debounce } from 'lodash/function';

import directionsPoint from '@/api/directions-point';

@Component({
  props: {
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
  },
  data() {
    return {
      address: '',
      fias: null,
      loadedData: false,
      clearFiasTimer: null,
    };
  },
  model: {
    event: 'modified',
  },
  watch: {
    value: {
      handler() {
        let data;
        try {
          data = JSON.parse(this.value);
        } catch (e) {
          data = {};
          if (this.value && !this.value.includes('{')) {
            data.address = this.value;
          }
        }

        if (_.has(data, 'address')) {
          this.address = data.address;
        }

        if (_.has(data, 'fias')) {
          this.fias = data.fias;
        } else {
          this.fias = null;
        }

        if (!this.loadedData) {
          setTimeout(() => this.loadData(), 15);
        }
      },
      immediate: true,
    },
    address() {
      this.clearFiasTimer = setTimeout(() => {
        this.fias = null;
      }, 50);
      this.debouncedChangeValue();
    },
    fias() {
      clearTimeout(this.clearFiasTimer);
      this.debouncedChangeValue();
    },
  },
})
export default class AddressFiasField extends Vue {
  value: string;

  address: string;

  name: string | null;

  fias: string | null;

  disabled: boolean;

  form: boolean;

  loadedData: boolean;

  clientPk: number | null;

  clearFiasTimer: any;

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
    this.$emit('modified', v);
  }

  debouncedChangeValue = debounce(function () {
    this.changeValue();
  }, 100);

  async loadData() {
    this.loadedData = true;
    if (!this.address || !this.address.startsWith('%')) {
      return;
    }

    const { result } = await directionsPoint.lastFieldResult(this, 'clientPk', { fieldPk: this.address });

    try {
      const v = JSON.parse(result.value);
      this.address = v.address;
      this.fias = v.fias;
    } catch (e) {
      console.error(e);
      this.address = '';
      this.fias = null;
    }
  }
}
</script>

<style scoped lang="scss">
:not(.field-form) ::v-deep .typeahead-dropdown-container {
  top: -28px;
}

.div-address {
  padding: 3px;
}
</style>
