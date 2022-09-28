<template>
  <div style="max-width: 800px;">
    <div
      v-if="disabled"
      class="simple-value"
    >
      {{ localCode }} – {{ localTitle }}
    </div>
    <div
      v-else-if="loading"
      class="simple-value"
    >
      загрузка значений справочника
    </div>
    <div v-else>
      <SelectFieldTitled
        v-model="localCode"
        :variants="variantsToSelect"
        full-width
      />
      <small v-if="fieldTitle !== directoryTitle">НСИ справочник: {{ directoryTitle }}</small>
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import { mapGetters } from 'vuex';
import Component from 'vue-class-component';

import { LOAD_PERMANENT_DIRECTORY } from '@/store/action-types';
import directionsPoint from '@/api/directions-point';

@Component({
  props: {
    fieldTitle: {
      type: String,
      required: true,
    },
    value: {
      type: String,
      required: true,
    },
    oid: {
      type: Array,
      required: true,
    },
    disabled: {
      required: false,
      default: false,
      type: Boolean,
    },
    fieldPk: {
      type: String,
      required: false,
    },
    iss_pk: {
      type: [String, Number],
      required: false,
    },
    clientPk: {
      type: Number,
      required: false,
      default: -1,
    },
  },
  components: {
    SelectFieldTitled: () => import('@/fields/SelectFieldTitled.vue'),
  },
  data() {
    return {
      localCode: '-1',
      localTitle: 'Не выбрано',
      loading: false,
    };
  },
  computed: mapGetters(['permanentDirectories']),
  mounted() {
    this.validateData();
    this.loadLast();
  },
  watch: {
    disabled() {
      this.validateData();
    },
    localCode() {
      if (this.disabled) {
        return;
      }

      this.localTitle = this.variants[this.localCode] || '';
      this.emit();
    },
    localTitle() {
      this.emit();
    },
  },
  model: {
    event: 'modified',
  },
})
export default class PermanentDirectoryField extends Vue {
  value: any;

  permanentDirectories: any;

  oid: string;

  disabled: boolean | void;

  localCode: string;

  localTitle: string;

  loading: boolean;

  get variants() {
    const [oid] = this.oid;
    return this.permanentDirectories[oid]?.values || {};
  }

  get directoryTitle() {
    const [oid] = this.oid;
    return this.permanentDirectories[oid]?.title || '';
  }

  get variantsToSelect() {
    return Object.keys(this.variants).map(k => ({ pk: k, title: `${k} – ${this.variants[k]}` }));
  }

  async validateData() {
    const [oid] = this.oid;
    let value = this.value || '{}';
    try {
      value = JSON.parse(value);
    } catch (e) {
      value = {};
    }

    if (value.code) {
      this.localCode = String(value.code);
    }
    if (value.title) {
      this.localTitle = String(value.title);
    }

    if (this.disabled) {
      return;
    }
    this.loading = true;
    await this.$store.dispatch(LOAD_PERMANENT_DIRECTORY, { oid });
    this.loading = false;
    if (!this.variants[this.localCode]) {
      // eslint-disable-next-line prefer-destructuring
      this.localCode = Object.keys(this.variants)[0];
    } else {
      this.localTitle = this.variants[this.localCode] || '';
    }
  }

  async loadLast() {
    const { result } = await directionsPoint.lastFieldResult(this, ['iss_pk', 'clientPk', 'fieldPk']);
    try {
      const jval = JSON.parse(result.value);
      if (jval.code && jval.title) {
        this.localCode = String(jval.code);
        this.localTitle = String(jval.title);
      }
    } catch (e) {
      // eslint-disable-next-line no-console
      console.log(e);
    }
  }

  emit() {
    this.$emit('modified', JSON.stringify({
      code: this.localCode,
      title: this.localTitle,
    }));
  }
}
</script>

<style scoped lang="scss">
.simple-value {
  padding: 5px;
}
</style>
