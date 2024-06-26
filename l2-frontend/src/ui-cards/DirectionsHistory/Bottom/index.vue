<template>
  <div>
    <div style="padding-left: 5px;color: #fff">
      <span v-show="checked.length > 0">Отмечено: {{ checked.length }}</span>
    </div>
    <div class="bottom-inner">
      <div
        v-show="checked.length > 0 &&
          active_type !== 5"
        class="dropup"
        style="display: inline-block;max-width: 350px;width: 100%"
      >
        <button
          class="btn btn-blue-nb btn-ell dropdown-toggle"
          type="button"
          data-toggle="dropdown"
          style="text-align: right!important;border-radius: 0;width: 100%"
        >
          Действие с отмеченными <span class="caret" />
        </button>
        <ul class="dropdown-menu">
          <li
            v-for="f in formsFiltered"
            :key="f.url"
          >
            <a
              :href="f.url"
              target="_blank"
            >{{ f.title }}</a>
          </li>
          <li
            v-for="value in menuItemsFiltered"
            :key="value.title"
          >
            <a
              v-if="(!value.onlyNotForIssledovaniye || !iss_pk)
                && (!value.onlyForTypes || value.onlyForTypes.includes(active_type))
                && (!value.requiredGroup || user_groups.includes(value.requiredGroup))"
              href="#"
              @click.prevent="() => callAsThis(value.handler)"
            >
              {{ value.title }}
            </a>
          </li>
        </ul>
      </div>
    </div>
    <DirectionsChangeParent
      v-if="isOpenChangeParent"
      :card_pk="card_pk"
      :directions_checked="directions_checked"
      :kk="kk"
    />
  </div>
</template>

<script lang="ts">
import { valuesToString } from '@/utils';

import menuMixin from './mixins/menu';
import { forDirs } from '../../../forms';
import DirectionsChangeParent from '../../../modals/DirectionsChangeParent.vue';

export default {
  components: { DirectionsChangeParent },
  mixins: [menuMixin],
  props: {
    checked: {
      type: Array,
      required: true,
    },
    directions: {
      type: Array,
      required: true,
    },
    iss_pk: {
      required: true,
    },
    card_pk: {
      required: true,
    },
    active_type: {
      required: true,
    },
    kk: {
      type: String,
      default: '',
    },
  },
  data() {
    return {
      isOpenChangeParent: false,
      disabled_forms: [],
    };
  },
  computed: {
    forms() {
      return forDirs.map((f) => ({
        ...f,
        url: valuesToString(f.url, {
          card: this.card_pk,
          dir: JSON.stringify(this.checked),
        }),
      })).filter(f => (!this.disabled_forms?.includes(f.type)));
    },
    formsFiltered() {
      return this.forms.filter(f => this.card_pk !== -1 && (!f.need_dirs || this.checked.length > 0));
    },
    directions_checked() {
      const r = [];
      for (const d of this.directions) {
        if (this.checked.includes(d.pk)) {
          r.push(d);
        }
      }
      return r;
    },
    user_groups() {
      return this.$store.getters.user_data.groups || [];
    },
    modules() {
      return {
        l2_send_patients_email_results: this.$store.getters.modules.l2_send_patients_email_results,
        l2_docx_aggregate_laboratory_results: this.$store.getters.modules.l2_docx_aggregate_laboratory_results,
        l2_need_order_redirection: this.$store.getters.modules.l2_need_order_redirection,
        l2_show_barcode_button_in_direction_history: this.$store.getters.modules.show_barcode_button_in_direction_history,
      };
    },
    menuItemsFiltered() {
      return this.menuItems.filter(item => !item.requiredModule || this.modules[item.requiredModule]);
    },
  },
  mounted() {
    this.$root.$on('hide_pe', this.change_parent_hide);
    this.get_disabled_forms();
  },
  methods: {
    callAsThis(handler) {
      handler.call(this);
    },
    change_parent_hide() {
      this.isOpenChangeParent = false;
    },
    async get_disabled_forms() {
      const resultData = await this.$api('disabled-forms');
      this.disabled_forms = resultData.rows;
    },
    in_checked(pk) {
      return this.checked.indexOf(pk) !== -1;
    },
  },
};
</script>

<style scoped lang="scss">
  .bottom-inner {
    display: flex;
    flex-wrap: wrap;
    justify-content: stretch;
    align-content: center;
    align-items: stretch;
    overflow-y: auto;
  }

  .bottom-inner {
    position: absolute;
    color: #fff;
    height: 34px;
    right: 0;
    left: 155px;
    top: 0;
    justify-content: flex-end;
    align-content: center;
    align-items: center;
    overflow: visible;
  }
</style>
