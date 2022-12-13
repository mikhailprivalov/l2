<template>
  <div>
    <h4>Контролируемые параметры пациентов</h4>
    <div>
      <input
        v-model.trim="search"
        class="form-control search"
        placeholder="Поиск исследования"
      >
    </div>
    <div class="card card1 card-no-hover">
      <div class="scroll">
        <table class="table">
          <colgroup>
            <col style="min-width: 200px">
            <col width="100">
            <col width="100">
            <col width="100">
            <col width="93">
          </colgroup>
          <thead class="sticky">
            <tr>
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
              <th
                class="text-center"
              >
                <strong>Приоритет</strong>
              </th>
              <th />
            </tr>
          </thead>
          <tr
            v-if="filteredParams.length === 0"
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
            v-for="(param) in filteredParams"
            :key="param.pk"
          >
            <td class="border">
              <input
                v-model="param.title"
                class="form-control nba"
                type="text"
              >
            </td>
            <td class="border">
              <input
                v-model="param.code"
                class="form-control nba"
                type="text"
              >
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
              <input
                v-model="param.order"
                class="form-control text-right nba"
                type="number"
              >
            </td>
            <td class="border">
              <button
                v-tippy
                class="btn btn-blue-nb update-button nbr"
                title="Сохранить"
                @click="updateParam(param)"
              >
                <i class="fa fa-save" />
              </button>
            </td>
          </tr>
        </table>
      </div>
    </div>
    <h4>Добавить параметр</h4>
    <div>
      <table class="table">
        <colgroup>
          <col style="min-width: 200px">
          <col width="100">
          <col width="100">
          <col width="100">
          <col width="93">
        </colgroup>
        <tr>
          <td class="border">
            <input
              v-model="newParam.title"
              class="form-control nba"
              type="text"
            >
          </td>
          <td class="border">
            <input
              v-model="newParam.code"
              class="form-control nba"
              type="text"
            >
          </td>
          <td
            class="text-center border"
          >
            <input
              v-model="newParam.all_patient_control"
              class="checkbox"
              type="checkbox"
            >
          </td>
          <td class="border">
            <input
              v-model="newParam.order"
              class="form-control text-right nba"
              type="number"
            >
          </td>
          <td class="text-center border">
            <button
              v-tippy
              class="btn btn-blue-nb nbr"
              title="Добавить"
              @click="addParam"
            >
              Добавить
            </button>
          </td>
        </tr>
      </table>
    </div>
  </div>
</template>

<script>

import * as actions from '../store/action-types';

export default {
  name: 'ConstructPatientControlParam',
  data() {
    return {
      data: '',
      search: '',
      params: [],
      newParam: {
        title: '',
        code: '',
        all_patient_control: false,
        order: -1,
      },
    };
  },
  computed: {
    filteredParams() {
      return this.params.filter(params => {
        const title = params.title.toLowerCase();
        const code = params.code.toLowerCase();
        const searchTerm = this.search.toLowerCase();

        return title.includes(searchTerm) || code.includes(searchTerm);
      });
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
      if (this.params.find((param) => param.title === currentParam.title
        && param.id !== currentParam.id)) {
        this.$root.$emit('msg', 'error', 'Такое название уже есть');
      } else {
        await this.$store.dispatch(actions.INC_LOADING);
        const { ok, message } = await this.$api('update-param', currentParam);
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
      if (this.newParam.title && this.params.find((param) => param.title === this.newParam.title)) {
        this.$root.$emit('msg', 'error', 'Такое название уже есть');
      } else {
        await this.$store.dispatch(actions.INC_LOADING);
        const { ok, message } = await this.$api('add-param', this.newParam);
        await this.$store.dispatch(actions.DEC_LOADING);
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Сохранено');
          await this.getParams();
          this.newParam.title = '';
          this.newParam.code = '';
          this.newParam.all_patient_control = false;
          this.newParam.order = -1;
        } else {
          this.$root.$emit('msg', 'error', message);
        }
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
  min-height: 111.5px;
  max-height: calc(100vh - 350px);
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
.update-button {
  padding: 7px 39px;
}
.table > thead > tr > th {
  border-bottom: 0;
}
.search {
  border: 1px solid #ddd;
  border-radius: 5px;
  padding-left: 6px;
  background-color: white;
}
</style>
