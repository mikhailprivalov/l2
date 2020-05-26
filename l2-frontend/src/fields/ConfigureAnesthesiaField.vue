<template>
    <div style="margin-top: 10px">
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
          <tr v-for="(val, index) in tb_data">
            <td class="first-column"><input class="no-outline" type="text" style="width:100%" v-model="val['title']" placeholder="Введите наименование"></td>
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
              <button class="btn btn-default btn-primary-nb" v-if="tb_data.length > 1" v-on:click="delete_row(index)"  v-tippy="{ placement : 'bottom'}" title="Удалить строку"> <i class="fa fa-times"/></button></td>
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
      data() {
        return {
          tb_data: [{"title": '', "type": '', "default": false}]
        }
      },
      methods: {
        add_new_row() {
          this.tb_data.push({"title": '', "type": '', "default": false});
          console.log(this.tb_data)
        },
        delete_row: function (index) {
          this.tb_data.splice(index, 1);
        }
      }
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
    border-bottom-style: groove;
    margin-left: 3px;
    margin-right: 3px;
    /*margin-top: 8px;*/
    width: 100%;
  }

  input:focus,
  input:active {
    border-bottom: 2px solid #56616c;
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
