<template>
  <div class="main">
    <div class="box card-1 card-no-hover">
      <h5 class="text-center">
        Компании
      </h5>
      <input
        class="form-control"
        style="margin-bottom: 10px"
        placeholder="Фильтр по названию..."
      >
      <div class="scroll">
        <table class="table table-bordered">
          <colgroup>
            <col>
            <col width="40">
          </colgroup>
          <tr
            v-for="(company) in companyList.data"
            :key="company.id"
          >
            <td class="title">
              {{ company.title }}
            </td>
            <td>
              <button
                v-tippy
                title="Редактировать"
                class="btn last btn-blue-nb nbr"
              >
                <i class="fa fa-pencil" />
              </button>
            </td>
          </tr>
        </table>
      </div>
    </div>
    <div class="box card-1 card-no-hover">
      <h5 class="text-center">
        Создание/Редактирование
      </h5>
      <div>
        <label>Наименование организации</label>
        <input
          placeholder="Введите наименование организации"
          class="form-control"
        >
        <label>Сокращенное наименование</label>
        <input
          placeholder="Введите сокращенное наименование"
          class="form-control"
        >
        <label>Юридический адрес</label>
        <input
          placeholder="Введите адрес"
          class="form-control"
        >
        <label>Фактический адрес</label>
        <input
          placeholder="Введите адрес"
          class="form-control"
        >
        <label>ИНН</label>
        <input
          placeholder="Введите ИНН"
          class="form-control"
        >
        <label>ОГРН</label>
        <input
          placeholder="Введите ОГРН"
          class="form-control"
        >
        <label>КПП</label>
        <input
          placeholder="Введите КПП"
          class="form-control"
        >
        <label>БИК</label>
        <input
          placeholder="Введите БИК"
          class="form-control"
        >
        <label>Договор</label>
        <select
          style="margin-bottom: 10px"
          class="form-control"
        />
        <button
          v-tippy
          title="Сохранить"
          class="btn last btn-blue-nb nbr"
        >
          Сохранить
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
export default {
  name: 'ConstructCompany',
  data() {
    return {
      companyList: [],
      contractList: [],
    };
  },
  computed: {},
  mounted() {
    this.getCompanyList();
  },
  methods: {
    async getCompanyList() {
      this.companyList = await this.$api('/get-company-list');
    },
    async getContractList() {
      this.contractList = await this.$api('get-contract-list');
    }
  },
};
</script>

<style scoped>
.box {
  background-color: #FFF;
  margin: 10px 10px;
  flex-basis: 350px;
  flex-grow: 1;
  border-radius: 4px;
}

.main {
  display: flex;
  max-height: 80vh;
  flex-wrap: wrap;
}
.scroll {
  overflow-y: auto;
  max-height: 70%;
}
.title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-left: 12px;
}
.table {
  margin-bottom: 0;
  table-layout: fixed;
}
label {
  margin-left: 12px;
}
</style>
