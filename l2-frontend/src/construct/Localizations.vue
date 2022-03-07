<template>
  <Modal
    ref="modal"
    show-footer="true"
    white-bg="true"
    max-width="680px"
    width="100%"
    margin-top
    margin-left-right="auto"
    @close="hide_modal"
  >
    <span slot="header">Настройка локализаций ({{ title }})</span>
    <div
      v-if="loaded"
      slot="body"
      style="min-height: 200px"
    >
      <div class="list-group">
        <a
          v-for="l in localizations"
          :key="l.pk"
          href="#"
          class="list-group-item list-group-item-light"
          :class="selected[l.pk] && 'active'"
          @click.prevent="toggleSelected(l.pk)"
        >
          <input
            type="checkbox"
            :checked="!!selected[l.pk]"
          >
          {{ l.title }}
        </a>
      </div>
    </div>
    <div
      v-else
      slot="body"
      style="line-height: 200px;text-align: center"
    >
      Загрузка данных...
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-8">
          <button
            type="button"
            :disabled="!hasChanges"
            class="btn btn-primary-nb"
            @click="save"
          >
            Сохранить
          </button>
        </div>
        <div class="col-xs-4">
          <button
            type="button"
            class="btn btn-primary-nb btn-blue-nb"
            @click="hide_modal"
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script lang="ts">
import Modal from '@/ui-cards/Modal.vue';
import * as actions from '@/store/action-types';

export default {
  components: { Modal },
  props: {
    research_pk: {
      type: Number,
      required: true,
    },
    title: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      loaded: false,
      localizations: [],
      selected: {},
      hasChanges: false,
    };
  },
  created() {
    this.load_data();
  },
  methods: {
    hide_modal() {
      this.$emit('hide');
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
    },
    async load_data() {
      await this.$store.dispatch(actions.INC_LOADING);
      this.loaded = false;
      const { localizations, selected } = await this.$api('researches/localization', { pk: this.research_pk });
      this.localizations = localizations;
      this.selected = localizations.reduce((a, { pk }) => ({ ...a, [pk]: selected.includes(pk) }), {});
      this.loaded = true;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    toggleSelected(pk) {
      this.selected[pk] = !this.selected[pk];
      this.hasChanges = true;
    },
    async save() {
      await this.$store.dispatch(actions.INC_LOADING);
      await this.$api('researches/localization/save', {
        pk: this.research_pk,
        selected: Object.keys(this.selected).filter(pk => this.selected[pk]),
      });
      this.hasChanges = false;
      await this.$store.dispatch(actions.DEC_LOADING);
      this.$root.$emit('msg', 'ok', `Локализации для исследования\n«‎${this.title}»‎\nсохранены`, 4000);
    },
  },
};
</script>

<style scoped lang="scss">
.modal-mask {
  align-items: stretch !important;
  justify-content: center !important;
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
  padding: 10px !important;
  height: calc(100% - 144px);
  min-height: 200px;
}

.list-group {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
}

.list-group-item-light {
  background-color: #f4f6f8;
  transition: all 0.2s ease-in-out;

  &.active {
    background: #049372 !important;
    border-color: #049372 !important;
  }

  input[type='checkbox'] {
    vertical-align: top;
  }
}
</style>
