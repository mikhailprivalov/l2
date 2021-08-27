<template>
  <div class="input-templates">
    <button class="btn btn-blue-nb2 btn-sm" @click="show">
      Шаблоны поля ввода
    </button>

    <MountingPortal mountTo="#portal-place-modal" name="InputTemplates" append>
      <transition name="fade">
        <Modal
          v-if="open"
          @close="open = false"
          show-footer="true"
          white-bg="true"
          max-width="710px"
          width="100%"
          marginLeftRight="auto"
        >
          <span slot="header">Ваши шалоны поля {{ `${group.title} ${field.title}`.trim() }}</span>
          <div slot="body" class="popup-body">
            <div class="preloader" v-if="loading"><i class="fa fa-spinner"></i> загрузка</div>
            <div v-else>
              <div class="templates-list">
                <div v-if="templates.length === 0" class="text-center">нет шаблонов для этого поля</div>
                <template v-else>
                  <div class="input-group input-group-flex t-group" v-for="t in templates" :key="t.pk">
                    <div class="input-group-btn">
                      <button class="btn btn-blue-nb2" @click="deleteTemplate(t.pk)" title="Удалить шаблон" v-tippy>
                        <i class="fas fa-times"></i>
                      </button>
                    </div>
                    <textarea
                      :rows="field.lines"
                      class="form-control"
                      v-if="field.lines > 1"
                      :value="t.value"
                      readonly
                    ></textarea>
                    <input class="form-control" v-else :value="t.value" readonly />
                    <div class="input-group-btn">
                      <button class="btn btn-blue-nb2" @click="useTemplate(t.value)" title="Применить шаблон" v-tippy>
                        <i class="fas fa-check"></i>
                      </button>
                    </div>
                  </div>
                </template>
              </div>
              <div class="input-group input-group-flex add-group">
                <textarea :rows="field.lines" class="form-control" v-if="field.lines > 1" v-model="value"></textarea>
                <input class="form-control" v-else v-model="value" />
                <div class="input-group-btn">
                  <button class="btn btn-blue-nb2" :disabled="value.trim().length === 0" @click="add">
                    Добавить
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-6">
                <button @click="open = false" class="btn btn-blue-nb" type="button">
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
  props: {
    field: Object,
    group: Object,
  },
  components: {
    Modal,
  },
  data() {
    return {
      loading: false,
      open: false,
      templates: [],
      value: '',
    };
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
      this.field.value = v;
      this.open = false;
      this.$root.$emit('msg', 'ok', 'Шаблон применён', 2000);
    },
  },
};
</script>

<style scoped lang="scss">
.input-templates {
  position: absolute;
  top: 100%;
  left: 5px;
  background: #fff;
  padding: 5px;
  border-radius: 0 0 5px 5px;
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.16), 0 3px 6px rgba(0, 0, 0, 0.23);
  display: none;
  z-index: 5;
}

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
    width: calc(100% - 80px);
    flex: 0 calc(100% - 80px);
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
