<template>
  <div>
    <h4>Контролируемые параметры пациентов</h4>
    <div>
      <input
        v-model="search"
        class="form-control search"
        placeholder="Поиск исследования"
      >
    </div>
    <div class="card card1 card-no-hover">
      <div class="scroll">
        <table class="table">
          <colgroup>
            <col style="min-width: 200px">
            <col style="width: 200px">
            <col style="width: 108px">
            <col style="width: 100px">
            <col style="width: 40px">
            <col style="width: 39px">
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
              <th />
            </tr>
          </thead>
          <tr
            v-for="(param) in filteredParams"
            :key="param.id"
            class="border"
          >
            <td class="td-padding">
              <input
                v-model="param.title"
                class="form-control"
                style="border-bottom-right-radius: 0; border-top-right-radius: 0"
                type="text"
              >
            </td>
            <td class="td-padding">
              <input
                v-model="param.code"
                class="form-control"
                style="border-bottom-left-radius: 0; border-top-left-radius: 0"
                type="text"
              >
            </td>
            <td
              class="text-center td-padding"
            >
              <input
                v-model="param.all_patient_control"
                class="checkbox"
                type="checkbox"
              >
            </td>
            <td class="td-padding">
              <input
                v-model="param.order"
                class="form-control text-right"
                type="number"
              >
            </td>
            <td class="text-center ">
              <button
                v-tippy
                class="btn btn-blue-nb"
                title="Сохранить"
              >
                <i class="fa fa-save" />
              </button>
            </td>
            <td class="text-center">
              <button
                v-tippy
                class="btn btn-blue-nb"
                title="Удалить"
              >
                <i class="fa fa-times" />
              </button>
            </td>
          </tr>
        </table>
      </div>
    </div>
  </div>
</template>

<script>

export default {
  name: 'ConstructPatientControlParam',
  data() {
    return {
      data: '',
      search: '',
      paramsList: [],
    };
  },
  computed: {
    filteredParams() {
      return this.paramsList.filter(params => {
        const title = params.title.toLowerCase();
        const code = params.code.toLowerCase();
        const searchTerm = this.search.toLowerCase();

        return title.includes(searchTerm) || code.includes(searchTerm);
      });
    },
  },
  mounted() {
    this.getParamsList();
  },
  methods: {
    async getParamsList() {
      const params = await this.$api('/get-params-list');
      this.paramsList = params.data;
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
  min-height: 100px;
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}
.sticky {
  position: sticky;
  top: 0;
  background-color: white;
}
.border {
  border: 1px solid #ddd;
}
.checkbox {
  height: 20px;
  width: 100%;
}
.td-padding {
  padding: 3px 2px;
}
::v-deep .form-control {
  padding: 6px 9px;
  border-radius: 8px;
  background-color: transparent;
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
