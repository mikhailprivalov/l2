<template>
  <div style="margin-top: 10px">
    <table class="table table-bordered">
      <colgroup>
        <col width='535'/>
        <col width='230'/>
        <col width='120'/>
      </colgroup>
      <thead>
      <tr>
        <th>Наименование</th>
        <th>Категория</th>
        <th>Показать по умолчанию</th>
        <th></th>
      </tr>
      </thead>
      <tbody>
      <tr class="tr-body" v-for="(val, index) in tb_data">
        <td><input class="no-outline" type="text" style="width:100%" v-model="val.title"
                                        placeholder="Введите наименование"></td>
        <td>
          <select v-model="val.type">
            <option disabled value="">Выберите один из вариантов</option>
            <option>Показатели человека</option>
            <option>Сильнодействующие</option>
            <option>Наркотические</option>
          </select>
        </td>
        <td align="center">
          <input type="checkbox" v-model="val.default">
        </td>
        <td>
          <button class="btn btn-default btn-primary-nb btn-delete" @click="delete_row(index)"
                  v-tippy="{ placement : 'bottom'}" title="Удалить строку">
          <i class="fa fa-minus"/>
          </button>
        </td>
      </tr>
      </tbody>
    </table>
    <button class="btn btn-blue-nb add-row" @click="add_new_row">
      Добавить
    </button>
  </div>
</template>

<script>
  export default {
    name: "ConfigureAnesthesiaField",
    props: {
      value: {
        required: false,
      },
      disabled: {
        required: false,
        default: false,
        type: Boolean,
      },
    },
    data() {
      return {
        tb_data: this.value || [{"header":'', "title": '', "type": '', "default": false}],
      }
    },
    methods: {
      add_new_row() {
        this.tb_data.push({"header":'', "title": '', "type": '', "default": false});
      },
       delete_row(index) {
        this.tb_data.splice(index, 1);
      },
      changeValue(newVal) {
        this.$emit('modified', newVal)
      }
    },
    watch: {
      tb_data: {
        handler() {
          this.changeValue(this.tb_data)
        },
        immediate: true,
      },
    },
    model: {
      event: `modified`
    },
  }
</script>

<style scoped lang="scss">

  .tr-body {
    height: 10px;
  }

  input {
    border: none;
    margin-left: 3px;
    margin-right: 3px;
    width: 100%;
  }

  .add-row {
    float: right;
  }

  .btn-delete {
    padding: 0;
  }

</style>
