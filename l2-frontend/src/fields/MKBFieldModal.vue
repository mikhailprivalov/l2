<template>
  <div v-frag>
    <div class="input-group" :class="form && 'form-row'" v-if="!disabled">
      <button
        title="МКБ-10"
        class="btn btn-blue-nb nbr btn-address"
        type="button"
        v-tippy
        tabindex="-1"
        @click="edit = true"
      >
        <i class="fa fa-pencil"></i>
      </button>
            <div class="form-control form-control-area cursor-pointer" title="Редактировать адрес" v-tippy @click="edit = true">
        {{ '' || 'не заполнено' }}
      </div>
    </div>
    <mkb10-search v-if="edit"/>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import TypeAhead from 'vue2-typeahead';
import _ from 'lodash';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import directionsPoint from '@/api/directions-point';
import Mkb10Search from '@/modals/Mkb10Search.vue';

const getDetails = (original = null) => {
  const details = original || {};

  return {
    mkb10_code: details.mkb10_code || '',
    mkb10_title: details.mkb10_title || '',
    nsi_code: details.nsi_code || '',
  };
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

  },
  components: {
    Mkb10Search,
    TypeAhead,
    Treeselect,
  },
  data() {
    return {
      currentMkb: '',
      prevMkb: '',
      loadedData: false,
      edit: false,
      details: getDetails(),
      prevDetails: getDetails(),
    };
  },
  model: {
    event: 'modified',
  },
  mounted() {
    this.$root.$on('hide_mkb_modal', () => this.hide_mkb());
  },
})

export default class MKBFieldModal extends Vue {
  value: string;

  name: string | null;

  disabled: boolean;

  form: boolean;

  loadedData: boolean;

  edit: boolean;

  strict: boolean;

  editTitle: string | null;

  details: any;

  prevDetails: any;

  // eslint-disable-next-line class-methods-use-this

  hide_mkb() {
    this.edit = false;
  }

  cancel() {
    this.edit = false;
  }

  async confirm() {
    this.$root.$emit('msg', 'ok', 'Адрес применён', 2000);
    this.edit = false;
  }
}
</script>

<style scoped lang="scss">

.form-row {
  border-bottom: none;
}

</style>
