<template>
  <div>
    <h4>Контролируемые параметры пациентов</h4>
    <div class="card card1 card-no-hover">
      <div class="scroll">
        <table class="table">
          <colgroup>
            <col width="85">
            <col>
            <col width="100">
            <col width="100">
            <col width="100">
          </colgroup>
          <thead class="sticky">
            <tr>
              <th />
              <th
                class="text-center"
              >
                <strong>Название</strong>
              </th>
              <th
                class="text-center"
              >
                <strong>Код</strong>
              </th>
              <th
                class="text-center"
              >
                <strong>Глобальный</strong>
              </th>
              <th />
            </tr>
          </thead>
          <tr
            v-if="params.length === 0"
            class="text-center"
          >
            <td
              colspan="5"
              class="border"
            >
              Нет данных
            </td>
          </tr>
          <tr
            v-for="(param) in params"
            :key="param.pk"
          >
            <td class="border">
              <div class="button">
                <button
                  class="btn last btn-blue-nb nbr"
                  :disabled="isFirstRow(param.order)"
                  @click="updateOrder(param, 'dec_order')"
                >
                  <i class="glyphicon glyphicon-arrow-up" />
                </button>
                <button
                  class="btn last btn-blue-nb nbr"
                  :disabled="isLastRow(param.order)"
                  @click="updateOrder(param, 'inc_order')"
                >
                  <i class="glyphicon glyphicon-arrow-down" />
                </button>
              </div>
            </td>
            <td class="border">
              <input
                v-model="param.title"
                class="form-control nba"
              >
            </td>
            <td class="border">
              <RegexFormatInput
                v-model="param.code"
                class="form-control nba"
                :rules="/[^0-9-.]/g"
              />
            </td>
            <td
              class="text-center border"
            >
              <input
                v-model="param.all_patient_control"
                class="checkbox"
                type="checkbox"
              >
            </td>
            <td class="border">
              <div class="button">
                <button
                  v-tippy
                  class="btn btn-blue-nb nbr"
                  title="Сохранить"
                  @click="updateParam(param)"
                >
                  <i class="fa fa-save" />
                </button>
              </div>
            </td>
          </tr>
        </table>
      </div>
    </div>
    <h4>Добавить параметр</h4>
    <div>
      <table class="table">
        <colgroup>
          <col>
          <col width="100">
          <col width="100">
          <col width="100">
        </colgroup>
        <tr>
          <td class="border">
            <input
              v-model="newParam.title"
              class="form-control nba"
              placeholder="Название"
            >
          </td>
          <td class="border">
            <RegexFormatInput
              v-model="newParam.code"
              class="form-control nba"
              placeholder="Код"
              :rules="/[^0-9-.]/g"
            />
          </td>
          <td
            class="text-center border"
          >
            <input
              v-model="newParam.allPatientControl"
              class="checkbox"
              type="checkbox"
            >
          </td>
          <td class="text-center border">
            <div class="button">
              <button
                v-tippy
                class="btn btn-blue-nb nbr"
                title="Добавить"
                @click="addParam"
              >
                Добавить
              </button>
            </div>
          </td>
        </tr>
      </table>
    </div>
  </div>
</template>

<script lang="ts">

import RegexFormatInput from '@/construct/RegexFormatInput.vue';

import * as actions from '../store/action-types';

export default {
  name: 'ConstructPatientControlParam',
  components: { RegexFormatInput },
  data() {
    return {
      params: [],
      newParam: {
        title: '',
        code: '',
        allPatientControl: false,
      },
    };
  },
  computed: {
    min_max_order() {
      let min = 0;
      let max = 0;
      for (const row of this.params) {
        min = Math.min(min, row.order);
        max = Math.max(max, row.order);
      }
      return { min, max };
    },
  },
  mounted() {
    this.getParams();
  },
  methods: {
    async getParams() {
      const params = await this.$api('/get-control-params');
      this.params = params.data;
    },
    async updateParam(currentParam) {
      if (!currentParam.title || !currentParam.code) {
        this.$root.$emit('msg', 'error', 'Ошибка заполнения');
      } else if (this.params.find((param) => currentParam.title === param.title && currentParam.id !== param.id)) {
        this.$root.$emit('msg', 'error', 'Такое название уже есть');
      } else if (this.params.find((param) => currentParam.code === param.code && currentParam.id !== param.id)) {
        this.$root.$emit('msg', 'error', 'Такой код уже есть');
      } else {
        await this.$store.dispatch(actions.INC_LOADING);
        const { ok, message } = await this.$api('update-control-param', currentParam);
        await this.$store.dispatch(actions.DEC_LOADING);
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Сохранено');
          await this.getParams();
        } else {
          this.$root.$emit('msg', 'error', message);
        }
      }
    },
    async addParam() {
      if (!this.newParam.title || !this.newParam.code) {
        this.$root.$emit('msg', 'error', 'Ошибка заполнения');
      } else if (this.params.find((param) => param.title === this.newParam.title)) {
        this.$root.$emit('msg', 'error', 'Такое название уже есть');
      } else if (this.params.find((param) => param.code === this.newParam.code)) {
        this.$root.$emit('msg', 'error', 'Такой код уже есть');
      } else {
        await this.$store.dispatch(actions.INC_LOADING);
        const { ok, message } = await this.$api('add-control-param', {
          title: this.newParam.title,
          code: this.newParam.code,
          allPatientControl: this.newParam.allPatientControl,
          maxOrder: this.min_max_order.max,
        });
        await this.$store.dispatch(actions.DEC_LOADING);
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Сохранено');
          await this.getParams();
          this.newParam.title = '';
          this.newParam.code = '';
          this.newParam.allPatientControl = false;
        } else {
          this.$root.$emit('msg', 'error', message);
        }
      }
    },
    isFirstRow(order) {
      return order === this.min_max_order.min;
    },
    isLastRow(order) {
      return order === this.min_max_order.max;
    },
    async updateOrder(param, action) {
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, message } = await this.$api('/update-order-param', {
        id: param.pk, order: param.order, action,
      });
      await this.$store.dispatch(actions.DEC_LOADING);
      if (ok) {
        this.$root.$emit('msg', 'ok', 'Порядок изменён');
        await this.getParams();
      } else {
        this.$root.$emit('msg', 'error', message);
      }
    },
  },
};
</script>

<style scoped>
::v-deep .card {
  margin: 1rem 0;
}
.table {
  margin-bottom: 0;
  table-layout: fixed;
}
.scroll {
  min-height: 111px;
  max-height: calc(100vh - 400px);
  overflow-y: auto;
}
.sticky {
  position: sticky;
  top: 0;
  z-index: 1;
  background-color: white;
}
.border {
  border: 1px solid #ddd;
}
.checkbox {
  height: 20px;
  width: 100%;
}
.table > thead > tr > th {
  border-bottom: 0;
}
.button {
  width: 100%;
  display: flex;
  flex-wrap: nowrap;
  flex-direction: row;
  justify-content: stretch;
}
  .btn {
    align-self: stretch;
    flex: 1;
    padding: 7px 0;
  }
</style>
