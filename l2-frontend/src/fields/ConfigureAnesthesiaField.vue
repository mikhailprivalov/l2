<template>
  <div style="margin-top: 10px" v-model="tb_data" :readonly="disabled">
    <table class="table table-bordered">
      <thead>
      <tr>
        <th class="first-column">Наименование</th>
        <th class="second-column">Категория</th>
        <th class="third-column">Показать по умолчанию</th>
        <th></th>
      </tr>
      </thead>
      <tbody>
      <tr class="tr-body" v-for="(val, index) in tb_data">
        <td class="first-column"><input class="no-outline" type="text" style="width:100%" v-model="val['title']"
                                        placeholder="Введите наименование"></td>
        <td class="second-column">
          <select v-model="val['type']">
            <option disabled value="">Выберите один из вариантов</option>
            <option>Показатели человека</option>
            <option>Сильнодействующие</option>
            <option>Наркотические</option>
          </select>
        </td>
        <td class="third-column" align="center">
          <input type="checkbox" v-model="val['default']">
        </td>
        <td>
          <button class="btn btn-default btn-primary-nb" v-if="tb_data.length > 0" v-on:click="delete_row(index)"
                  v-tippy="{ placement : 'bottom'}" title="Удалить строку"><i class="fa fa-times"/></button>
        </td>
      </tr>
      </tbody>
    </table>
    <button class="btn btn-blue-nb" @click="add_new_row">
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
      delete_row: function (index) {
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

  td, th {
    padding-right: 4px;
    padding-left: 4px;
    padding-top: 1px;
    padding-bottom: 2px;
  }

  .first-column {
    width: 535px;
  }
  .tr-body{
    height: 10px;
  }

  .second-column {
    width: 230px;
  }

  .third-column {
    width: 120px;
  }

  input[type=text] {
    border-top-style: hidden;
    border-right-style: hidden;
    border-left-style: hidden;
    /*border-bottom-style: groove;*/
    border-bottom-style: hidden;
    margin-left: 3px;
    margin-right: 3px;
    /*margin-top: 8px;*/
    width: 100%;
  }

  input:focus,
  input:active {
    /*border-bottom: 2px solid #56616c;*/
    background-color: #66afe9;
  }

  .no-outline:focus {
    outline: none;
  }

  .btn {
    padding: 5px 4px;
    width: 100px;
    float: right;
  }

</style>
