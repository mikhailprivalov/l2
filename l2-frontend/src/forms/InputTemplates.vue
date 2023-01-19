<template>
  <div v-frag>
    <button
      v-tippy
      class="btn btn-default btn-field"
      title="Шаблоны поля ввода"
      tabindex="-1"
      @click="show"
    >
      <i class="fa fa-list-alt" />
    </button>

    <MountingPortal
      mount-to="#portal-place-modal"
      :name="`InputTemplates_${field.pk}`"
      append
    >
      <transition name="fade">
        <Modal
          v-if="open"
          show-footer="true"
          white-bg="true"
          max-width="710px"
          width="100%"
          margin-left-right="auto"
          @close="open = false"
        >
          <span slot="header">Ваши шаблоны поля {{ `${group.title} ${field.title}`.trim() }}</span>
          <div
            slot="body"
            class="popup-body"
          >
            <div
              v-if="loading"
              class="preloader"
            >
              <i class="fa fa-spinner" /> загрузка
            </div>
            <div v-else>
              <div class="templates-list">
                <div
                  v-if="templates.length === 0"
                  class="text-center"
                >
                  нет шаблонов для этого поля
                </div>
                <template v-else>
                  <div
                    v-for="t in templates"
                    :key="t.pk"
                    class="input-group input-group-flex t-group"
                  >
                    <div class="input-group-btn">
                      <button
                        v-tippy
                        class="btn btn-blue-nb2"
                        title="Удалить шаблон"
                        @click="deleteTemplate(t.pk)"
                      >
                        <i class="fas fa-times" />
                      </button>
                    </div>
                    <textarea
                      v-if="field.lines > 1"
                      :rows="field.lines"
                      class="form-control"
                      :value="t.value"
                      readonly
                    />
                    <input
                      v-else
                      class="form-control"
                      :value="t.value"
                      readonly
                    >
                    <div class="input-group-btn">
                      <button
                        v-tippy
                        class="btn btn-blue-nb2"
                        title="Добавить значение"
                        @click="useTemplateAppend(t.value)"
                      >
                        <i class="fas fa-plus" />
                      </button>
                      <button
                        v-tippy
                        class="btn btn-blue-nb2"
                        title="Заменить значение"
                        @click="useTemplate(t.value)"
                      >
                        <i class="fas fa-check" />
                      </button>
                    </div>
                  </div>
                </template>
              </div>
              <div class="input-group input-group-flex add-group">
                <textarea
                  v-if="field.lines > 1"
                  v-model="value"
                  :rows="field.lines"
                  class="form-control"
                />
                <input
                  v-else
                  v-model="value"
                  class="form-control"
                >
                <div class="input-group-btn">
                  <button
                    class="btn btn-blue-nb2"
                    :disabled="value.trim().length === 0"
                    @click="add"
                  >
                    Добавить
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-6">
                <button
                  class="btn btn-blue-nb"
                  type="button"
                  @click="open = false"
                >
                  Закрыть
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
import Modal from '@/ui-cards/Modal.vue';
import * as actions from '@/store/action-types';

export default {
  name: 'InputTemplates',
  components: {
    Modal,
  },
  props: {
    field: Object,
    group: Object,
  },
  data() {
    return {
      loading: false,
      open: false,
      templates: [],
      value: '',
    };
  },
  mounted() {
    this.$root.$on(`templates-open:${this.field.pk}`, () => this.show());
  },
  methods: {
    async show() {
      this.value = '';
      this.open = true;
      this.loading = true;
      await this.$store.dispatch(actions.INC_LOADING);
      const { rows } = await this.$api('/input-templates/get', { pk: this.field.pk });
      this.templates = rows;
      await this.$store.dispatch(actions.DEC_LOADING);
      this.loading = false;
    },
    async add() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, pk } = await this.$api('/input-templates/add', { pk: this.field.pk, value: this.value });
      if (ok) {
        this.templates = [...this.templates, { pk, value: this.value }];
        this.value = '';
        this.$root.$emit('msg', 'ok', 'Шаблон добавлен', 2000);
      } else {
        this.$root.$emit('msg', 'error', 'Такой шаблон уже существует', 2000);
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async deleteTemplate(pk) {
      try {
        await this.$dialog.confirm('Подтвердите удаление шаблона');
      } catch (_) {
        return;
      }
      await this.$store.dispatch(actions.INC_LOADING);
      await this.$api('/input-templates/delete', { pk });
      this.templates = this.templates.filter(t => t.pk !== pk);
      this.$root.$emit('msg', 'ok', 'Шаблон удалён', 2000);
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    useTemplate(v) {
      // eslint-disable-next-line vue/no-mutating-props
      this.field.value = v;
      this.open = false;
      this.$root.$emit('msg', 'ok', 'Шаблон применён', 2000);
    },
    useTemplateAppend(v) {
      if (!v) {
        return;
      }
      let result = this.field.value.trim();
      let vToAppend: string = v;

      if (result.length > 0) {
        const li = result.length - 1;
        if (result[li] === '.') {
          vToAppend = vToAppend.charAt(0).toLocaleUpperCase() + vToAppend.slice(1);
        }

        vToAppend = ` ${vToAppend}`;
      }

      result += vToAppend;

      this.useTemplate(result);
    },
  },
};
</script>

<style scoped lang="scss">
textarea {
  resize: none;
}

.add-group {
  .form-control {
    width: calc(100% - 100px);
    flex: 0 calc(100% - 100px);
  }

  .input-group-btn {
    width: 100px;
    flex: 0 100px;
  }
}

.t-group {
  .form-control {
    width: calc(100% - 120px);
    flex: 0 calc(100% - 120px);
  }

  .input-group-btn {
    width: 40px;
    flex: 0 40px;
  }

  & + & {
    margin-top: 10px;
  }
}

.templates-list {
  margin-bottom: 20px;
}
</style>
