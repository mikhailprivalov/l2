<template>
  <div>
    <div style="padding-left: 5px;color: #fff">
      <span v-show="checked.length > 0">Отмечено: {{checked.length}}</span>
    </div>
    <div class="bottom-inner">
      <div class="dropup" style="display: inline-block;max-width: 350px;width: 100%" v-show="checked.length > 0">
        <button class="btn btn-blue-nb btn-ell dropdown-toggle" type="button" data-toggle="dropdown"
                style="text-align: right!important;border-radius: 0;width: 100%">
          Действие с отмеченными <span class="caret"></span>
        </button>
        <ul class="dropdown-menu">
          <li v-for="f in formsFiltered" :key="f.url">
            <a :href="f.url" target="_blank">{{f.title}}</a>
          </li>
          <li v-for="value in menuItems" :key="value.title">
            <a href="#"
               v-if="(!value.onlyNotForIssledovaniye || !iss_pk)
                  && (!value.onlyForTypes || value.onlyForTypes.includes(active_type))
                  && (!value.requiredGroup || user_groups.includes(value.requiredGroup))"
               @click.prevent="() => callAsThis(value.handler)">
              {{value.title}}
            </a>
          </li>
        </ul>
      </div>
    </div>
    <directions-change-parent
      v-if="isOpenChangeParent"
      :card_pk="card_pk"
      :directions_checked="directions_checked"
      :kk="kk"
    />
  </div>
</template>

<script>
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
    };
  },
  mounted() {
    this.$root.$on('hide_pe', this.change_parent_hide);
  },
  methods: {
    callAsThis(handler) {
      handler.call(this);
    },
    change_parent_hide() {
      this.isOpenChangeParent = false;
    },
  },
  computed: {
    forms() {
      return forDirs.map((f) => ({
        ...f,
        url: f.url.kwf({
          card: this.card_pk,
          dir: JSON.stringify(this.checked),
        }),
      }));
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
