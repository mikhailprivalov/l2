<template>
  <modal ref="modal" @close="hide_modal" show-footer="true" white-bg="true" max-width="50%" min-width="900px" width="50%"
         marginLeftRight="auto" margin-top="48px">
    <span slot="header">Выбрать диагноз</span>
    <div slot="body" style="min-height: 160px">
      <h6><strong>Поиск: </strong></h6>
      <div class="row" id="row-box">
        <div class="col-xs-3">
          <form>
            <div class="form-group">
              <label for="mkb10Code">Код МКБ10</label>
              <input type="text" class="form-control" id="mkb10Code" placeholder="Код МКБ-10">
            </div>
          </form>
        </div>
        <div class="col-xs-9" id="box-right">
          <form>
            <div class="form-group">
              <label for="mkb10Title">Название в МКБ10</label>
              <input type="text" class="form-control" id="mkb10Title" placeholder="Название МКБ-10">
            </div>
          </form>
        </div>
      </div>
      Y14.4 Отравление Cyamopsis tetragonoloba с неопределенными намерениями, на автомагистрали
    </div>

    <div slot="footer">
      <div class="row">
        <div class="col-xs-4">
          <button type="button" @click="updateDiagnosis" class="btn btn-primary-nb btn-blue-nb">
            Выбрать
          </button>
        </div>
        <div class="col-xs-4">
          <button type="button" @click="hide_modal" class="btn btn-primary-nb btn-blue-nb">
            Отмена
          </button>
        </div>
      </div>
    </div>
  </modal>
</template>

<script lang="ts">
import Modal from '../ui-cards/Modal.vue';
import * as actions from '../store/action-types';

export default {
  name: 'Mkb10Search',
  components: { Modal },
  props: {
    currentDiagnoses: {
      type: String,
      default: '',
    },
  },
  data() {
    return {
      mkb10Code: '',
      mkb10Title: '',
    };
  },
  mounted() {
    this.load_data();
  },
  methods: {
    hide_modal() {
      this.$root.$emit('hide_mkb_modal');
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
    },
    async load_data() {
      await this.$store.dispatch(actions.INC_LOADING);
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async updateDiagnosis() {
      await this.$store.dispatch(actions.INC_LOADING);
      const ok = true;
      if (ok) {
        this.$root.$emit('msg', 'ok', 'Cохранено');
        this.hide_modal();
      } else {
        this.$root.$emit('msg', 'error', 'Ошибка');
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
};
</script>

<style scoped lang="scss">
  .invalid {
    color: #d35400;
    cursor: pointer;
  }

  .isDisabled {
    cursor: not-allowed;
    opacity: 0.7;
    color: #d35400;
  }

  #row-box {
    display: flex;
  }

  #box-right {
    border-left: 1px solid silver;
  }
</style>
