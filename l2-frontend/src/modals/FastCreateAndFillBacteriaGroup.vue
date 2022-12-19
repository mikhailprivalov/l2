<template>
  <Modal
    ref="modal"
    show-footer="true"
    white-bg="true"
    min-width="40%"
    max-width="40%"
    width="100%"
    margin-left-right="auto"
    @close="hide_modal"
  >
    <span slot="header">Быстрое создание и заполнение: {{ typesObject }} – {{ typesGroups }}</span>
    <div
      slot="body"
      style="min-height: 200px"
      class="manage"
    >
      <div class="form-group">
        <label for="change-group-title">
          Название: {{ typesGroups }}
        </label>
        <input
          id="change-group-title"
          v-model.trim="title"
          class="form-control"
        >
      </div>

      <table class="table table-bordered table-condensed">
        <thead>
          <tr>
            <th>Название: {{ typesObject }}</th>
            <th>Код ФСЛИ</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="e in elements"
            :key="e.fsli"
          >
            <td class="cl-td">
              <input
                v-model="e.title"
                type="text"
                class="form-control"
              >
            </td>
            <td class="cl-td">
              <input
                v-model="e.fsli"
                type="text"
                class="form-control"
              >
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-4">
          <button
            type="button"
            class="btn btn-primary-nb btn-blue-nb"
            :disabled="!valid"
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
            Отмена
          </button>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script lang="ts">
import Modal from '@/ui-cards/Modal.vue';
import * as actions from '@/store/action-types';
import bacteriaPoint from '@/api/bacteria-point';

const getNewElement = () => ({
  title: '',
  fsli: '',
});

export default {
  name: 'FastCreateAndFillBacteriaGroup',
  components: { Modal },
  props: {
    typesObject: {
      type: String,
      required: true,
    },
    typesGroups: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      title: '',
      elements: [],
    };
  },
  computed: {
    valid() {
      return this.title.length > 0;
    },
  },
  mounted() {
    for (let i = 0; i < 14; i++) {
      this.elements.push(getNewElement());
    }
  },
  methods: {
    hide_modal() {
      this.$root.$emit('hide_fcafbg');
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
    },
    async save() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, message, obj } = await bacteriaPoint.packageGroupCreate(this, [
        'title', 'elements', 'typesObject',
      ]);
      if (ok) {
        this.$root.$emit('msg', 'ok', `Группа сохранена\n${this.title}`);
        this.$root.$emit('select2', obj);
        this.hide_modal();
      } else {
        this.$root.$emit('msg', 'error', `Ошибка\n${message}`);
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
};
</script>

<style scoped lang="scss">
  .manage {
    display: flex;
    align-items: stretch;
    flex-direction: column;
    flex-wrap: nowrap;
    align-content: stretch;

    & > div {
      align-self: stretch;
    }
  }

  p {
    display: flex;
    padding-top: 10px
  }

</style>
